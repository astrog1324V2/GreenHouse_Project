# GreenhouseMonitor iOS App

Native iPhone/iPad client for the greenhouse API.

## Open in Xcode

Open:

```text
ios/GreenhouseMonitor/GreenhouseMonitor.xcodeproj
```

Select the `GreenhouseMonitor` scheme.

## First launch settings

Enter:

```text
API URL: https://greenhouse-api.nathansapps.ca
Read token: the GREENHOUSE_READ_TOKEN from the Windows PC .env file
```

The app stores the API URL in app storage and the read token in Keychain.

## Device install

In Xcode:

1. Select the `GreenhouseMonitor` target.
2. Open `Signing & Capabilities`.
3. Pick your Apple development team.
4. Connect or wirelessly pair the iPhone/iPad.
5. Choose that device in the run destination picker.
6. Press Run.

The bundle id is:

```text
com.nathansapps.greenhousemonitor
```

Change it in Xcode if your signing team requires a different unique id.

## Validation

From the repo root:

```zsh
xcodebuild -project ios/GreenhouseMonitor/GreenhouseMonitor.xcodeproj -scheme GreenhouseMonitor -destination 'generic/platform=iOS Simulator' build
xcodebuild -project ios/GreenhouseMonitor/GreenhouseMonitor.xcodeproj -scheme GreenhouseMonitor -destination 'platform=iOS Simulator,name=iPhone 17' test
```
