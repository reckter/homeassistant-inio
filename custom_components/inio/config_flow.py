"""UI setup: manual host entry, or auto-discovery via the lamp's DHCP hostname (inio_*)."""
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac

from .api import InioApi


class InioConfigFlow(ConfigFlow, domain="inio"):
    VERSION = 1

    def __init__(self):
        self._host = None

    async def _can_connect(self, host):
        try:
            await InioApi(async_get_clientsession(self.hass), host).mode()
            return True
        except Exception:  # noqa: BLE001 - any failure means "not a reachable inio"
            return False

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            self._async_abort_entries_match({CONF_HOST: host})
            if await self._can_connect(host):
                return self.async_create_entry(title=f"Inio ({host})", data={CONF_HOST: host})
            errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_HOST): str}), errors=errors
        )

    async def async_step_dhcp(self, discovery_info):
        await self.async_set_unique_id(format_mac(discovery_info.macaddress))
        # known lamp got a new IP: just update it
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        self._async_abort_entries_match({CONF_HOST: discovery_info.ip})
        if not await self._can_connect(discovery_info.ip):
            return self.async_abort(reason="cannot_connect")
        self._host = discovery_info.ip
        self.context["title_placeholders"] = {"name": discovery_info.hostname}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"Inio ({self._host})", data={CONF_HOST: self._host})
        self._set_confirm_only()
        return self.async_show_form(step_id="confirm", description_placeholders={"host": self._host})
