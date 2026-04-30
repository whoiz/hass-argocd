"""Config flow for ArgoCD integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_TOKEN, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import ArgoCDApiClient

_LOGGER = logging.getLogger(__package__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        vol.Optional(CONF_VERIFY_SSL, default=True): bool,
    }
)


class ArgoCDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ArgoCD."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate input
            url = user_input[CONF_URL]
            token = user_input[CONF_TOKEN]

            # Test connection
            api_client = ArgoCDApiClient(url, token)
            try:
                apps = await api_client.get_applications()
                if not apps:
                    errors["base"] = "no_applications"
            except Exception:
                errors["base"] = "cannot_connect"
            finally:
                await api_client.close()

            if not errors:
                return self.async_create_entry(
                    title=url,
                    data={
                        CONF_URL: url,
                        CONF_TOKEN: token,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )