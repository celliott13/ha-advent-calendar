import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def release_dates(monkeypatch):
    """Tests assert the real (December) dates, whatever TEST_MONTH is set to in the test build."""
    from custom_components.advent_calendar import const

    monkeypatch.setattr(const, "TEST_MONTH", None)
