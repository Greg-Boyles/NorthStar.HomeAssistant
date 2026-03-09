"""Diagnostics support for NorthStar Polestar integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_API_URL, DOMAIN

REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Redact sensitive fields from config
    config_data = dict(entry.data)
    config_data[CONF_EMAIL] = REDACTED
    config_data[CONF_PASSWORD] = REDACTED

    # Redact VINs in coordinator data (keep last 6 chars)
    redacted_data = {}
    if coordinator.data:
        for vin, car_data in coordinator.data.items():
            redacted_vin = f"***{vin[-6:]}" if len(vin) > 6 else REDACTED
            redacted_data[redacted_vin] = car_data

    return {
        "config": config_data,
        "options": dict(entry.options),
        "coordinator_data": redacted_data,
    }
