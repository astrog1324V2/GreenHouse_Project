import SwiftUI

struct ContentView: View {
    @Bindable var store: DashboardStore
    @Environment(\.scenePhase) private var scenePhase
    @State private var isShowingSettings = false
    @State private var hasStarted = false

    var body: some View {
        NavigationStack {
            Group {
                if let payload = store.payload {
                    DashboardView(payload: payload, errorMessage: store.errorMessage)
                } else if store.isConfigured {
                    LoadingView(errorMessage: store.errorMessage)
                } else {
                    SetupPromptView {
                        isShowingSettings = true
                    }
                }
            }
            .navigationTitle("Greenhouse")
            .toolbar {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    Button {
                        Task { await store.refresh() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(store.isLoading || !store.isConfigured)
                    .accessibilityLabel("Refresh")

                    Button {
                        isShowingSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                    .accessibilityLabel("Settings")
                }
            }
        }
        .sheet(isPresented: $isShowingSettings) {
            SettingsView(store: store)
        }
        .task {
            guard !hasStarted else { return }
            hasStarted = true
            store.loadCachedPayload()
            if store.isConfigured {
                await store.refresh()
            }
        }
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active, hasStarted, store.isConfigured else {
                return
            }
            Task {
                store.loadCachedPayload()
                await store.refresh()
            }
        }
    }
}

struct DashboardView: View {
    let payload: AppLatestResponse
    let errorMessage: String?

    private let columns = [
        GridItem(.adaptive(minimum: 150), spacing: 12),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                statusHeader

                LazyVGrid(columns: columns, spacing: 12) {
                    MetricTile(
                        title: "Temperature",
                        value: ReadingFormat.temperature(payload.current?.temperatureC),
                        systemImage: "thermometer.medium",
                        tint: .green
                    )
                    MetricTile(
                        title: "Humidity",
                        value: ReadingFormat.percent(payload.current?.humidityPct),
                        systemImage: "humidity",
                        tint: .blue
                    )
                    MetricTile(
                        title: "Light",
                        value: ReadingFormat.lux(payload.current?.lightLux),
                        systemImage: "sun.max",
                        tint: .yellow
                    )
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text("3 AM and 3 PM")
                        .font(.headline)
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(payload.temperatureSnapshots) { snapshot in
                            SnapshotTile(snapshot: snapshot)
                        }
                    }
                }

                if let errorMessage {
                    Label(errorMessage, systemImage: "exclamationmark.triangle")
                        .font(.footnote)
                        .foregroundStyle(.orange)
                        .padding(.top, 4)
                }
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
    }

    private var statusHeader: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline) {
                Text(ReadingFormat.temperature(payload.current?.temperatureC))
                    .font(.system(size: 56, weight: .bold, design: .rounded))
                    .minimumScaleFactor(0.7)
                Spacer()
                StatusPill(isStale: payload.current?.isStale)
            }
            Text(payload.current?.measurementAtLocal ?? "No greenhouse reading yet")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.background, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct MetricTile: View {
    let title: String
    let value: String
    let systemImage: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: systemImage)
                .font(.title2)
                .foregroundStyle(tint)
                .frame(width: 32, height: 32, alignment: .leading)
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.weight(.semibold))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .padding(14)
        .frame(maxWidth: .infinity, minHeight: 132, alignment: .leading)
        .background(.background, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct SnapshotTile: View {
    let snapshot: TemperatureSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(snapshot.label)
                    .font(.headline)
                Spacer()
                Text(snapshot.targetLocalTime)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Text(ReadingFormat.temperature(snapshot.reading?.temperatureC))
                .font(.title2.weight(.semibold))
            Text(snapshot.reading?.measurementAtLocal ?? "No reading in window")
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(14)
        .frame(maxWidth: .infinity, minHeight: 132, alignment: .leading)
        .background(.background, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct StatusPill: View {
    let isStale: Bool?

    var body: some View {
        Label(title, systemImage: iconName)
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(tint.opacity(0.16), in: Capsule())
            .foregroundStyle(tint)
    }

    private var title: String {
        switch isStale {
        case false:
            return "Fresh"
        case true:
            return "Stale"
        case nil:
            return "Waiting"
        }
    }

    private var iconName: String {
        switch isStale {
        case false:
            return "checkmark.circle.fill"
        case true:
            return "clock.badge.exclamationmark"
        case nil:
            return "clock"
        }
    }

    private var tint: Color {
        switch isStale {
        case false:
            return .green
        case true:
            return .orange
        case nil:
            return .secondary
        }
    }
}

struct LoadingView: View {
    let errorMessage: String?

    var body: some View {
        VStack(spacing: 12) {
            ProgressView()
            if let errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .padding()
    }
}

struct SetupPromptView: View {
    let openSettings: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("API Setup Required", systemImage: "lock")
        } description: {
            Text("Enter the Cloudflare API URL and read token.")
        } actions: {
            Button("Open Settings", action: openSettings)
                .buttonStyle(.borderedProminent)
        }
    }
}

enum ReadingFormat {
    static func temperature(_ value: Double?) -> String {
        guard let value else { return "-- C" }
        return String(format: "%.1f C", value)
    }

    static func percent(_ value: Double?) -> String {
        guard let value else { return "--%" }
        return String(format: "%.1f%%", value)
    }

    static func lux(_ value: Double?) -> String {
        guard let value else { return "-- lux" }
        return String(format: "%.0f lux", value)
    }
}

#Preview {
    ContentView(store: {
        let store = DashboardStore()
        store.payload = .preview
        return store
    }())
}
