"""The ArgoCD integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import voluptuous as vol

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
    CONF_VERIFY_SSL,
    SERVICE_DELETE_POD,
    SERVICE_SYNC_APP,
)
from .api import ArgoCDApiClient

_LOGGER = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]


SERVICE_SYNC_APP_SCHEMA = vol.Schema(
    {
        vol.Required("application_name"): str,
    }
)

SERVICE_DELETE_POD_SCHEMA = vol.Schema(
    {
        vol.Required("application_name"): str,
        vol.Required("pod_name"): str,
        vol.Required("namespace"): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ArgoCD from a config entry."""

    url = entry.data[CONF_URL]
    token = entry.data[CONF_TOKEN]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL)

    api_client = await ArgoCDApiClient.create(url, token, verify_ssl)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            return await api_client.get_applications()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.data.setdefault(DOMAIN + "_api", {})[entry.entry_id] = api_client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.data.get(DOMAIN + "_services_registered"):
        hass.data[DOMAIN + "_services_registered"] = True

        async def handle_sync_app(call):
            app_name = call.data["application_name"]
            api_clients = hass.data.get(DOMAIN + "_api", {})
            if not api_clients:
                _LOGGER.error("No ArgoCD API client available")
                return
            client = next(iter(api_clients.values()))
            success = await client.sync_application(app_name)
            if success:
                _LOGGER.info("Synced application %s", app_name)
                for entry_id, coord in hass.data.get(DOMAIN, {}).items():
                    await coord.async_request_refresh()
            else:
                _LOGGER.error("Failed to sync application %s", app_name)

        async def handle_delete_pod(call):
            app_name = call.data["application_name"]
            pod_name = call.data["pod_name"]
            namespace = call.data["namespace"]

            api_clients = hass.data.get(DOMAIN + "_api", {})
            if not api_clients:
                _LOGGER.error("No ArgoCD API client available")
                return
            client = next(iter(api_clients.values()))

            success = await client.delete_resource(
                app_name, "Pod", pod_name, namespace, "v1"
            )
            if success:
                _LOGGER.info("Deleted pod %s/%s in app %s", namespace, pod_name, app_name)
            else:
                _LOGGER.error(
                    "Failed to delete pod %s/%s in app %s", namespace, pod_name, app_name
                )

        hass.services.async_register(
            DOMAIN, SERVICE_SYNC_APP, handle_sync_app, schema=SERVICE_SYNC_APP_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, SERVICE_DELETE_POD, handle_delete_pod, schema=SERVICE_DELETE_POD_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        api_client: ArgoCDApiClient = hass.data[DOMAIN + "_api"].pop(entry.entry_id)
        await api_client.close()

    return unload_ok