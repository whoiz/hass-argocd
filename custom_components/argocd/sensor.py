"""Sensor platform for ArgoCD integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_APPLICATION_NAME,
    ATTR_EXTERNAL_URLS,
    ATTR_HEALTH_STATUS,
    ATTR_LAST_SYNC,
    ATTR_REVISION,
    ATTR_SYNC_STATUS,
    DOMAIN,
    SENSOR_TYPES,
)
from .api import ArgoCDApiClient

_LOGGER = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ArgoCD sensor platform."""
    # We get the coordinator from hass.data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    if not coordinator.data:
        _LOGGER.debug("No applications yet, skipping sensor setup")
        async_add_entities(entities)
        return
    for app in coordinator.data:
        app_name = app.get("metadata", {}).get("name", "unknown")
        for sensor_type in SENSOR_TYPES:
            entities.append(
                ArgoCDApplicationSensor(
                    coordinator,
                    app_name,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class ArgoCDApplicationSensor(CoordinatorEntity, SensorEntity):
    """Representation of an ArgoCD Application sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        app_name: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._app_name = app_name
        self._sensor_type = sensor_type
        self._attr_name = f"{app_name} {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"{DOMAIN}_{app_name}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type].get("icon")

    @property
    def application_data(self) -> dict[str, Any] | None:
        """Return the application data for this sensor."""
        for app in self.coordinator.data:
            if app.get("metadata", {}).get("name") == self._app_name:
                return app
        return None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if not self.application_data:
            return None

        status = self.application_data.get("status", {})
        if self._sensor_type == "sync_status":
            return status.get("sync", {}).get("status", "Unknown")
        if self._sensor_type == "health_status":
            return status.get("health", {}).get("status", "Unknown")
        if self._sensor_type == "last_sync":
            sync_time = status.get("sync", {}).get("finishedAt")
            if sync_time:
                try:
                    return datetime.fromisoformat(sync_time.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None
        if self._sensor_type == "revision":
            return status.get("sync", {}).get("revision", "Unknown")
        if self._sensor_type == "external_urls":
            urls = status.get("summary", {}).get("externalURLs", [])
            return urls[0] if urls else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.application_data:
            return {}

        status = self.application_data.get("status", {})
        attrs = {
            ATTR_APPLICATION_NAME: self._app_name,
        }

        # Add common attributes
        if self._sensor_type in ["sync_status", "health_status"]:
            attrs[ATTR_SYNC_STATUS] = status.get("sync", {}).get("status")
            attrs[ATTR_HEALTH_STATUS] = status.get("health", {}).get("status")
            attrs[ATTR_REVISION] = status.get("sync", {}).get("revision")
            attrs[ATTR_LAST_SYNC] = status.get("sync", {}).get("finishedAt")

        if self._sensor_type == "external_urls":
            attrs[ATTR_EXTERNAL_URLS] = status.get("summary", {}).get("externalURLs", [])

        return attrs