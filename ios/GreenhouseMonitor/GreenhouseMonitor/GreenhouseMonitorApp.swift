import SwiftUI

@main
struct GreenhouseMonitorApp: App {
    @State private var store = DashboardStore()

    var body: some Scene {
        WindowGroup {
            ContentView(store: store)
        }
    }
}
