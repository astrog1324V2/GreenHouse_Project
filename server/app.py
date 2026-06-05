from __future__ import annotations

import json
import queue
import threading
from datetime import datetime, timezone
from io import BytesIO
from typing import Any
from zoneinfo import ZoneInfo

from flask import Flask, Response, jsonify, redirect, render_template, request, send_file, url_for

from .archive import run_weekly_archive
from .config import Settings, load_settings
from .db import (
    delete_device_data,
    fetch_device_statuses,
    fetch_latest_archive_run,
    fetch_reading_count,
    fetch_recent_history,
    fetch_temperature_readings,
    initialize_database,
    insert_reading,
    write_csv_export,
)


REQUIRED_FIELDS = {
    "device_id": str,
    "mode": str,
    "sequence": int,
    "wifi_rssi_dbm": int,
}
OPTIONAL_NUMERIC_FIELDS = {
    "temperature_c": float,
    "humidity_pct": float,
    "light_lux": float,
    "latency_ms": int,
    "uptime_s": int,
}
OPTIONAL_TEXT_FIELDS = {"sent_at_utc": str}
VALID_MODES = {"summer", "range_test", "component_test", "display_only"}
CLIENT_DEVICE_ID = "greenhouse"
CLIENT_TEMPERATURE_HOURS = (
    {"label": "3 PM", "hour": 15},
    {"label": "3 AM", "hour": 3},
)


class DashboardEventStream:
    def __init__(self) -> None:
        self._subscribers: set[queue.Queue[str]] = set()
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[str]:
        subscriber: queue.Queue[str] = queue.Queue(maxsize=8)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[str]) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, payload: dict[str, Any]) -> None:
        serialized = self._serialize(payload)
        with self._lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            if subscriber.full():
                try:
                    subscriber.get_nowait()
                except queue.Empty:
                    pass
            try:
                subscriber.put_nowait(serialized)
            except queue.Full:
                continue

    def stream(self, initial_payload: dict[str, Any]):
        subscriber = self.subscribe()
        initial_message = self._serialize(initial_payload)

        def generate():
            try:
                yield "retry: 5000\n"
                yield initial_message
                while True:
                    try:
                        yield subscriber.get(timeout=15)
                    except queue.Empty:
                        yield ": keepalive\n\n"
            finally:
                self.unsubscribe(subscriber)

        return generate()

    @staticmethod
    def _serialize(payload: dict[str, Any]) -> str:
        return "event: dashboard\ndata: %s\n\n" % json.dumps(payload, separators=(",", ":"))


