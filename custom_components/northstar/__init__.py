"""The NorthStar Polestar integration."""
from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import NorthStarApiClient
from .const import CONF_API_URL, DOMAIN
from .coordinator import NorthStarDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NorthStar Polestar from a config entry."""
    # Create aiohttp session
    session = aiohttp.ClientSession()

    # Create API client
    api = NorthStarApiClient(entry.data[CONF_API_URL], session)

    # Create coordinator
    coordinator = NorthStarDataUpdateCoordinator(hass, api, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and session
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    # Register devices
    device_registry = dr.async_get(hass)
    for vin, car_data in coordinator.data.items():
        car = car_data.get("car", {})
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, vin)},
            manufacturer="Polestar",
            model=car.get("modelName", "Unknown"),
            name=f"Polestar {car.get('modelName', 'Car')} ({vin[-6:]})",
            sw_version=car.get("softwareVersion"),
        )

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close session and remove data
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["session"].close()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
