import pytest
import os
import dotenv

import tests

dotenv.load_dotenv(verbose=True)

try:
    assert os.environ[tests.access_token_field]
except KeyError:
    raise KeyError(
        "You need to set the 'NATURE_ACCESS_TOKEN' environment variable for the tests"
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