def create_app(settings: Settings | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SETTINGS"] = settings or load_settings()
    dashboard_events = DashboardEventStream()

    current_settings: Settings = app.config["SETTINGS"]
    current_settings.ensure_directories()
    initialize_database(current_settings.db_path)

    @app.get("/health")
    def health() -> Response:
        return jsonify(
            {
                "status": "ok",
                "db_path": str(current_settings.db_path),
                "timestamp_utc": _utc_now_iso(),
            }
        )

    @app.get("/api/v1/latest")
    def latest() -> Response:
        return jsonify(_build_dashboard_payload(current_settings))

    @app.get("/api/v1/stream")
    def stream() -> Response:
        return Response(
            dashboard_events.stream(_build_dashboard_payload(current_settings)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/v1/readings")
    def readings() -> Response:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        try:
            cleaned_payload = _validate_payload(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        record = insert_reading(current_settings.db_path, cleaned_payload)
        dashboard_events.publish(_build_dashboard_payload(current_settings))
        return jsonify({"status": "ok", "reading": record}), 201

    @app.get("/export.csv")
    def export_csv() -> Response:
        temp_path = current_settings.export_dir / "export-current.csv"
        write_csv_export(current_settings.db_path, temp_path)
        buffer = BytesIO(temp_path.read_bytes())
        return send_file(
            buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name="greenhouse-export.csv",
        )

    @app.post("/admin/archive")
    def archive_now() -> Response:
        result = run_weekly_archive(current_settings)
        status_code = 200 if result.status == "success" else 500
        return jsonify(
            {
                "status": result.status,
                "row_count": result.row_count,
                "output_file": result.output_file,
                "message": result.message,
            }
        ), status_code

    @app.post("/admin/devices/<device_id>/delete")
    def delete_device(device_id: str) -> Response:
        if not delete_device_data(current_settings.db_path, device_id):
            return jsonify({"error": f"Unknown device: {device_id}"}), 404
        return redirect(url_for("dev"), code=303)

    @app.get("/")
    def index() -> str:
        dashboard = _build_client_payload(current_settings, CLIENT_DEVICE_ID)
        return render_template(
            "index.html",
            generated_at_local=dashboard["generated_at_local"],
            device_id=dashboard["device_id"],
            device=dashboard["device"],
            temperature_snapshots=dashboard["temperature_snapshots"],
        )

    @app.get("/dev")
    def dev() -> str:
        dashboard = _build_dashboard_payload(current_settings)
        return render_template(
            "dev.html",
            generated_at_local=dashboard["generated_at_local"],
            devices=dashboard["devices"],
            history=dashboard["history"],
            reading_count=dashboard["reading_count"],
            latest_archive=dashboard["latest_archive"],
        )

    return app


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}

    for field_name, field_type in REQUIRED_FIELDS.items():
        if field_name not in payload:
            raise ValueError(f"Missing required field: {field_name}")
        cleaned[field_name] = _coerce_value(field_name, payload[field_name], field_type)

    if not cleaned["device_id"].strip():
        raise ValueError("device_id cannot be empty.")
    cleaned["device_id"] = cleaned["device_id"].strip()

    if cleaned["mode"] not in VALID_MODES:
        raise ValueError(
            "mode must be 'summer', 'range_test', 'component_test', or 'display_only'."
        )

    for field_name, field_type in OPTIONAL_NUMERIC_FIELDS.items():
        value = payload.get(field_name)
        cleaned[field_name] = (
            None if value is None else _coerce_value(field_name, value, field_type)
        )

    for field_name, field_type in OPTIONAL_TEXT_FIELDS.items():
        value = payload.get(field_name)
        cleaned[field_name] = (
            None if value is None else _coerce_value(field_name, value, field_type)
        )

    return cleaned


def _coerce_value(field_name: str, value: Any, field_type: type) -> Any:
    if field_type is str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")
        return value

    if field_type is int:
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be an integer.")
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be an integer.") from exc

    if field_type is float:
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be numeric.")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric.") from exc

    raise ValueError(f"Unsupported field type for {field_name}.")


def _build_status_payload(settings: Settings) -> dict[str, dict[str, Any]]:
    rows = fetch_device_statuses(settings.db_path)
    devices: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = dict(row)
        received_at_utc = item["received_at_utc"]
        age_seconds = _age_seconds(received_at_utc)
        item["received_at_local"] = _format_local(received_at_utc, settings.timezone)
        item["sent_at_local"] = (
            _format_local(item["sent_at_utc"], settings.timezone) if item["sent_at_utc"] else None
        )
        item["age_seconds"] = age_seconds
        item["is_stale"] = age_seconds > settings.stale_minutes * 60
        devices[item["device_id"]] = item
    return devices


def _build_dashboard_payload(settings: Settings) -> dict[str, Any]:
    devices = _build_status_payload(settings)
    history = fetch_recent_history(settings.db_path, settings.ui_history_limit)
    generated_at_utc = _utc_now_iso()

    for rows in history.values():
        for row in rows:
            row["received_at_local"] = _format_local(row["received_at_utc"], settings.timezone)
            row["sent_at_local"] = _format_local(row["sent_at_utc"], settings.timezone)

    return {
        "generated_at_utc": generated_at_utc,
        "generated_at_local": _format_local(generated_at_utc, settings.timezone),
        "devices": devices,
        "history": history,
        "reading_count": fetch_reading_count(settings.db_path),
        "latest_archive": fetch_latest_archive_run(settings.db_path),
    }


def _build_client_payload(settings: Settings, device_id: str) -> dict[str, Any]:
    generated_at_utc = _utc_now_iso()
    devices = _build_status_payload(settings)

    return {
        "generated_at_utc": generated_at_utc,
        "generated_at_local": _format_local(generated_at_utc, settings.timezone),
        "device_id": device_id,
        "device": devices.get(device_id),
        "temperature_snapshots": _build_temperature_snapshots(settings, device_id),
    }


def _build_temperature_snapshots(
    settings: Settings,
    device_id: str,
) -> list[dict[str, Any]]:
    target_hours = {item["hour"] for item in CLIENT_TEMPERATURE_HOURS}
    readings_by_hour: dict[int, dict[str, Any]] = {}

    for row in fetch_temperature_readings(settings.db_path, device_id=device_id):
        local_hour = _local_hour(row["received_at_utc"], settings.timezone)
        if local_hour not in target_hours or local_hour in readings_by_hour:
            continue
        row["received_at_local"] = _format_local(row["received_at_utc"], settings.timezone)
        row["sent_at_local"] = _format_local(row["sent_at_utc"], settings.timezone)
        readings_by_hour[local_hour] = row
        if len(readings_by_hour) == len(target_hours):
            break

    return [
        {
            "label": item["label"],
            "hour": item["hour"],
            "reading": readings_by_hour.get(item["hour"]),
        }
        for item in CLIENT_TEMPERATURE_HOURS
    ]


def _local_hour(timestamp_utc: str | None, timezone_name: str) -> int | None:
    if not timestamp_utc:
        return None
    parsed = datetime.fromisoformat(timestamp_utc)
    return parsed.astimezone(ZoneInfo(timezone_name)).hour


def _format_local(timestamp_utc: str | None, timezone_name: str) -> str | None:
    if not timestamp_utc:
        return None
    parsed = datetime.fromisoformat(timestamp_utc)
    local_time = parsed.astimezone(ZoneInfo(timezone_name))
    return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")


def _age_seconds(timestamp_utc: str | None) -> int:
    if not timestamp_utc:
        return 0
    parsed = datetime.fromisoformat(timestamp_utc)
    return int((datetime.now(timezone.utc) - parsed).total_seconds())


def main() -> None:
    settings = load_settings()
    app = create_app(settings)

    try:
        from waitress import serve
    except ImportError:
        app.run(host=settings.host, port=settings.port, debug=False)
        return

    serve(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
