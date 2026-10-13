"""Run: python test_api.py [lamp-host] [--write]  (--write changes the lamp, then restores it)"""
import asyncio, sys
sys.path.insert(0, "custom_components/inio")
from api import InioApi, estimate

# real pwm readings (warm, cold) from the lamp for known settings
for (b, k), (w, c) in {(100, 2700): (99.59, 0), (100, 6500): (0, 99.55), (40, 4200): (24.08, 15.68),
                       (70, 5200): (23.82, 45.80), (8, 3300): (6.68, 1.20)}.items():
    got = estimate(w, c)
    assert got[0] == b and abs(got[1] - k) <= 20, ((b, k), got)
assert estimate(0, 0) == (0, 2700)
print("estimate ok")

if len(sys.argv) > 1:
    import aiohttp
    async def main():
        async with aiohttp.ClientSession() as s:
            api = InioApi(s, sys.argv[1])
            mode, color = await api.mode(), await api.read_color()
            print("mode", mode, "color", color)
            if "--write" not in sys.argv:
                return
            try:
                for target in ["OFF", "STATIC", "CONNECTED", "OFF", "CONNECTED", "STATIC", "CONNECTED", "OFF", "STATIC"]:
                    await api.set_mode(target)
                    await asyncio.sleep(1)
                    got = await api.mode()
                    print("set_mode", target, "->", got)
                    assert got == target, (target, got)
                for b, k in [(30, 3000), (80, 6000), (50, 4500)]:
                    await api.set_color(b, k)
                    got = await api.read_color()
                    print("set_color", (b, k), "-> estimated", got)
                    assert abs(got[0] - b) <= 5 and abs(got[1] - k) <= 30, ((b, k), got)
            finally:
                await api.set_mode("STATIC")
                await api.set_color(*color)
                await api.set_mode(mode)
                print("restored", await api.mode(), await api.read_color())
    asyncio.run(main())
