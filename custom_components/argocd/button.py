"""Button platform for ArgoCD integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .api import ArgoCDApiClient

_LOGGER = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ArgoCD button platform."""
    # We get the coordinator from hass.data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    api_client: ArgoCDApiClient = hass.data[DOMAIN + "_api"][config_entry.entry_id]

    entities = []
    for app in coordinator.data:
        app_name = app.get("metadata", {}).get("name", "unknown")
        entities.append(
            ArgoCDSyncButton(
                coordinator,
                app_name,
                api_client,
            )
        )

    async_add_entities(entities)


class ArgoCDSyncButton(ButtonEntity):
    """Representation of an ArgoCD Sync button."""

    def __init__(
        self,
        coordinator,
        app_name: str,
        api_client: ArgoCDApiClient,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._app_name = app_name
        self._api_client = api_client
        self._attr_name = f"{app_name} Sync"
        self._attr_unique_id = f"{DOMAIN}_{app_name}_sync"
        self._attr_icon = "mdi:arrows-clockwise"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Syncing application %s", self._app_name)
        success = await self._api_client.sync_application(self._app_name)
        if success:
            # Request a refresh of the coordinator to get the latest status
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to sync application %s", self._app_name)