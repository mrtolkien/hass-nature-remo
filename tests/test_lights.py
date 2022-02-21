import asyncio
import os
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import tests
from custom_components.nature_remo.api.nature_remo_api import NatureRemoAPI
from custom_components.nature_remo.light import NatureRemoLight


async def test_get_appliances(hass):
    # TODO Reuse result from API get appliances test
    api = NatureRemoAPI(
        os.environ[tests.access_token_field],
        async_get_clientsession(hass),
    )

    appliances = await api.get_appliances()

    lights = [
        NatureRemoLight(appliance, api, None)
        for appliance in appliances.values()
        if appliance["type"] == "LIGHT"
    ]

    # TODO Rely on mock data, this currently relies on the dev having a light...
    assert lights

    # Testing actual values
    if light_id := os.environ.get("NATURE_TEST_LIGHT_ID"):
        light = next(light for light in lights if light.unique_id == light_id)

        # Flickering the light
        await light.async_turn_off()
        await asyncio.sleep(1)
        await light.async_turn_on()
