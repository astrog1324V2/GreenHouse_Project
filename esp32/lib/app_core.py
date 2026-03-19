import time

try:
    import ntptime
except ImportError:
    ntptime = None

import app_config as config

from display_ui import StatusDisplay
from sensors import SensorSuite
from uploader import Uploader
from wifi_manager import WiFiManager


def _utc_timestamp():
    now = time.gmtime()
    return "%04d-%02d-%02dT%02d:%02d:%02d+00:00" % (
        now[0],
        now[1],
        now[2],
        now[3],
        now[4],
        now[5],
    )


def _interval_seconds():
    if config.RUN_MODE == "range_test":
        return config.RANGE_TEST_INTERVAL_SECONDS
    return config.UPLOAD_INTERVAL_SECONDS


def _sync_clock():
    if ntptime is None:
        return False
    try:
        ntptime.settime()
        return True
    except Exception:
        return False


def run_device():
    wifi = WiFiManager(
        config.WIFI_SSID,
        config.WIFI_PASSWORD,
        timeout_s=config.WIFI_TIMEOUT_SECONDS,
    )
    sensors = SensorSuite(config)
    uploader = Uploader(config.SERVER_URL, timeout_s=config.HTTP_TIMEOUT_SECONDS)
    display = StatusDisplay(sensors.i2c, config) if config.OLED_ENABLED else None

    interval_seconds = _interval_seconds()
    boot_ms = time.ticks_ms()
    sequence = 0
    last_latency_ms = None

    _sync_clock()
    if display:
        display.render({"temperature_c": None, "humidity_pct": None, "light_lux": None}, "BOOT")

    while True:
        cycle_started_ms = time.ticks_ms()
        wifi_ok = wifi.ensure_connected()
        readings = sensors.read_all()
        rssi = wifi.rssi()
        sent_at_utc = _utc_timestamp() if wifi_ok else None
        sequence += 1

        payload = {
            "device_id": config.DEVICE_ID,
            "mode": config.RUN_MODE,
            "sequence": sequence,
            "wifi_rssi_dbm": rssi if rssi is not None else -127,
            "temperature_c": readings["temperature_c"],
            "humidity_pct": readings["humidity_pct"],
            "light_lux": readings["light_lux"],
            "sent_at_utc": sent_at_utc,
            "latency_ms": last_latency_ms,
            "uptime_s": time.ticks_diff(time.ticks_ms(), boot_ms) // 1000,
        }

        footer = "WIFI DOWN"
        if wifi_ok:
            success, status_code, latency_ms, _response_text = uploader.send(payload)
            last_latency_ms = latency_ms
            if success:
                footer = "POST OK %dms" % latency_ms
            else:
                footer = "HTTP %d" % status_code
        else:
            footer = "WIFI DOWN"

        if readings["errors"]:
            footer = readings["errors"][0][:21]

        print(
            "mode=%s seq=%d wifi=%s temp=%s hum=%s light=%s status=%s"
            % (
                config.RUN_MODE,
                sequence,
                payload["wifi_rssi_dbm"],
                readings["temperature_c"],
                readings["humidity_pct"],
                readings["light_lux"],
                footer,
            )
        )

        if display:
            display.render(readings, footer)

        elapsed_ms = time.ticks_diff(time.ticks_ms(), cycle_started_ms)
        remaining_ms = max(0, interval_seconds * 1000 - elapsed_ms)
        while remaining_ms > 0:
            sleep_ms = 250 if remaining_ms > 250 else remaining_ms
            time.sleep_ms(sleep_ms)
            remaining_ms -= sleep_ms
