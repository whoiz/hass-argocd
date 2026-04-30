"""The ArgoCD integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, CONF_TOKEN, CONF_URL, DOMAIN
from .api import ArgoCDApiClient

_LOGGER = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ArgoCD from a config entry."""

    url = entry.data[CONF_URL]
    token = entry.data[CONF_TOKEN]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 60)

    api_client = ArgoCDApiClient(url, token)

    async def async_update_data():
        """Fetch data from API endpoint. """
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

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        api_client: ArgoCDApiClient = hass.data[DOMAIN + "_api"].pop(entry.entry_id)
        await api_client.close()

    return unload_ok