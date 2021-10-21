from __future__ import annotations

from datetime import datetime, timedelta
import pytz

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import _LOGGER, DOMAIN

binary_sensor_class = {
    "mo": DEVICE_CLASS_MOTION,
}


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Sets up sensors found in the Nature Remo API"""
    if discovery_info is None:
        # TODO What even is that
        return

    _LOGGER.debug("Setting up Nature Remo sensors")

    devices_update_coordinator = hass.data[DOMAIN]["devices_update_coordinator"]

    async_add_entities(
        [
            NatureRemoBinarySensor(
                devices_update_coordinator,
                device,
                sensor_type,
            )
            for device in devices_update_coordinator.data.values()
            for sensor_type in device["newest_events"]
            if sensor_type in binary_sensor_class
        ]
    )


# TODO Common code with NatureRemoSensor
class NatureRemoBinarySensor(BinarySensorEntity, CoordinatorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: dict,
        sensor_type: str,
    ):
        # We don't need to have an API object in that one as the updating is fully done through the coordinator

        # Calling the CoordinatorEntity constructor which adds listeners and self.coordinator
        super().__init__(coordinator)

        # Concatenating the device name and sensor type
        self._name = f"{device['name']} - {binary_sensor_class[sensor_type]}"

        # device.id cannot unique id in itself as there are multiple sensors per device
        self._device_id = device["id"]

        self._sensor_type = sensor_type

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}-{self._sensor_type}"

    @property
    def device_class(self) -> str:
        return binary_sensor_class[self._sensor_type]

    @property
    def sensor_data(self):
        return self.coordinator.data[self._device_id]["newest_events"][
            self._sensor_type
        ]

    def latest_event_datetime(self) -> datetime:
        return datetime.fromisoformat(
            # Cutting the Z at the end and adding +00:00 as it's how python does it
            self.sensor_data["created_at"][:-1]
            + "+00:00"
        )

    @property
    def is_on(self):
        # Not entirely sure how this works, but currently it is *always* 1
        #   Adding some logging to make sure I'm not missing something
        if self.sensor_data["val"] != 1:
            _LOGGER.warning(
                f"Issue with Nature Remo Motion Sensor\n\t\t{self.sensor_data=}"
            )
            return None

        # From what I understand, we only know the last time motion was detected
        #   We return True if movement was detected in the last minute, False otherwise
        if datetime.now(pytz.UTC) - self.latest_event_datetime() < timedelta(
            seconds=60
        ):
            return True
        else:
            return False
