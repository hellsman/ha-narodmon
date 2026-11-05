"""Tests for Narodmon config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from custom_components.narodmon.const import (
    CONF_APIKEY,
    CONF_CENTER_HOME,
    CONF_SERVER,
    DOMAIN,
    SERVERS,
)


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def _bypass_setup_fixture() -> None:
    """Prevent setup."""
    with (
        patch(
            "custom_components.narodmon.async_setup",
            return_value=True,
        ),
        patch(
            "custom_components.narodmon.async_setup_entry",
            return_value=True,
        ),
    ):
        yield


async def test_user_step(hass: HomeAssistant) -> None:
    """Test the user step of the config flow."""
    result: FlowResult = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is None
    assert result["step_id"] == "user"


async def test_user_step_valid(hass: HomeAssistant) -> None:
    """Test the user step with valid credentials."""
    with patch(
        "custom_components.narodmon.config_flow.NarodmonApiClient.async_init",
        return_value=None,
    ):
        result: FlowResult = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_SERVER: "global",
                CONF_APIKEY: "testapikey",
                CONF_CENTER_HOME: True,
            },
        )
        assert result["type"] is None
        assert result["data"][CONF_SERVER] == "global"
        assert result["data"][CONF_APIKEY] == "testapikey"
        assert result["data"][CONF_CENTER_HOME] is True


async def test_user_step_invalid(hass: HomeAssistant) -> None:
    """Test the user step with invalid credentials."""
    with patch(
        "custom_components.narodmon.config_flow.NarodmonApiClient.async_init",
        side_effect=Exception("Invalid API key"),
    ):
        result: FlowResult = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_SERVER: "global",
                CONF_APIKEY: "invalidkey",
                CONF_CENTER_HOME: True,
            },
        )
        assert result["type"] is None
        assert result["errors"] == {"base": "auth"}


async def test_options_step(hass: HomeAssistant) -> None:
    """Test the options step of the config flow."""
    with (
        patch(
            "custom_components.narodmon.async_setup",
            return_value=True,
        ),
        patch(
            "custom_components.narodmon.async_setup_entry",
            return_value=True,
        ),
    ):
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=0,
            domain=DOMAIN,
            title="Narodmon Cloud Integration",
            data={
                CONF_SERVER: "global",
                CONF_APIKEY: "testapikey",
            },
            options={},
        )
        entry.add_to_hass(hass)

        assert hass.config_entries.async_get_entry(entry.entry_id) is not None

        result: FlowResult = await hass.config_entries.options.async_init(
            entry.entry_id
        )

        assert result["type"] is None
        assert result["step_id"] == "user"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "show_on_map": True,
                "scan_interval": cv.time_period_string_to_timedelta("00:03:00"),
                "search_area_radius": 10.0,
            },
        )

        assert result["type"] is None
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get(
                "show_on_map"
            )
            is True
        )
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get(
                "scan_interval"
            )
            == 180
        )
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get(
                "search_area_radius"
            )
            == 10.0
        )


async def test_options_step_manual_center(hass: HomeAssistant) -> None:
    """Test the options step with manual latitude/longitude."""
    with (
        patch(
            "custom_components.narodmon.async_setup",
            return_value=True,
        ),
        patch(
            "custom_components.narodmon.async_setup_entry",
            return_value=True,
        ),
    ):
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=0,
            domain=DOMAIN,
            title="Narodmon Cloud Integration",
            data={
                CONF_SERVER: "ru",
                CONF_APIKEY: "testapikey",
                CONF_CENTER_HOME: True,
            },
            options={
                "center_home": False,
                "latitude": 55.75,
                "longitude": 37.61,
                "scan_interval": 180,
                "search_area_radius": 5.0,
                "show_on_map": False,
            },
        )
        entry.add_to_hass(hass)

        result: FlowResult = await hass.config_entries.options.async_init(
            entry.entry_id
        )
        assert result["type"] is None
        assert result["step_id"] == "user"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "center_home": False,
                "show_on_map": True,
                "scan_interval": cv.time_period_string_to_timedelta("00:05:00"),
                "search_area_radius": 10.0,
            },
        )

        assert result["type"] is None
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get(
                "center_home"
            )
            is False
        )
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get("latitude")
            == 55.75
        )
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get("longitude")
            == 37.61
        )
        assert (
            hass.config_entries.async_get_entry(entry.entry_id).options.get(
                "scan_interval"
            )
            == 300
        )


def test_server_list() -> None:
    """Test the server list."""
    servers = {srv_id: srv["title"] for srv_id, srv in SERVERS.items()}
    assert len(servers) == 2
    assert "global" in servers
    assert "ru" in servers
    assert "Global (narodmon.com)" in servers.values()
    assert "RU (narodmon.ru)" in servers.values()
