#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="$SCRIPT_DIR/GreenhouseMonitor/GreenhouseMonitor.xcodeproj"
SCHEME="GreenhouseMonitor"
SIM_NAME="Greenhouse iPhone 17"
DEVICE_TYPE="com.apple.CoreSimulator.SimDeviceType.iPhone-17"
RUNTIME="com.apple.CoreSimulator.SimRuntime.iOS-26-5"
BUNDLE_ID="com.nathansapps.greenhousemonitor"
DERIVED_DATA="/tmp/GreenhouseMonitorDerived"
APP_PATH="$DERIVED_DATA/Build/Products/Debug-iphonesimulator/GreenhouseMonitor.app"

sim_id="$(xcrun simctl list devices available | awk -v name="$SIM_NAME" '
  index($0, name " (") {
    match($0, /\(([0-9A-F-]+)\)/)
    print substr($0, RSTART + 1, RLENGTH - 2)
    exit
  }
')"

if [[ -z "$sim_id" ]]; then
  sim_id="$(xcrun simctl create "$SIM_NAME" "$DEVICE_TYPE" "$RUNTIME")"
fi

open -a Simulator
xcrun simctl boot "$sim_id" 2>/dev/null || true
xcrun simctl bootstatus "$sim_id" -b

xcodebuild \
  -project "$PROJECT_PATH" \
  -scheme "$SCHEME" \
  -destination "id=$sim_id" \
  -derivedDataPath "$DERIVED_DATA" \
  build

xcrun simctl terminate "$sim_id" "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl install "$sim_id" "$APP_PATH"
xcrun simctl launch "$sim_id" "$BUNDLE_ID"
