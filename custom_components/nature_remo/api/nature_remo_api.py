from typing import Dict
import aiohttp

from custom_components.nature_remo import _API_URL, _LOGGER


class NatureRemoAPI:
    """
    Nature Remo API client
    """

    def __init__(
        self,
        access_token: str,
        session: aiohttp.ClientSession,
    ):
        """
        Init API client
        """
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self._session = session

    async def get_appliances(self) -> Dict[str, dict]:
        """
        Gets the list of IR-controlled appliances accessible through Nature, as well as their state
        """
        _LOGGER.debug("Fetching appliances from the Nature Remo API.")

        appliances_query = self._session.get(
            f"{_API_URL}/appliances", headers=self.headers
        )
        appliances_response = await appliances_query

        return {x["id"]: x for x in await appliances_response.json()}

    async def get_devices(self) -> Dict[str, dict]:
        """
        Gets the list of Remo devices accessible through Nature, as well as their sensors state
        """
        _LOGGER.debug("Fetching devices from the Nature Remo API.")

        devices_query = self._session.get(f"{_API_URL}/devices", headers=self.headers)
        devices_response = await devices_query

        return {x["id"]: x for x in await devices_response.json()}

    async def post(
        self,
        path: str,
        data: dict,
    ) -> dict:
        """Emits a POST request to the API and returns it serialized."""
        _LOGGER.debug("Trying to request post:%s, data:%s", path, data)

        response = await self._session.post(
            f"{_API_URL}{path}", data=data, headers=self.headers
        )

        try:
            assert response.status == 200
        except AssertionError:
            raise aiohttp.ClientError(response)

        return await response.json()
