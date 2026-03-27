# GreenHouse Project

Local greenhouse monitoring stack for two ESP32 nodes:

- `greenhouse`: DHT22 + BH1750 + SH1106 OLED
- `outdoor`: DHT22 + BH1750
- `server`: Flask + SQLite backend that runs on Windows for testing and on a Raspberry Pi Zero 2 W for deployment
- `weekly archive`: CSV dump from the Raspberry Pi to a Windows SMB share

## Project layout

- `server/`: Python web app and database helpers
- `scripts/`: launch and maintenance scripts
- `deploy/systemd/`: Raspberry Pi service and timer units
- `esp32/`: MicroPython firmware and board config examples
- `docs/`: setup and enclosure guides
- `tests/`: server and archive tests

## Quick start on Windows

1. Create a virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Start the temporary test server with `python scripts/run_dev_server.py`.
4. Set `TEMP_WINDOWS_SERVER_URL = "http://<your-pc-ip>:8000/api/v1/readings"` in each ESP32 config and use `RUN_MODE = "component_test"` while bench-testing components.

## Raspberry Pi deployment

Read [docs/pi-setup.md](docs/pi-setup.md) for the full setup checklist and [docs/windows-share-setup.md](docs/windows-share-setup.md) for the weekly SMB archive target.

## Full project walkthrough

If you want the full project in order from hardware build to Pi deployment, read [docs/full-setup-guide.md](docs/full-setup-guide.md).

## Test suite

Run:

```powershell
python -m unittest discover -s tests -v
```
