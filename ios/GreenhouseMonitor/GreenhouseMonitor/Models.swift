import Foundation

struct AppLatestResponse: Codable, Equatable {
    let generatedAtUTC: String
    let generatedAtLocal: String?
    let timezone: String
    let deviceID: String
    let current: GreenhouseReading?
    let temperatureSnapshots: [TemperatureSnapshot]

    enum CodingKeys: String, CodingKey {
        case generatedAtUTC = "generated_at_utc"
        case generatedAtLocal = "generated_at_local"
        case timezone
        case deviceID = "device_id"
        case current
        case temperatureSnapshots = "temperature_snapshots"
    }
}

struct GreenhouseReading: Codable, Equatable {
    let temperatureC: Double?
    let humidityPct: Double?
    let lightLux: Double?
    let measurementAtUTC: String?
    let measurementAtLocal: String?
    let receivedAtUTC: String?
    let receivedAtLocal: String?
    let ageSeconds: Int?
    let isStale: Bool?

    enum CodingKeys: String, CodingKey {
        case temperatureC = "temperature_c"
        case humidityPct = "humidity_pct"
        case lightLux = "light_lux"
        case measurementAtUTC = "measurement_at_utc"
        case measurementAtLocal = "measurement_at_local"
        case receivedAtUTC = "received_at_utc"
        case receivedAtLocal = "received_at_local"
        case ageSeconds = "age_seconds"
        case isStale = "is_stale"
    }
}

struct TemperatureSnapshot: Codable, Equatable, Identifiable {
    let label: String
    let hour: Int
    let targetLocalTime: String
    let windowMinutes: Int
    let reading: GreenhouseReading?

    var id: String { label }

    enum CodingKeys: String, CodingKey {
        case label
        case hour
        case targetLocalTime = "target_local_time"
        case windowMinutes = "window_minutes"
        case reading
    }
}

extension AppLatestResponse {
    static let preview = AppLatestResponse(
        generatedAtUTC: "2026-06-16T21:30:00+00:00",
        generatedAtLocal: "2026-06-16 17:30:00 EDT",
        timezone: "America/Toronto",
        deviceID: "greenhouse",
        current: GreenhouseReading(
            temperatureC: 24.5,
            humidityPct: 66.1,
            lightLux: 348,
            measurementAtUTC: "2026-06-16T21:29:00+00:00",
            measurementAtLocal: "2026-06-16 17:29:00 EDT",
            receivedAtUTC: "2026-06-16T21:29:04+00:00",
            receivedAtLocal: "2026-06-16 17:29:04 EDT",
            ageSeconds: 40,
            isStale: false
        ),
        temperatureSnapshots: [
            TemperatureSnapshot(
                label: "3 AM",
                hour: 3,
                targetLocalTime: "03:00",
                windowMinutes: 5,
                reading: GreenhouseReading(
                    temperatureC: 18.7,
                    humidityPct: nil,
                    lightLux: nil,
                    measurementAtUTC: "2026-06-16T07:00:00+00:00",
                    measurementAtLocal: "2026-06-16 03:00:00 EDT",
                    receivedAtUTC: "2026-06-16T07:00:03+00:00",
                    receivedAtLocal: "2026-06-16 03:00:03 EDT",
                    ageSeconds: nil,
                    isStale: nil
                )
            ),
            TemperatureSnapshot(
                label: "3 PM",
                hour: 15,
                targetLocalTime: "15:00",
                windowMinutes: 5,
                reading: GreenhouseReading(
                    temperatureC: 31.2,
                    humidityPct: nil,
                    lightLux: nil,
                    measurementAtUTC: "2026-06-15T19:00:00+00:00",
                    measurementAtLocal: "2026-06-15 15:00:00 EDT",
                    receivedAtUTC: "2026-06-15T19:00:05+00:00",
                    receivedAtLocal: "2026-06-15 15:00:05 EDT",
                    ageSeconds: nil,
                    isStale: nil
                )
            ),
        ]
    )
}
