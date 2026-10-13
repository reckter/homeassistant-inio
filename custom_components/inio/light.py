"""Inio lamp as a Home Assistant light. Effect 'Connected' = the lamp's circadian mode."""
from datetime import timedelta

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .api import InioApi

SCAN_INTERVAL = timedelta(seconds=30)
EFFECT_STATIC = "Static"
EFFECT_CONNECTED = "Connected"


async def async_setup_entry(hass, entry, async_add_entities):
    api = InioApi(async_get_clientsession(hass), entry.data[CONF_HOST])
    async_add_entities([InioLight(api, entry.entry_id)], True)


class InioLight(LightEntity):
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = [EFFECT_STATIC, EFFECT_CONNECTED]
    _attr_min_color_temp_kelvin = 2700
    _attr_max_color_temp_kelvin = 6500
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, api: InioApi, entry_id: str):
        self._api = api
        self._attr_unique_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={("inio", entry_id)}, name="Inio", manufacturer="Inio", model="Inio Light"
        )

    async def async_update(self):
        mode = await self._api.mode()
        self._attr_is_on = mode != "OFF"
        self._attr_effect = EFFECT_CONNECTED if mode == "CONNECTED" else EFFECT_STATIC
        if self._attr_is_on:
            brightness, kelvin = await self._api.read_color()
            self._attr_brightness = round(brightness * 255 / 100)
            self._attr_color_temp_kelvin = kelvin

    async def async_turn_on(self, **kwargs):
        wants_color = ATTR_BRIGHTNESS in kwargs or ATTR_COLOR_TEMP_KELVIN in kwargs
        if kwargs.get(ATTR_EFFECT) == EFFECT_CONNECTED and not wants_color:
            await self._api.set_mode("CONNECTED")
        elif wants_color or kwargs.get(ATTR_EFFECT) == EFFECT_STATIC:
            # changing color only works in static mode; start from what the lamp shows now
            await self._api.set_mode("STATIC")
            brightness, kelvin = await self._api.read_color()
            if ATTR_BRIGHTNESS in kwargs:
                brightness = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self._api.set_color(brightness, kwargs.get(ATTR_COLOR_TEMP_KELVIN, kelvin))
        elif not self.is_on:
            await self._api.set_mode("STATIC")

    async def async_turn_off(self, **kwargs):
        await self._api.set_mode("OFF")
