"""DataUpdateCoordinator for NorthStar Polestar integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import APIError, AuthenticationError, NorthStarApiClient, TimeoutError
from .const import CONF_API_URL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NorthStarDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NorthStar data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: NorthStarApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self.api = api
        self.config_entry = config_entry
        self._token: str | None = None

        update_interval = timedelta(
            seconds=config_entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Authenticate if we don't have a token
            if not self._token:
                self._token = await self._authenticate()

            # Get list of cars
            try:
                cars = await self.api.get_cars(self._token)
            except AuthenticationError:
                # Token expired, re-authenticate and retry
                _LOGGER.debug("Token expired, re-authenticating")
                self._token = await self._authenticate()
                cars = await self.api.get_cars(self._token)

            # Fetch detailed data for each car
            result = {}
            for car in cars:
                vin = car.get("vin")
                if not vin:
                    continue

                # Fetch all data in parallel
                car_data = {"car": car}

                tasks = {
                    "battery": self.api.get_battery(self._token, vin),
                    "trips": self.api.get_trips(self._token, vin),
                    "status": self.api.get_status(self._token, vin),
                    "charging_schedule": self.api.get_charging_schedule(self._token, vin),
                    "climate_schedule": self.api.get_climate_schedule(self._token, vin),
                }

                results = await asyncio.gather(*tasks.values(), return_exceptions=True)

                for key, result_value in zip(tasks.keys(), results):
                    if isinstance(result_value, Exception):
                        if isinstance(result_value, TimeoutError):
                            _LOGGER.warning(
                                "Timeout fetching %s for VIN %s (car may be asleep)", key, vin
                            )
                            car_data[key] = None
                        else:
                            _LOGGER.error(
                                "Error fetching %s for VIN %s: %s", key, vin, result_value
                            )
                            car_data[key] = None
                    else:
                        car_data[key] = result_value

                result[vin] = car_data

            return result

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _authenticate(self) -> str:
        """Authenticate and return access token."""
        email = self.config_entry.data[CONF_EMAIL]
        password = self.config_entry.data[CONF_PASSWORD]

        try:
            token = await self.api.authenticate(email, password)
            _LOGGER.debug("Successfully authenticated")
            return token
        except AuthenticationError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise ConfigEntryAuthFailed("Invalid credentials") from err
