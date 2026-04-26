# ESP32 MicroPython Firmware

This firmware supports the home networked boards and the standalone ESP32-C3 display units with the same shared code.

## Home ESP32 default wiring

- DHT22 data pin: `GPIO4`
- I2C SDA: `GPIO21`
- I2C SCL: `GPIO22`
- BH1750 I2C address: `0x23`
- SH1106 OLED I2C address: `0x3C`

The BH1750 and SH1106 share the same I2C bus on the greenhouse board.

## ESP32-C3 gift display wiring

- DHT22 data pin: `GPIO4`
- I2C SDA: `GPIO8`
- I2C SCL: `GPIO9`
- BH1750 I2C address: `0x23`
- SH1106 OLED I2C address: `0x3C`

The BH1750 and SH1106 share the same I2C bus. Power the modules from `3V3` and `GND`; do not use 5V pull-ups on signal lines. If using a bare DHT22, add a `4.7K` to `10K` pull-up resistor from data to `3V3`.

## File layout on the board

Copy these to the ESP32:

- `boot.py`
- `main.py`
- `app_config.py` for the target board
- every file from `lib/`

## Board configs

- `boards/greenhouse/app_config.py`
- `boards/outdoor/app_config.py`
- `boards/test_dht22/app_config.py`
- `boards/portable_demo/app_config.py`
- `boards/esp32_c3_gift_display/app_config.py`

Both example configs need your WiFi credentials and `SERVER_URL` filled in before upload.
For the normal deployment, point `SERVER_URL` at the always-on Windows PC and leave `TEMP_WINDOWS_SERVER_URL = None` unless you want a different target only for `component_test`.

`test_dht22` is the DHT22-only test board profile. It disables the BH1750 and OLED so you can run `range_test` with just the DHT22 connected.
`portable_demo` is the self-contained OLED demo profile. It reads sensors and updates the screen without WiFi or server uploads, which makes it suitable for a battery-bank-powered walkthrough.
`esp32_c3_gift_display` is the compact standalone profile for neighbor/family units. It reads the DHT22 and BH1750, updates the OLED, and does not use WiFi, HTTP, timestamps, queues, or the Windows server.

## Run modes

- `summer`: upload every 60 seconds to `SERVER_URL`
- `range_test`: upload every 10 seconds to `SERVER_URL`
- `component_test`: upload every 10 seconds to `TEMP_WINDOWS_SERVER_URL` when set, otherwise `SERVER_URL`
- `display_only`: refresh the OLED locally without WiFi or HTTP uploads

Switch modes by editing `RUN_MODE` in `app_config.py`.
For `component_test`, `TEMP_WINDOWS_SERVER_URL` is optional. If it is not set, the board uses `SERVER_URL`.
For a portable standalone build, use `UPLOAD_ENABLED = False` and `RUN_MODE = "display_only"`.
Set `OLED_SHOW_MODE = True` only on profiles where you want the mode name shown on the display.

## Power recovery behavior

- `boot.py` runs automatically at power-on.
- `main.py` restarts the board after unexpected failures.
- `MAX_PENDING_UPLOADS` controls how many unsent readings are kept in RAM while WiFi or the server is unavailable.

That means the boards will resume on their own after a power outage, and if the Windows PC takes longer to boot than the ESP32s, the nodes can hold a short backlog until uploads succeed again.
