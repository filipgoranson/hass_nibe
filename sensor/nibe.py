import logging
import asyncio

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.helpers.entity import (Entity, async_generate_entity_id)


DEPENDENCIES = ['nibe']
_LOGGER      = logging.getLogger(__name__)

CONF_SYSTEM    = 'system'
CONF_PARAMETER = 'parameter'

DATA_NIBE      = 'nibe'

PLATFORM_SCHEMA = vol.Schema({
        vol.Required(CONF_SYSTEM): cv.string,
        vol.Required(CONF_PARAMETER): cv.string,
    }, extra=vol.ALLOW_EXTRA)

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    sensors = None
    if (discovery_info):
        sensors = [ NibeSensor(hass, parameter['system_id'], parameter['parameter_id']) for parameter in discovery_info ]
    else:
        sensors = [ NibeSensor(hass, config.get(CONF_SYSTEM), config.get(CONF_PARAMETER)) ]

    async_add_devices(sensors, True)


class NibeSensor(Entity):
    def __init__(self, hass, system_id, parameter_id):
        """Initialize the Nibe sensor."""
        self._state        = None
        self._system_id    = system_id
        self._parameter_id = parameter_id
        self._name         = "{}_{}".format(system_id, parameter_id)
        self._unit         = None
        self._data         = None
        self._icon         = None
        self.entity_id     = async_generate_entity_id(
                                ENTITY_ID_FORMAT,
                                self._name,
                                hass=hass)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        return self._icon

    @property
    def should_poll(self):
        """No polling needed."""
        return True

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'designation'  : self._data['designation'],
            'parameter_id' : self._data['parameterId'],
            'display_value': self._data['displayValue'],
            'raw_value'    : self._data['rawValue'],
            'display_unit' : self._data['unit'],
        }

    @property
    def available(self):
        """Return True if entity is available."""
        if self._state == None:
            return False
        else:
            return True

    @asyncio.coroutine
    def async_update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        data = yield from self.hass.data[DATA_NIBE]['uplink'].get_parameter(self._system_id, self._parameter_id)
        print(data)
        if data:

            self._name  = data['title']

            scale = SCALE.get(data['unit'], SCALE_DEFAULT)
            self._icon  = scale['icon']
            self._unit  = scale['unit']
            if data['displayValue'] == '--':
                self._state = None
            elif scale['scale']:
                self._state = data['rawValue'] / scale['scale']
            else:
                self._state = data['displayValue']

            self._data = data

        else:
            self._state = None
