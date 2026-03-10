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

from .api import APIError, AuthenticationError, NorthStarApiClient, StreamNotActiveError, TimeoutError
from .const import (
    CONF_API_URL,
    CONF_ENABLE_STREAMING,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    STREAMING_UPDATE_INTERVAL,
)

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
        self._streaming_enabled = config_entry.options.get(
            CONF_ENABLE_STREAMING,
            config_entry.data.get(CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING),
        )
        self._streams_started: set[str] = set()

        # Use shorter interval when streaming is enabled (data is cached server-side)
        if self._streaming_enabled:
            update_interval = timedelta(seconds=STREAMING_UPDATE_INTERVAL)
        else:
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

            # Fetch detailed data for each car
            result = {}
            for car in cars:
                vin = car.get("vin")
                if not vin:
                    continue

                car_data = {"car": car}

                # If streaming enabled, start stream if not already started
                if self._streaming_enabled and vin not in self._streams_started:
                    try:
                        if self._refresh_token:
                            await self.api.start_stream(self._refresh_token, vin)
                            self._streams_started.add(vin)
                            _LOGGER.info("Started stream for VIN %s", vin)
                        else:
                            _LOGGER.warning(
                                "Cannot start stream for VIN %s - no refresh token", vin
                            )
                    except (APIError, TimeoutError) as err:
                        _LOGGER.error("Failed to start stream for VIN %s: %s", vin, err)

                try:
                    # If streaming enabled, try stream endpoint first
                    if self._streaming_enabled:
                        try:
                            snapshot = await self.api.get_stream_data(self._token, vin)
                            _LOGGER.debug("Got stream data for VIN %s", vin)
                        except StreamNotActiveError:
                            _LOGGER.warning(
                                "Stream not active for VIN %s, falling back to snapshot", vin
                            )
                            snapshot = await self.api.get_snapshot(self._token, vin)
                    else:
                        # Not streaming - use regular snapshot endpoint
                        snapshot = await self.api.get_snapshot(self._token, vin)

                    car_data["battery"] = snapshot.get("battery")
                    car_data["trips"] = snapshot.get("trips")
                    car_data["status"] = snapshot.get("status")
                    car_data["charging_schedule"] = snapshot.get("chargingSchedule")
                    car_data["climate_schedule"] = snapshot.get("climateSchedule")
                except TimeoutError:
                    _LOGGER.warning(
                        "Timeout fetching data for VIN %s (car may be asleep)", vin
                    )
                    car_data.update(
                        battery=None, trips=None, status=None,
                        charging_schedule=None, climate_schedule=None,
                    )
                except APIError as err:
                    _LOGGER.error(
                        "Error fetching data for VIN %s: %s", vin, err
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

    async def async_stop_streams(self) -> None:
        """Stop all active streams."""
        if not self._streaming_enabled or not self._streams_started:
            return

        _LOGGER.info("Stopping streams for %d VINs", len(self._streams_started))
        for vin in list(self._streams_started):
            try:
                if self._token:
                    await self.api.stop_stream(self._token, vin)
                    _LOGGER.info("Stopped stream for VIN %s", vin)
            except (APIError, TimeoutError) as err:
                _LOGGER.warning("Failed to stop stream for VIN %s: %s", vin, err)

        self._streams_started.clear()
