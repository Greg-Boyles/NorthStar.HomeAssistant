"""API client for NorthStar Polestar integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""


class APIError(Exception):
    """Exception raised for API errors."""


class TimeoutError(Exception):
    """Exception raised for timeout errors."""


class NorthStarApiClient:
    """Client for communicating with NorthStar API."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._base_url = base_url.rstrip("/")
        self._session = session

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate with NorthStar API and return token response."""
        url = f"{self._base_url}/api/auth/login"
        data = {"email": email, "password": password}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(url, json=data, ssl=False) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid credentials")
                    if response.status != 200:
                        text = await response.text()
                        raise APIError(f"Authentication failed: {response.status} - {text}")
                    
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise TimeoutError("Authentication request timed out") from err
        except aiohttp.ClientError as err:
            raise APIError(f"Connection error: {err}") from err

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token. Single HTTP call vs full OIDC login."""
        url = f"{self._base_url}/api/auth/refresh"
        data = {"refreshToken": refresh_token}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(url, json=data, ssl=False) as response:
                    if response.status == 401:
                        raise AuthenticationError("Refresh token expired or invalid")
                    if response.status != 200:
                        text = await response.text()
                        raise APIError(f"Token refresh failed: {response.status} - {text}")
                    
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise TimeoutError("Token refresh request timed out") from err
        except aiohttp.ClientError as err:
            raise APIError(f"Connection error: {err}") from err

    async def get_cars(self, token: str) -> list[dict[str, Any]]:
        """Get list of cars."""
        return await self._get(f"/api/cars", token)

    async def get_battery(self, token: str, vin: str) -> dict[str, Any]:
        """Get battery data for a car."""
        return await self._get(f"/api/cars/{vin}/battery", token)

    async def get_trips(self, token: str, vin: str) -> dict[str, Any]:
        """Get trip data for a car."""
        return await self._get(f"/api/cars/{vin}/trips", token)

    async def get_status(self, token: str, vin: str) -> dict[str, Any]:
        """Get comprehensive status for a car."""
        return await self._get(f"/api/cars/{vin}/status", token)

    async def get_charging_schedule(self, token: str, vin: str) -> dict[str, Any]:
        """Get charging schedule for a car."""
        return await self._get(f"/api/cars/{vin}/charging-schedule", token)

    async def get_climate_schedule(self, token: str, vin: str) -> dict[str, Any]:
        """Get climate schedule for a car."""
        return await self._get(f"/api/cars/{vin}/climate-schedule", token)

    async def get_snapshot(self, token: str, vin: str) -> dict[str, Any]:
        """Get unified vehicle snapshot (all data in one call)."""
        return await self._get(f"/api/cars/{vin}/snapshot", token)

    async def _get(self, path: str, token: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a GET request."""
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 401:
                        raise AuthenticationError("Token expired or invalid")
                    if response.status == 504:
                        raise TimeoutError(f"Request timed out: {path}")
                    if response.status != 200:
                        text = await response.text()
                        raise APIError(f"API request failed: {response.status} - {text}")
                    
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise TimeoutError(f"Request timed out: {path}") from err
        except aiohttp.ClientError as err:
            raise APIError(f"Connection error: {err}") from err
