import XCTest
@testable import GreenhouseMonitor

final class GreenhouseMonitorTests: XCTestCase {
    func testDecodesCompactAppPayload() throws {
        let json = """
        {
          "generated_at_utc": "2026-06-16T21:30:00+00:00",
          "generated_at_local": "2026-06-16 17:30:00 EDT",
          "timezone": "America/Toronto",
          "device_id": "greenhouse",
          "current": {
            "temperature_c": 24.5,
            "humidity_pct": 66.1,
            "light_lux": 348.0,
            "measurement_at_utc": "2026-06-16T21:29:00+00:00",
            "measurement_at_local": "2026-06-16 17:29:00 EDT",
            "received_at_utc": "2026-06-16T21:29:04+00:00",
            "received_at_local": "2026-06-16 17:29:04 EDT",
            "age_seconds": 40,
            "is_stale": false
          },
          "temperature_snapshots": [
            {
              "label": "3 AM",
              "hour": 3,
              "target_local_time": "03:00",
              "window_minutes": 5,
              "reading": null
            }
          ]
        }
        """.data(using: .utf8)!

        let payload = try JSONDecoder().decode(AppLatestResponse.self, from: json)

        XCTAssertEqual(payload.deviceID, "greenhouse")
        XCTAssertEqual(payload.current?.temperatureC, 24.5)
        XCTAssertEqual(payload.temperatureSnapshots.first?.label, "3 AM")
        XCTAssertNil(payload.temperatureSnapshots.first?.reading)
    }

    func testReadingFormatting() {
        XCTAssertEqual(ReadingFormat.temperature(24.54), "24.5 C")
        XCTAssertEqual(ReadingFormat.temperature(nil), "-- C")
        XCTAssertEqual(ReadingFormat.percent(66.12), "66.1%")
        XCTAssertEqual(ReadingFormat.lux(348.2), "348 lux")
    }
}
