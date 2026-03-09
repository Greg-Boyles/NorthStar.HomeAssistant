"""Config flow for NorthStar Polestar integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import APIError, AuthenticationError, NorthStarApiClient, TimeoutError
from .const import (
    CONF_API_URL,
    DEFAULT_API_URL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class NorthStarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NorthStar Polestar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Test authentication
                async with aiohttp.ClientSession() as session:
                    api = NorthStarApiClient(user_input[CONF_API_URL], session)
                    await api.authenticate(
                        user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                    )

                # Set unique ID based on email to prevent duplicate entries
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Polestar ({user_input[CONF_EMAIL]})",
                    data=user_input,
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except TimeoutError:
                errors["base"] = "timeout"
            except APIError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NorthStarOptionsFlow:
        """Get the options flow for this handler."""
        return NorthStarOptionsFlow(config_entry)


class NorthStarOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for NorthStar Polestar."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "update_interval",
                        default=self.config_entry.options.get(
                            "update_interval", DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )
