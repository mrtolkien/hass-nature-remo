"""Support for Nature Remo AC."""
from homeassistant.core import callback
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from . import CONF_COOL_TEMP, CONF_HEAT_TEMP, DOMAIN, _LOGGER
from .common import NatureRemoBase

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE

MODE_HA_TO_REMO = {
    HVAC_MODE_AUTO: "auto",
    HVAC_MODE_FAN_ONLY: "blow",
    HVAC_MODE_COOL: "cool",
    HVAC_MODE_DRY: "dry",
    HVAC_MODE_HEAT: "warm",
    HVAC_MODE_OFF: "power-off",
}

MODE_REMO_TO_HA = {
    "auto": HVAC_MODE_AUTO,
    "blow": HVAC_MODE_FAN_ONLY,
    "cool": HVAC_MODE_COOL,
    "dry": HVAC_MODE_DRY,
    "warm": HVAC_MODE_HEAT,
    "power-off": HVAC_MODE_OFF,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo AC."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up climate platform.")

    devices_update_coordinator = hass.data[DOMAIN]["devices_update_coordinator"]
    appliances_update_coordinator = hass.data[DOMAIN]["appliances_update_coordinator"]

    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]

    async_add_entities(
        [
            NatureRemoAC(
                devices_update_coordinator,
                appliances_update_coordinator,
                api,
                appliance,
                config,
            )
            for appliance in appliances_update_coordinator.data.values()
            if appliance["type"] == "AC"
        ]
    )


class NatureRemoAC(NatureRemoBase, ClimateEntity):
    """Implementation of a Nature Remo E AC."""

    def __init__(
        self,
        devices_update_coordinator,
        appliances_update_coordinator,
        api,
        appliance,
        config,
    ):
        super().__init__(appliance)

        self.devices_update_coordinator = devices_update_coordinator
        self.appliances_update_coordinator = appliances_update_coordinator

        self.api = api

        self._default_temp = {
            HVAC_MODE_COOL: config[CONF_COOL_TEMP],
            HVAC_MODE_HEAT: config[CONF_HEAT_TEMP],
        }
        self._modes = appliance["aircon"]["range"]["modes"]
        self._hvac_mode = None
        self._current_temperature = None
        self._target_temperature = None
        self._remo_mode = None
        self._fan_mode = None
        self._swing_mode = None
        self._last_target_temperature = {v: None for v in MODE_REMO_TO_HA}
        self._update(appliance["settings"])

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        temp_range = self._current_mode_temp_range()
        if len(temp_range) == 0:
            return 0
        return min(temp_range)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        temp_range = self._current_mode_temp_range()
        if len(temp_range) == 0:
            return 0
        return max(temp_range)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        _LOGGER.debug("Current target temperature: %s", self._target_temperature)
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        temp_range = self._current_mode_temp_range()
        if len(temp_range) >= 2:
            # determine step from the gap of first and second temperature
            step = round(temp_range[1] - temp_range[0], 1)
            if step in [1.0, 0.5]:  # valid steps
                return step
        return 1

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        remo_modes = list(self._modes.keys())
        ha_modes = list(map(lambda mode: MODE_REMO_TO_HA[mode], remo_modes))
        ha_modes.append(HVAC_MODE_OFF)
        return ha_modes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._fan_mode

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._modes[self._remo_mode]["vol"]

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self._swing_mode

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return self._modes[self._remo_mode]["dir"]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return
        if target_temp.is_integer():
            # has to cast to whole number otherwise API will return an error
            target_temp = int(target_temp)
        _LOGGER.debug("Set temperature: %d", target_temp)
        await self._post({"temperature": f"{target_temp}"})

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("Set hvac mode: %s", hvac_mode)
        mode = MODE_HA_TO_REMO[hvac_mode]
        if mode == MODE_HA_TO_REMO[HVAC_MODE_OFF]:
            await self._post({"button": mode})
        else:
            data = {"operation_mode": mode}
            if self._last_target_temperature[mode]:
                data["temperature"] = self._last_target_temperature[mode]
            elif self._default_temp.get(hvac_mode):
                data["temperature"] = self._default_temp[hvac_mode]
            await self._post(data)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        _LOGGER.debug("Set fan mode: %s", fan_mode)
        await self._post({"air_volume": fan_mode})

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        _LOGGER.debug("Set swing mode: %s", swing_mode)
        await self._post({"air_direction": swing_mode})

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.appliances_update_coordinator.async_add_listener(self._update_callback)
        )
        self.async_on_remove(
            self.devices_update_coordinator.async_add_listener(self._update_callback)
        )

    async def async_update(self):
        """
        Updates the entity

        Only used by the generic entity update service
        """

        # TODO See if that is really needed here
        await self.appliances_update_coordinator.async_request_refresh()
        await self.devices_update_coordinator.async_request_refresh()

    def _update(self, ac_settings, device=None):
        # Holding this to determine the AC mode while it's turned-off
        self._remo_mode = ac_settings["mode"]

        try:
            self._target_temperature = float(ac_settings["temp"])
            self._last_target_temperature[self._remo_mode] = ac_settings["temp"]

        # TODO Understand the reason behind the except here and catch the right value
        except:
            self._target_temperature = None

        if ac_settings["button"] == MODE_HA_TO_REMO[HVAC_MODE_OFF]:
            self._hvac_mode = HVAC_MODE_OFF
        else:
            self._hvac_mode = MODE_REMO_TO_HA[self._remo_mode]

        self._fan_mode = ac_settings["vol"] or None
        self._swing_mode = ac_settings["dir"] or None

        if device is not None:
            self._current_temperature = float(device["newest_events"]["te"]["val"])

    @callback
    def _update_callback(self):

        # TODO I think that should be somewhere else, see _handle_coordinator_update in update_coordinator
        self._update(
            self.appliances_update_coordinator.data[self.unique_id]["settings"],
            self.devices_update_coordinator.data[self._device["id"]],
        )

        self.async_write_ha_state()

    async def _post(self, data):
        response = await self.api.post(
            f"/appliances/{self.unique_id}/aircon_settings",
            data,
        )
        self._update(response)
        self.async_write_ha_state()

    def _current_mode_temp_range(self):
        temp_range = self._modes[self._remo_mode]["temp"]
        return list(map(float, filter(None, temp_range)))
