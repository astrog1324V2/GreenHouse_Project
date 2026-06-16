import Foundation
import Observation
import Security

struct AppConfiguration {
    var baseURLString: String
    var readToken: String

    var isReady: Bool {
        normalizedBaseURL != nil && !readToken.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var normalizedBaseURL: URL? {
        guard var components = URLComponents(
            string: baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        ) else {
            return nil
        }
        if components.scheme == nil {
            components.scheme = "https"
        }
        guard let scheme = components.scheme?.lowercased(),
              ["http", "https"].contains(scheme),
              components.host != nil else {
            return nil
        }
        return components.url
    }
}

struct GreenhouseAPIClient {
    enum APIError: LocalizedError {
        case invalidURL
        case badStatus(Int)

        var errorDescription: String? {
            switch self {
            case .invalidURL:
                return "Enter a valid API URL."
            case .badStatus(let status):
                return "The server returned HTTP \(status)."
            }
        }
    }

    var session: URLSession = .shared

    func fetchLatest(baseURL: URL, token: String) async throws -> AppLatestResponse {
        let url = latestEndpoint(from: baseURL)
        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 15
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.badStatus(-1)
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            throw APIError.badStatus(httpResponse.statusCode)
        }
        return try JSONDecoder().decode(AppLatestResponse.self, from: data)
    }

    private func latestEndpoint(from baseURL: URL) -> URL {
        if baseURL.path.hasSuffix("/api/v1/app/latest") {
            return baseURL
        }
        return baseURL.appending(path: "api/v1/app/latest")
    }
}

struct DashboardCache {
    private let key = "greenhouse.latestPayload"
    var defaults: UserDefaults = .standard

    func load() -> AppLatestResponse? {
        guard let data = defaults.data(forKey: key) else {
            return nil
        }
        return try? JSONDecoder().decode(AppLatestResponse.self, from: data)
    }

    func save(_ payload: AppLatestResponse) {
        guard let data = try? JSONEncoder().encode(payload) else {
            return
        }
        defaults.set(data, forKey: key)
    }

    func clear() {
        defaults.removeObject(forKey: key)
    }
}

struct KeychainTokenStore {
    private let service = "com.nathansapps.greenhousemonitor"
    private let account = "greenhouse-read-token"

    func readToken() -> String? {
        var query = baseQuery()
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        return token
    }

    func saveToken(_ token: String) throws {
        let data = Data(token.utf8)
        var query = baseQuery()
        let update = [kSecValueData as String: data]
        let status = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        if status == errSecSuccess {
            return
        }
        if status == errSecItemNotFound {
            query[kSecValueData as String] = data
            let addStatus = SecItemAdd(query as CFDictionary, nil)
            guard addStatus == errSecSuccess else {
                throw KeychainError.unhandled(addStatus)
            }
            return
        }
        throw KeychainError.unhandled(status)
    }

    private func baseQuery() -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
    }

    enum KeychainError: LocalizedError {
        case unhandled(OSStatus)

        var errorDescription: String? {
            switch self {
            case .unhandled(let status):
                return "Keychain error \(status)."
            }
        }
    }
}

@MainActor
@Observable
final class DashboardStore {
    var configuration: AppConfiguration
    var payload: AppLatestResponse?
    var isLoading = false
    var errorMessage: String?

    private let baseURLKey = "greenhouse.apiBaseURL"
    private let apiClient: GreenhouseAPIClient
    private let cache: DashboardCache
    private let tokenStore: KeychainTokenStore

    init(
        apiClient: GreenhouseAPIClient = GreenhouseAPIClient(),
        cache: DashboardCache = DashboardCache(),
        tokenStore: KeychainTokenStore = KeychainTokenStore(),
        defaults: UserDefaults = .standard
    ) {
        self.apiClient = apiClient
        self.cache = cache
        self.tokenStore = tokenStore
        self.configuration = AppConfiguration(
            baseURLString: defaults.string(forKey: baseURLKey) ?? "",
            readToken: tokenStore.readToken() ?? ""
        )
    }

    var isConfigured: Bool {
        configuration.isReady
    }

    func loadCachedPayload() {
        if payload == nil {
            payload = cache.load()
        }
    }

    func saveConfiguration(baseURLString: String, readToken: String) {
        let cleanedURL = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        let cleanedToken = readToken.trimmingCharacters(in: .whitespacesAndNewlines)
        configuration = AppConfiguration(baseURLString: cleanedURL, readToken: cleanedToken)
        UserDefaults.standard.set(cleanedURL, forKey: baseURLKey)
        do {
            try tokenStore.saveToken(cleanedToken)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func refresh() async {
        guard let baseURL = configuration.normalizedBaseURL else {
            errorMessage = "Enter your Cloudflare API URL in settings."
            return
        }
        let token = configuration.readToken.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !token.isEmpty else {
            errorMessage = "Enter your app read token in settings."
            return
        }

        isLoading = true
        defer { isLoading = false }

        do {
            let latest = try await apiClient.fetchLatest(baseURL: baseURL, token: token)
            payload = latest
            cache.save(latest)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
