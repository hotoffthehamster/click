import pytest

from click_hotoffthehamster.testing import CliRunner


@pytest.fixture(scope="function")
def runner(request):
    return CliRunner()
