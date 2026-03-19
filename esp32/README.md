# ESP32 MicroPython Firmware

This firmware supports both boards with the same shared code.

## Default wiring

- DHT22 data pin: `GPIO4`
- I2C SDA: `GPIO21`
- I2C SCL: `GPIO22`
- BH1750 I2C address: `0x23`
- SH1106 OLED I2C address: `0x3C`

The BH1750 and SH1106 share the same I2C bus on the greenhouse board.

## File layout on the board

Copy these to the ESP32:

- `boot.py`
- `main.py`
- `app_config.py` for the target board
- every file from `lib/`

## Board configs

- `boards/greenhouse/app_config.py`
- `boards/outdoor/app_config.py`

Both example configs need your WiFi credentials and server URL filled in before upload.

## Run modes

- `summer`: upload every 60 seconds
- `range_test`: upload every 10 seconds

Switch modes by editing `RUN_MODE` in `app_config.py`.
