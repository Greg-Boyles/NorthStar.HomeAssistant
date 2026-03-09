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
        self._refresh_token: str | None = None

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
                await self._authenticate()

            # Get list of cars
            try:
                cars = await self.api.get_cars(self._token)
            except AuthenticationError:
                # Token expired — try refresh first, fall back to full login
                await self._refresh_or_authenticate()
                cars = await self.api.get_cars(self._token)

            # Fetch detailed data for each car via unified snapshot endpoint
            result = {}
            for car in cars:
                vin = car.get("vin")
                if not vin:
                    continue

                car_data = {"car": car}

                try:
                    snapshot = await self.api.get_snapshot(self._token, vin)
                    car_data["battery"] = snapshot.get("battery")
                    car_data["trips"] = snapshot.get("trips")
                    car_data["status"] = snapshot.get("status")
                    car_data["charging_schedule"] = snapshot.get("chargingSchedule")
                    car_data["climate_schedule"] = snapshot.get("climateSchedule")
                except TimeoutError:
                    _LOGGER.warning(
                        "Timeout fetching snapshot for VIN %s (car may be asleep)", vin
                    )
                    car_data.update(
                        battery=None, trips=None, status=None,
                        charging_schedule=None, climate_schedule=None,
                    )
                except APIError as err:
                    _LOGGER.error(
                        "Error fetching snapshot for VIN %s: %s", vin, err
                    )
                    car_data.update(
                        battery=None, trips=None, status=None,
                        charging_schedule=None, climate_schedule=None,
                    )

                result[vin] = car_data

            return result

        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _authenticate(self) -> None:
        """Full authentication with email/password."""
        email = self.config_entry.data[CONF_EMAIL]
        password = self.config_entry.data[CONF_PASSWORD]

        try:
            result = await self.api.authenticate(email, password)
            self._token = result["accessToken"]
            self._refresh_token = result.get("refreshToken")
            _LOGGER.debug("Successfully authenticated (refresh token %s)",
                          "received" if self._refresh_token else "not available")
        except AuthenticationError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise ConfigEntryAuthFailed("Invalid credentials") from err

    async def _refresh_or_authenticate(self) -> None:
        """Try refresh token first, fall back to full login."""
        if self._refresh_token:
            try:
                result = await self.api.refresh_token(self._refresh_token)
                self._token = result["accessToken"]
                self._refresh_token = result.get("refreshToken", self._refresh_token)
                _LOGGER.debug("Token refreshed successfully")
                return
            except (AuthenticationError, APIError) as err:
                _LOGGER.warning("Token refresh failed, falling back to full login: %s", err)

        await self._authenticate()
