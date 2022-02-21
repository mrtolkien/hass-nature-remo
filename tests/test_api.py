import os

from homeassistant.helpers.aiohttp_client import async_get_clientsession

import tests

from custom_components.nature_remo.api.nature_remo_api import NatureRemoAPI


async def test_get_appliances(hass):
    api = NatureRemoAPI(
        os.environ[tests.access_token_field],
        async_get_clientsession(hass),
    )

    devices = await api.get_devices()

    assert devices
