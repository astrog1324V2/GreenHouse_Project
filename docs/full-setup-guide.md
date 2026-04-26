# Full Project Setup Guide

This is the top-level setup order for the greenhouse project with the always-on Windows PC as the main server.
Your home greenhouse and outdoor boards upload to this PC. The ESP32-C3 gift display units are standalone and only show readings on their OLED screens.

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
- gift display node: ESP32-C3 Super Mini + DHT22 + BH1750 + SH1106 OLED, no WiFi upload

Goal for this step:

- confirm all sensors power on
- confirm the greenhouse OLED turns on
- confirm both nodes can be powered reliably from USB

## Step 3: Prepare the always-on Windows PC

Set up the Windows PC that will host the dashboard, database, and API.

Read:

- [windows-server-setup.md](windows-server-setup.md)

Goal for this step:

- install Python and project dependencies
- confirm Docker Desktop is installed
- confirm the dashboard starts from Docker on the Windows PC
- confirm Docker Desktop is set to start with your Windows session

## Step 4: Start the Windows server in Docker

Run the server before touching the ESP32 configs.

Project commands:

```powershell
docker compose up -d --build
```

Then open:

```text
http://<your-windows-pc-ip>:8000/
```

Goal for this step:

- confirm the local server starts
- confirm the web UI loads
- confirm another device on the LAN can reach port `8000`

## Step 5: Configure the ESP32 firmware files

Fill in your WiFi and Windows server settings before uploading code to each ESP32.

Files to use:

- `esp32/boards/greenhouse/app_config.py`
- `esp32/boards/outdoor/app_config.py`
- `esp32/boards/esp32_c3_gift_display/app_config.py`
- `esp32/README.md`

What to change:

- `WIFI_SSID`
- `WIFI_PASSWORD`
- `SERVER_URL`
- `RUN_MODE`

Use:

- `RUN_MODE = "component_test"` for bench testing
- `RUN_MODE = "range_test"` for signal testing
- `RUN_MODE = "summer"` for normal 1-minute uploads
- `RUN_MODE = "display_only"` and `UPLOAD_ENABLED = False` for ESP32-C3 gift display units

For the Windows host:

- set `SERVER_URL = "http://<your-windows-pc-ip>:8000/api/v1/readings"`
- leave `TEMP_WINDOWS_SERVER_URL = None` unless you want a separate target only for `component_test`
- leave `UPLOAD_INTERVAL_SECONDS = 60`
- leave `MAX_PENDING_UPLOADS = 8` so the board can hold a short backlog if the PC is still booting after power returns

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
- both boards attempt WiFi and HTTP upload on their own
- gift display boards update the OLED without WiFi or HTTP upload

## Step 7: Test components against the Windows server

Put both boards in `component_test` mode first.

Test process:

- keep the Windows server running
- verify each sensor reports values before moving it to the final location
- confirm the greenhouse OLED updates while uploads are being posted
- fix wiring or sensor issues before doing WiFi range checks

Goal for this step:

- confirm each board can boot, read sensors, and post to the Windows server
- confirm the dashboard refreshes itself when readings arrive
- catch wiring or component failures before longer range testing

## Step 8: Run range tests before final installation

After the component checks pass, switch both boards to `range_test`.

Test process:

- keep the Windows server running
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

This keeps each node on the normal 60-second upload cadence.

Goal for this step:

- move from fast test uploads to the real summer schedule

## Step 10: Test power-loss recovery

Before final installation, simulate the failure mode you care about.

Test process:

1. shut down the Windows PC and remove power from the ESP32 supplies
2. restore power to the shared outlet
3. confirm the PC powers back on automatically from BIOS or UEFI settings
4. confirm Docker Desktop starts and the `greenhouse-server` container comes back automatically
5. confirm both ESP32 boards boot and resume posting without needing Thonny
6. confirm the dashboard repopulates once the PC finishes booting

Goal for this step:

- both nodes restart automatically after power loss
- the Windows server container comes back with your other Docker workloads
- any readings captured while the PC was still booting are flushed from the ESP32 backlog

## Step 11: Final assembly and deployment

After the firmware, server, WiFi, and recovery flow all work, move the hardware into the printed enclosures.

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

## Step 12: Normal operation checklist

During the season, your normal checks should be simple:

- open the Windows web UI to see the latest readings
- confirm both nodes are marked fresh
- confirm the `greenhouse-server` container is healthy after maintenance reboots
- confirm the PC still starts Docker Desktop correctly after maintenance reboots

## Recommended first-run order

If you want the shortest possible path, do it in this order:

1. read [enclosure-guide.md](enclosure-guide.md)
2. build both systems on breadboards
3. set up the Windows server with [windows-server-setup.md](windows-server-setup.md)
4. run the server on the Windows PC
5. configure and upload the ESP32 firmware
6. run `component_test`
7. run range tests
8. switch both nodes to `summer`
9. test a full power-loss recovery cycle
10. install everything into the printed enclosures
