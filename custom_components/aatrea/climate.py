import requests
from typing import Any
import voluptuous as vol

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    UnitOfTemperature,
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST,"172.30.0.11"): cv.string,
        vol.Optional(CONF_NAME, default="Atrea"): cv.string,
        vol.Inclusive(CONF_USERNAME, "authentication"): cv.string,
        vol.Inclusive(CONF_PASSWORD, "authentication"): cv.string,
    }
)

SUPPORT_HVAC = [HVACMode.HEAT_COOL, HVACMode.OFF, HVACMode.FAN_ONLY]

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the oemthermostat platform."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    requests.get(f"http://{host}/api/ping")

    add_entities((ThermostatDevice(name, host, username, password),), True)

class ThermostatDevice(ClimateEntity):
    """Interface class for the oemthermostat module."""

    _attr_hvac_modes = SUPPORT_HVAC
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, name, host, username, password):
        """Initialize the device."""
        self._name = name
        self._host = host
        self._username = username
        self._password = password

        # set up internal state varS
        self._state = None
        self._temperature = None 
        self._setpoint = None
        self._mode = None
        self._inside_temperature = None
        self._outside_temperature = None
        self._exhaust_temperature = None
        self._fan_mode = None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        if self._mode == 2:
            return HVACMode.HEAT_COOL
        return HVACMode.HEAT_COOL

    @property
    def name(self):
        """Return the name of this Thermostat."""
        return self._name

    @property
    def hvac_action(self) -> HVACAction:
        """Return current hvac i.e. heat, cool, idle."""
        if not self._mode:
            return HVACAction.OFF
        if self._state:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._setpoint

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._fan_mode

    @property
    def fan_modes(self):
        return ["on_low", "on_high", "auto_low", "auto_high", "off"]

    @property
    def extra_state_attributes(self):
        attributes = {}
        attributes["inside_temperature"] = self._inside_temperature
        attributes["outside_temperature"] = self._outside_temperature
        attributes["exhaust_temperature"] = self._exhaust_temperature
        return attributes

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        pass

    def set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        pass

    def update(self) -> None:
        """Update local state."""
        #{
        #  "code": "OK",
        #  "error": null,
        #  "result": {
        #    "requests": {
        #      "fan_power_req": 45,
        #      "temp_request": 21.0,
        #      "work_regime": "VENTILATION"
        #    },
        #    "states": {
        #      "active": {}
        #    },
        #    "unit": {
        #      "fan_eta_factor": 45,
        #      "fan_sup_factor": 45,
        #      "mode_current": "NORMAL",
        #      "season_current": "HEATING",
        #      "temp_eha": 13.6,
        #      "temp_eta": 20.4,
        #      "temp_ida": 20.4,
        #      "temp_oda": 10.0,
        #      "temp_oda_mean": 9.875,
        #      "temp_sup": 19.3
        #    }
        #  }
        #}
        r = requests.get(f"http://{self._host}/api/ui_info")
        self._setpoint = r.json()['result']["requests"]["temp_request"]
        self._temperature = r.json()['result']["unit"]["temp_sup"]
        self._inside_temperature = r.json()['result']["unit"]["temp_ida"]
        self._outside_temperature = r.json()['result']["unit"]["temp_oda"]
        self._exhaust_temperature = r.json()['result']["unit"]["temp_eha"]
        self._fan_mode = r.json()['result']["requests"]["fan_power_req"]
