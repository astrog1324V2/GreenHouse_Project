from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path

from server.app import create_app
from server.config import load_settings


class AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        base_path = Path(self.temp_dir.name)
        os.environ["GREENHOUSE_DB_PATH"] = str(base_path / "test.db")
        os.environ["GREENHOUSE_EXPORT_DIR"] = str(base_path / "exports")
        os.environ["GREENHOUSE_ARCHIVE_TEMP_DIR"] = str(base_path / "pending")
        os.environ["GREENHOUSE_ARCHIVE_SHARE_DIR"] = str(base_path / "share")
        os.environ["GREENHOUSE_TIMEZONE"] = "America/Toronto"
        self.app = create_app(load_settings())
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        for key in (
            "GREENHOUSE_DB_PATH",
            "GREENHOUSE_EXPORT_DIR",
            "GREENHOUSE_ARCHIVE_TEMP_DIR",
            "GREENHOUSE_ARCHIVE_SHARE_DIR",
            "GREENHOUSE_TIMEZONE",
        ):
            os.environ.pop(key, None)

    def test_post_reading_and_fetch_latest(self) -> None:
        payload = {
            "device_id": "greenhouse",
            "mode": "summer",
            "sequence": 10,
            "wifi_rssi_dbm": -62,
            "temperature_c": 24.5,
            "humidity_pct": 66.1,
            "light_lux": 348.0,
        }
        response = self.client.post("/api/v1/readings", json=payload)
        self.assertEqual(response.status_code, 201)

        latest_response = self.client.get("/api/v1/latest")
        self.assertEqual(latest_response.status_code, 200)
        latest = latest_response.get_json()
        self.assertIn("greenhouse", latest["devices"])
        self.assertEqual(latest["devices"]["greenhouse"]["sequence"], 10)

    def test_export_csv_contains_rows(self) -> None:
        for device_id in ("greenhouse", "outdoor"):
            self.client.post(
                "/api/v1/readings",
                json={
                    "device_id": device_id,
                    "mode": "summer",
                    "sequence": 1,
                    "wifi_rssi_dbm": -70,
                    "temperature_c": 20.0,
                    "humidity_pct": 50.0,
                    "light_lux": 120.0,
                },
            )

        response = self.client.get("/export.csv")
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(response.data.decode("utf-8").splitlines()))
        self.assertEqual(len(rows), 2)

    def test_index_page_renders(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Current conditions", response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
