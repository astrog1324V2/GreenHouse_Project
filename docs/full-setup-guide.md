# Full Project Setup Guide

This is the top-level setup order for the whole greenhouse project.

Use this guide for the sequence. Use the other Markdown files for the detailed steps.

## Step 1: Build and plan the enclosures

Before you wire everything permanently, decide how both enclosures will be laid out.

Read:

- [enclosure-guide.md](enclosure-guide.md)

Goal for this step:

- decide the shape of the greenhouse enclosure
- decide the shape of the outdoor enclosure
- separate the sealed electronics bay from the vented sensor bay
- confirm where the OLED, DHT22, BH1750, USB cable, and mounting points will go

## Step 2: Bench-wire both ESP32 systems

Build both systems on breadboards first before moving anything into a printed enclosure.

Hardware plan:

- greenhouse node: ESP32 + DHT22 + BH1750 + SH1106 OLED
- outdoor node: ESP32 + DHT22 + BH1750

Goal for this step:

- confirm all sensors power on
- confirm the greenhouse OLED turns on
- confirm both nodes can be powered reliably from USB

## Step 3: Prepare the archive Windows PC

Set up the second Windows PC first, because the Raspberry Pi will eventually dump weekly CSV files there.

Read:

- [windows-share-setup.md](windows-share-setup.md)

Goal for this step:

- create the archive folder
- share it on the network
- confirm the Pi will later be able to write to it

## Step 4: Start the temporary test server on your main PC

Use the main Windows PC as the first server so you can test everything before touching the Pi.

Project commands:

```powershell
python -m pip install -r requirements.txt
python scripts/run_dev_server.py
```

Then open:

```text
http://<your-main-pc-ip>:8000/
```

Goal for this step:

- confirm the local server starts
- confirm the web UI loads
- keep this running while you test the ESP32 boards

## Step 5: Configure the ESP32 firmware files

Fill in your WiFi and server settings before uploading code to each ESP32.

Files to use:

- `esp32/boards/greenhouse/app_config.py`
- `esp32/boards/outdoor/app_config.py`
- `esp32/README.md`

What to change:

- `WIFI_SSID`
- `WIFI_PASSWORD`
- `SERVER_URL`
- `TEMP_WINDOWS_SERVER_URL`
- `RUN_MODE`

Use:

- `RUN_MODE = "component_test"` for temporary Windows server component testing
- `RUN_MODE = "range_test"` for signal testing
- `RUN_MODE = "summer"` for normal 1-minute uploads

For the temporary Windows test server, `TEMP_WINDOWS_SERVER_URL` should point to your main Windows PC.

## Step 6: Upload the MicroPython files to each ESP32

Using Thonny, copy the shared firmware files plus the correct board config to each device.

Files to copy:

- `esp32/boot.py`
- `esp32/main.py`
- all files in `esp32/lib/`
- one board-specific `app_config.py`

Goal for this step:

- both boards auto-start on power-up
- greenhouse board updates the OLED
- both boards attempt WiFi and HTTP upload

## Step 7: Test components on the temporary Windows server

Put both boards in `component_test` mode first.

Test process:

- keep the temporary Windows test server running
- verify each sensor reports values before moving it to the final location
- confirm the greenhouse OLED updates while uploads are being posted
- fix wiring or sensor issues before doing WiFi range checks

Goal for this step:

- confirm each board can boot, read sensors, and post to the temporary Windows server
- catch wiring or component failures before longer range testing

## Step 8: Run range tests before final installation

After the component checks pass, switch both boards to `range_test`.

Test process:

- keep the temporary Windows test server running
- place each node in its intended location
- let it run for at least 15 minutes
- watch the web UI and the Thonny serial output

Goal for this step:

- confirm reliable WiFi at the greenhouse location
- confirm reliable WiFi at the outdoor benchmark location
- decide whether router placement or an access point/extender is needed before final mounting

## Step 9: Switch both ESP32 boards to summer mode

Once range testing looks stable, change both board configs to:

```python
RUN_MODE = "summer"
```

This makes each node upload once per minute.

Goal for this step:

- move from fast test uploads to the real summer schedule

## Step 10: Set up the Raspberry Pi Zero 2 W

After the ESP32 boards work with the temporary Windows server, move the backend to the Pi.

Read:

- [pi-setup.md](pi-setup.md)

This includes:

- flashing Raspberry Pi OS Lite
- enabling SSH
- cloning the project
- creating the Python environment
- setting the `.env` file
- mounting the Windows SMB share
- enabling the `systemd` service and weekly timer

Goal for this step:

- the Pi hosts the web UI full-time
- the Pi stores the current week of data
- the Pi is ready to archive to the second Windows PC every week

## Step 11: Move the ESP32 server target from the main PC to the Pi

Once the Pi server is running correctly, update both ESP32 config files again.

Change:

- `SERVER_URL` from the main Windows PC IP
- to the Raspberry Pi IP or hostname

Then re-upload the updated `app_config.py` to each board.

Goal for this step:

- both ESP32 nodes now send to the Pi instead of the temporary PC server

## Step 12: Test the weekly archive flow

Before leaving the system unattended, manually test the archive process.

On the Pi:

```bash
python scripts/archive_weekly.py
```

Goal for this step:

- CSV appears on the second Windows PC
- Pi data is purged only after a successful copy
- the web UI starts repopulating as new readings arrive

## Step 13: Final assembly and deployment

After the firmware, server, WiFi, and archive flow all work, move the hardware into the printed enclosures.

Deployment order:

1. print and test-fit the enclosure parts
2. move the greenhouse node into its final enclosure
3. move the outdoor node into its final enclosure
4. mount both units in their final positions
5. power-cycle each one to confirm boot recovery

Goal for this step:

- both nodes restart automatically after power loss
- greenhouse OLED remains readable
- outdoor node stays shaded and ventilated

## Step 14: Normal operation checklist

During the season, your normal checks should be simple:

- open the Pi web UI to see the latest readings
- confirm both nodes are marked fresh
- occasionally confirm the weekly CSV files are appearing on the archive PC
- replace or dry silica packs in the sealed electronics compartments when needed

## Recommended first-run order

If you want the shortest possible path, do it in this order:

1. read [enclosure-guide.md](enclosure-guide.md)
2. build both systems on breadboards
3. set up the Windows archive share with [windows-share-setup.md](windows-share-setup.md)
4. run the temporary server on your main PC
5. configure and upload the ESP32 firmware
6. run `component_test`
7. run range tests
8. set up the Pi with [pi-setup.md](pi-setup.md)
9. point both ESP32 boards at the Pi
10. test the weekly archive
11. install everything into the printed enclosures
