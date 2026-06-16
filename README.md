# GreenHouse Project

Local greenhouse monitoring stack for ESP32 sensor nodes:

- `greenhouse`: DHT22 + BH1750 + SH1106 OLED
- `outdoor`: DHT22 + BH1750
- `esp32_c3_gift_display`: ESP32-C3 Super Mini + DHT22 + BH1750 + SH1106 OLED, display-only with no uploads
- `server`: Flask + SQLite backend hosted on an always-on Windows PC
- `ios/GreenhouseMonitor`: native iPhone/iPad app that reads the public API through Cloudflare Tunnel

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
3. Copy `.env.example` to `.env` and fill in the Cloudflare tunnel, app read, and ESP32 ingest tokens.
4. Set `SERVER_URL = "http://<your-pc-ip>:8000/api/v1/readings"` in each ESP32 config.
5. Set `SERVER_UPLOAD_TOKEN` in each uploading ESP32 config to match `GREENHOUSE_INGEST_TOKEN`.
6. Leave `TEMP_WINDOWS_SERVER_URL = None` unless `component_test` should post somewhere different.
7. Use the iPhone/iPad app with `https://<your-cloudflare-hostname>/api/v1/app/latest`.

The local dashboard still exists for troubleshooting, and each ESP32 keeps a short backlog in memory so it can flush readings once the Windows PC finishes booting after a power outage. The native app uses the compact `/api/v1/app/latest` endpoint instead of the web page.

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
