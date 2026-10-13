# homeassistant-inio

Home Assistant integration for [Inio](https://inio-light.com) lamps, ported from [homebridge-inio](https://github.com/reckter/homebridge-inio).

Exposes one light with brightness and color temperature (2700–6500 K). The effect `Connected` switches the lamp into its circadian ("connected") mode; changing brightness or temperature switches it back to static.

## Install

Copy `custom_components/inio` into your Home Assistant `config/custom_components/` folder and restart Home Assistant.

Lamps on the same network are discovered automatically (by their DHCP hostname `inio_*`) and show up under *Settings → Devices & services*. You can also add one by hand there: *Add integration → Inio*, then enter its IP address.

## Test

```sh
pip install aiohttp
python test_api.py 10.10.0.70   # read-only check against a lamp
```
