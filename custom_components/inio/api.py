"""Talks to the Inio lamp's local HTTP API. No Home Assistant imports, so it can be tested standalone."""
import asyncio

import aiohttp


def estimate(warm, cold):
    """The lamp only reports LED pwm duty. Total duty is the brightness and the cold share
    maps linearly onto 2700-6500 K (measured on hardware: within 20 K from 8% brightness up)."""
    total = warm + cold
    if not total:
        return 0, 2700
    return round(total), round((2700 + 3800 * cold / total) / 10) * 10


class InioApi:
    def __init__(self, session: aiohttp.ClientSession, host: str):
        self._session = session
        self._base = f"http://{host}"

    async def _req(self, method, path, **kw):
        async with self._session.request(
            method, self._base + path, timeout=aiohttp.ClientTimeout(total=10), **kw
        ) as r:
            r.raise_for_status()
            # lamp answers with JSON but not always with the right content type
            return await r.json(content_type=None) if method == "GET" else None

    async def mode(self) -> str:
        return (await self._req("GET", "/api/app/status"))["mode"]

    async def _press(self, button):
        await self._req("PUT", f"/api/interface/btn_short_{button}")

    async def set_mode(self, mode: str):
        """Modes cycle via the lamp's buttons: manual toggles OFF<->on, connect toggles CONNECTED<->STATIC."""
        current = await self.mode()
        if current == mode:
            return
        if mode == "OFF" or current == "OFF":
            await self._press("manual")
            current = "STATIC"  # verified on hardware: manual from OFF lands in STATIC
        if mode == "CONNECTED" or (mode == "STATIC" and current == "CONNECTED"):
            await self._press("connect")

    async def read_color(self):
        """(brightness 0-100, kelvin). The lamp fades, so poll pwm until it stops changing."""
        prev = await self._req("GET", "/api/app/pwm_duty_get")
        for _ in range(50):
            await asyncio.sleep(0.1)
            cur = await self._req("GET", "/api/app/pwm_duty_get")
            if cur == prev:
                break
            prev = cur
        return estimate(prev["warm"], prev["cold"])

    async def set_color(self, brightness: int, kelvin: int):
        kelvin = max(2700, min(6500, kelvin))
        await self._req(
            "POST", "/api/app/light_color", json={"brightness": brightness, "kelvin": kelvin}
        )
