"""Sensor platform for NorthStar Polestar integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
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
    """Set up NorthStar sensors."""
    coordinator: NorthStarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = []
    for vin in coordinator.data:
        # Battery sensors
        entities.extend([
            NorthStarBatteryLevelSensor(coordinator, vin),
            NorthStarRangeSensor(coordinator, vin),
            NorthStarChargingPowerSensor(coordinator, vin),
            NorthStarChargingCurrentSensor(coordinator, vin),
            NorthStarChargingVoltageSensor(coordinator, vin),
            NorthStarTimeToFullSensor(coordinator, vin),
        ])

        # Odometer and trip sensors
        entities.extend([
            NorthStarOdometerSensor(coordinator, vin),
            NorthStarTripAutoDistanceSensor(coordinator, vin),
            NorthStarTripManualDistanceSensor(coordinator, vin),
            NorthStarTripSinceChargeDistanceSensor(coordinator, vin),
            NorthStarAverageSpeedSensor(coordinator, vin),
            NorthStarAverageConsumptionSensor(coordinator, vin),
        ])

        # Climate sensors
        entities.extend([
            NorthStarInteriorTemperatureSensor(coordinator, vin),
            NorthStarClimateRuntimeLeftSensor(coordinator, vin),
        ])

        # Other sensors
        entities.append(NorthStarSoftwareVersionSensor(coordinator, vin))

    async_add_entities(entities)


class NorthStarSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for NorthStar sensors."""

    def __init__(
        self,
        coordinator: NorthStarDataUpdateCoordinator,
        vin: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
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


# Battery Sensors


class NorthStarBatteryLevelSensor(NorthStarSensorBase):
    """Battery level sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "battery_level")
        self._attr_name = "Battery Level"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("chargeLevelPercentage")
        return None


class NorthStarRangeSensor(NorthStarSensorBase):
    """Range sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "range")
        self._attr_name = "Range"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("estimatedRangeKm")
        return None


class NorthStarChargingPowerSensor(NorthStarSensorBase):
    """Charging power sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "charging_power")
        self._attr_name = "Charging Power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("chargingPowerWatts")
        return None


class NorthStarChargingCurrentSensor(NorthStarSensorBase):
    """Charging current sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "charging_current")
        self._attr_name = "Charging Current"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("chargingCurrentAmps")
        return None


class NorthStarChargingVoltageSensor(NorthStarSensorBase):
    """Charging voltage sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "charging_voltage")
        self._attr_name = "Charging Voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("chargingVoltageVolts")
        return None


class NorthStarTimeToFullSensor(NorthStarSensorBase):
    """Time to full charge sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "time_to_full")
        self._attr_name = "Time to Full"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self):
        """Return the state."""
        battery = self.coordinator.data[self._vin].get("battery")
        if battery:
            return battery.get("estimatedChargingTimeToFullMinutes")
        return None


# Odometer and Trip Sensors


class NorthStarOdometerSensor(NorthStarSensorBase):
    """Odometer sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "odometer")
        self._attr_name = "Odometer"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips:
            return trips.get("odometerKm")
        return None


class NorthStarTripAutoDistanceSensor(NorthStarSensorBase):
    """Trip Auto distance sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "trip_auto_distance")
        self._attr_name = "Trip Auto Distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips and trips.get("tripAuto"):
            return trips["tripAuto"].get("distanceKm")
        return None


class NorthStarTripManualDistanceSensor(NorthStarSensorBase):
    """Trip Manual distance sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "trip_manual_distance")
        self._attr_name = "Trip Manual Distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips and trips.get("tripManual"):
            return trips["tripManual"].get("distanceKm")
        return None


class NorthStarTripSinceChargeDistanceSensor(NorthStarSensorBase):
    """Trip Since Charge distance sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "trip_since_charge_distance")
        self._attr_name = "Trip Since Charge Distance"
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips and trips.get("tripSinceCharge"):
            return trips["tripSinceCharge"].get("distanceKm")
        return None


class NorthStarAverageSpeedSensor(NorthStarSensorBase):
    """Average speed sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "average_speed")
        self._attr_name = "Average Speed"
        self._attr_device_class = SensorDeviceClass.SPEED
        self._attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips and trips.get("tripAuto"):
            return trips["tripAuto"].get("averageSpeedKmh")
        return None


class NorthStarAverageConsumptionSensor(NorthStarSensorBase):
    """Average consumption sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "average_consumption")
        self._attr_name = "Average Consumption"
        self._attr_native_unit_of_measurement = "kWh/100km"

    @property
    def native_value(self):
        """Return the state."""
        trips = self.coordinator.data[self._vin].get("trips")
        if trips and trips.get("tripAuto"):
            return trips["tripAuto"].get("averageConsumptionKwhPer100Km")
        return None


# Climate Sensors


class NorthStarInteriorTemperatureSensor(NorthStarSensorBase):
    """Interior temperature sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "interior_temperature")
        self._attr_name = "Interior Temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("climate"):
            return status["climate"].get("currentTemperatureCelsius")
        return None


class NorthStarClimateRuntimeLeftSensor(NorthStarSensorBase):
    """Climate runtime left sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "climate_runtime_left")
        self._attr_name = "Climate Runtime Left"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self):
        """Return the state."""
        status = self.coordinator.data[self._vin].get("status")
        if status and status.get("climate"):
            return status["climate"].get("runtimeLeftMinutes")
        return None


# Other Sensors


class NorthStarSoftwareVersionSensor(NorthStarSensorBase):
    """Software version sensor."""

    def __init__(self, coordinator: NorthStarDataUpdateCoordinator, vin: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin, "software_version")
        self._attr_name = "Software Version"

    @property
    def native_value(self):
        """Return the state."""
        car = self.coordinator.data[self._vin].get("car")
        if car:
            return car.get("softwareVersion")
        return None
