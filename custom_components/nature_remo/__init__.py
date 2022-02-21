"""The Nature Remo integration."""
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.helpers import discovery, config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import CONF_ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)
DOMAIN = "nature_remo"

_API_URL = "https://api.nature.global/1/"

CONF_COOL_TEMP = "cool_temperature"
CONF_HEAT_TEMP = "heat_temperature"
DEFAULT_COOL_TEMP = 28
DEFAULT_HEAT_TEMP = 20

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Optional(CONF_COOL_TEMP, default=DEFAULT_COOL_TEMP): vol.Coerce(
                    int
                ),
                vol.Optional(CONF_HEAT_TEMP, default=DEFAULT_HEAT_TEMP): vol.Coerce(
                    int
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(
    hass,
    config,
):
    """Sets up the Nature Remo integration."""
    from custom_components.nature_remo.api.nature_remo_api import NatureRemoAPI

    _LOGGER.debug("Setting up Nature Remo integration.")

    # Creating integration-global objects
    api = NatureRemoAPI(
        config[DOMAIN][CONF_ACCESS_TOKEN],
        async_get_clientsession(hass, verify_ssl=False),
    )

    # This is an object that will periodically refresh its values, allowing us to read sensors and appliances states
    # TODO Contact devs: English API says 30 requests/minute, JP says 30/5 minutes
    #   It seems JP page is right, but it's way too low

    appliances_update_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Nature Remo Appliances Update",
        update_method=api.get_appliances,
        update_interval=timedelta(seconds=60),
    )

    devices_update_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Nature Remo Devices Update",
        update_method=api.get_devices,
        update_interval=timedelta(seconds=15),
    )

    await appliances_update_coordinator.async_config_entry_first_refresh()
    await devices_update_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = {
        "api": api,
        "devices_update_coordinator": devices_update_coordinator,
        "appliances_update_coordinator": appliances_update_coordinator,
        # TODO Check why we need to save config, it seems unnecessary to me and unsafe
        "config": config[DOMAIN],
    }

    # TODO I don't test this at the moment
    # await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)

    await discovery.async_load_platform(hass, "climate", DOMAIN, {}, config)
    await discovery.async_load_platform(hass, "light", DOMAIN, {}, config)

    return True
