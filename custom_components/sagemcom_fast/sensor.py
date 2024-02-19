"""Support for internet speed testing sensor."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeAssistantSagemcomFastData
from .const import DOMAIN
from .coordinator import SagemcomDataUpdateCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="download",
        translation_key="bytes_received",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="upload",
        translation_key="bytes_sent",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        suggested_display_precision=2,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors."""
    data: HomeAssistantSagemcomFastData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SagemcomSensorEntity(data.coordinator, description)
        for description in SENSOR_TYPES
    )


class SagemcomSensorEntity(
    CoordinatorEntity[SagemcomDataUpdateCoordinator], SensorEntity
):
    """Implementation of a sensor."""

    def __init__(
        self,
        coordinator: SagemcomDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = description.key
        self._state: StateType = None
        self._attrs: dict[str, Any] = {}
        self._last_refresh: int = 0
        self._last_state: int = 0

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, description.key)},
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType:
        """Return native value for entity."""

        if self.coordinator.stats:
            last_refresh = self._last_refresh
            last_state = self._last_state

            self._last_refresh = self.coordinator.stats["last_refresh"]
            self._last_state = int(
                self.coordinator.stats[self.entity_description.translation_key]
            )

            if last_refresh == 0:
                return None

            if (self._last_refresh - last_refresh) <= 0:
                return None

            total = (self._last_state - last_state) / (
                self._last_refresh - last_refresh
            )
            self._state = cast(StateType, total)

        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.stats:

            if self.entity_description.key == "download":
                self._attrs[
                    self.entity_description.translation_key
                ] = self.coordinator.stats[self.entity_description.translation_key]
            elif self.entity_description.key == "upload":
                self._attrs[
                    self.entity_description.translation_key
                ] = self.coordinator.stats[self.entity_description.translation_key]

        return self._attrs
