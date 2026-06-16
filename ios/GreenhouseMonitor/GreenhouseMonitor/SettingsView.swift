import SwiftUI

struct SettingsView: View {
    @Bindable var store: DashboardStore
    @Environment(\.dismiss) private var dismiss
    @State private var baseURLString: String
    @State private var readToken: String

    init(store: DashboardStore) {
        self.store = store
        _baseURLString = State(initialValue: store.configuration.baseURLString)
        _readToken = State(initialValue: store.configuration.readToken)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Connection") {
                    TextField("https://greenhouse-api.nathansapps.ca", text: $baseURLString)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)

                    SecureField("Read token", text: $readToken)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }

                if let errorMessage = store.errorMessage {
                    Section {
                        Label(errorMessage, systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.orange)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        store.saveConfiguration(baseURLString: baseURLString, readToken: readToken)
                        Task {
                            await store.refresh()
                        }
                        dismiss()
                    }
                }
            }
        }
    }
}
