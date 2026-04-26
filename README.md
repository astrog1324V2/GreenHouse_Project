# GreenHouse Project

Local greenhouse monitoring stack for ESP32 sensor nodes:

- `greenhouse`: DHT22 + BH1750 + SH1106 OLED
- `outdoor`: DHT22 + BH1750
- `esp32_c3_gift_display`: ESP32-C3 Super Mini + DHT22 + BH1750 + SH1106 OLED, display-only with no uploads
- `server`: Flask + SQLite backend hosted on an always-on Windows PC

## Project layout

- `server/`: Python web app and database helpers
- `scripts/`: launch and maintenance scripts
- `esp32/`: MicroPython firmware and board config examples
- `docs/`: setup and enclosure guides
- `tests/`: server and ESP32 tests
- `Dockerfile` + `docker-compose.yml`: Docker Desktop deployment for the Windows server

## Windows server quick start

1. Start Docker Desktop on the Windows PC.
2. Run `docker compose up -d --build`.
3. Set `SERVER_URL = "http://<your-pc-ip>:8000/api/v1/readings"` in each ESP32 config.
4. Leave `TEMP_WINDOWS_SERVER_URL = None` unless `component_test` should post somewhere different.
5. Open `http://<your-pc-ip>:8000/` to view the live dashboard.

The dashboard now updates itself as soon as new readings arrive, and each ESP32 keeps a short backlog in memory so it can flush readings once the Windows PC finishes booting after a power outage.

`SERVER_URL` is the normal destination. `TEMP_WINDOWS_SERVER_URL` is only an optional override used by `component_test` mode, and it now falls back to `SERVER_URL` automatically when left blank.

The `esp32_c3_gift_display` profile is for compact standalone units for neighbors or family. It uses the same sensor/display firmware, but `UPLOAD_ENABLED = False` and `RUN_MODE = "display_only"` so it never connects to WiFi or sends data anywhere.

## Docker startup and recovery

Read [docs/windows-server-setup.md](docs/windows-server-setup.md) for the Docker Desktop startup, recovery, and ESP32 URL setup.

## Full project walkthrough

If you want the full project in order from hardware build to Windows deployment, read [docs/full-setup-guide.md](docs/full-setup-guide.md).

## Test suite

Run:

```powershell
python -m unittest discover -s tests -v
```
