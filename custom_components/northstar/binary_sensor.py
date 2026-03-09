"""Binary sensor platform for NorthStar Polestar integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NorthStarDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NorthStar binary sensors."""
    coordinator: NorthStarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = []
    for vin in coordinator.data:
        # Charging
        entities.extend([
            NorthStarChargingSensor(coordinator, vin),
            NorthStarChargerConnectedSensor(coordinator, vin),
        ])

        # Doors
        entities.extend([
            NorthStarDoorSensor(coordinator, vin, "frontLeftDoor", "Front Left Door"),
            NorthStarDoorSensor(coordinator, vin, "frontRightDoor", "Front Right Door"),
            NorthStarDoorSensor(coordinator, vin, "rearLeftDoor", "Rear Left Door"),
            NorthStarDoorSensor(coordinator, vin, "rearRightDoor", "Rear Right Door"),
            NorthStarDoorSensor(coordinator, vin, "hood", "Hood"),
            NorthStarDoorSensor(coordinator, vin, "tailgate", "Tailgate"),
        ])

        # Locks
        entities.extend([
            NorthStarLockSensor(coordinator, vin, "centralLock", "Central Lock"),
            NorthStarLockSensor(coordinator, vin, "tailgateLock", "Tailgate Lock"),
        ])

        # Windows
        entities.extend([
            NorthStarWindowSensor(coordinator, vin, "frontLeftWindow", "Front Left Window"),
            NorthStarWindowSensor(coordinator, vin, "frontRightWindow", "Front Right Window"),
            NorthStarWindowSensor(coordinator, vin, "rearLeftWindow", "Rear Left Window"),
            NorthStarWindowSensor(coordinator, vin, "rearRightWindow", "Rear Right Window"),
            NorthStarWindowSensor(coordinator, vin, "sunroof", "Sunroof"),
        ])

        # Other
        entities.extend([
            NorthStarOnlineSensor(coordinator, vin),
            NorthStarClimateRunningSensor(coordinator, vin),
        ])

    async_add_entities(entities)


class NorthStarBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Base class for NorthStar binary sensors."""

    def __init__(
        self,
        coordinator: NorthStarDataUpdateCoordinator,
        vin: str,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._vin = vin
        self._attr_unique_id = f"{vin}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._vin in self.coordinator.data
        )


# Charging Sensors


class NorthStarChargingSensor(NorthStarBinarySensorBase):
    """Charging binary sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "charging")
        self._attr_name = "Charging"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def is_on(self) -> bool | None:
        """Return true if charging."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            status = battery.get("chargingStatus")
            return status is not None and status.upper() == "CHARGING"
        return None


class NorthStarChargerConnectedSensor(NorthStarBinarySensorBase):
    """Charger connected binary sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "charger_connected")
        self._attr_name = "Charger Connected"
        self._attr_device_class = BinarySensorDeviceClass.PLUG

    @property
    def is_on(self) -> bool | None:
        """Return true if charger is connected."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            status = battery.get("chargerConnectionStatus")
            return status is not None and status.upper() == "CONNECTED"
        return None


# Door Sensors


class NorthStarDoorSensor(NorthStarBinarySensorBase):
    """Door binary sensor."""

    def __init__(
        self,
        coordinator: NorthStarDataUpdateCoordinator,
        vin: str,
        key: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, key.lower())
        self._key = key
        self._attr_name = name
        self._attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def is_on(self) -> bool | None:
        """Return true if door is open."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("exterior"):
            value = status["exterior"].get(self._key)
            if value is not None:
                return value.upper() == "OPEN"
        return None


# Lock Sensors


class NorthStarLockSensor(NorthStarBinarySensorBase):
    """Lock binary sensor."""

    def __init__(
        self,
        coordinator: NorthStarDataUpdateCoordinator,
        vin: str,
        key: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, key.lower())
        self._key = key
        self._attr_name = name
        self._attr_device_class = BinarySensorDeviceClass.LOCK

    @property
    def is_on(self) -> bool | None:
        """Return true if unlocked (lock device_class: on=unlocked, off=locked)."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("exterior"):
            value = status["exterior"].get(self._key)
            if value is not None:
                return value.upper() == "UNLOCKED"
        return None


# Window Sensors


class NorthStarWindowSensor(NorthStarBinarySensorBase):
    """Window binary sensor."""

    def __init__(
        self,
        coordinator: NorthStarDataUpdateCoordinator,
        vin: str,
        key: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, key.lower())
        self._key = key
        self._attr_name = name
        self._attr_device_class = BinarySensorDeviceClass.WINDOW

    @property
    def is_on(self) -> bool | None:
        """Return true if window is open."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("exterior"):
            value = status["exterior"].get(self._key)
            if value is not None:
                return value.upper() == "OPEN"
        return None


# Other Sensors


class NorthStarOnlineSensor(NorthStarBinarySensorBase):
    """Online connectivity binary sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "online")
        self._attr_name = "Online"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        """Return true if car is online."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("availability"):
            value = status["availability"].get("status")
            return value is not None and value.upper() == "AVAILABLE"
        return None


class NorthStarClimateRunningSensor(NorthStarBinarySensorBase):
    """Climate running binary sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "climate_running")
        self._attr_name = "Climate Running"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool | None:
        """Return true if climate is running."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("climate"):
            value = status["climate"].get("runningStatus")
            return value is not None and value.upper() == "RUNNING"
        return None
