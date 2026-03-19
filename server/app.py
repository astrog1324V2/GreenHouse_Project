from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any
from zoneinfo import ZoneInfo

from flask import Flask, Response, jsonify, render_template, request, send_file

from .archive import run_weekly_archive
from .config import Settings, load_settings
from .db import (
    fetch_device_statuses,
    fetch_latest_archive_run,
    fetch_reading_count,
    fetch_recent_history,
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
VALID_MODES = {"summer", "range_test"}


def create_app(settings: Settings | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SETTINGS"] = settings or load_settings()

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
        statuses = _build_status_payload(current_settings)
        return jsonify(
            {
                "generated_at_utc": _utc_now_iso(),
                "devices": statuses,
                "deltas": _build_deltas(statuses),
                "reading_count": fetch_reading_count(current_settings.db_path),
                "latest_archive": fetch_latest_archive_run(current_settings.db_path),
            }
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

    @app.get("/")
    def index() -> str:
        statuses = _build_status_payload(current_settings)
        history = fetch_recent_history(
            current_settings.db_path, current_settings.ui_history_limit
        )
        reading_count = fetch_reading_count(current_settings.db_path)
        return render_template(
            "index.html",
            generated_at_local=_format_local(_utc_now_iso(), current_settings.timezone),
            devices=statuses,
            deltas=_build_deltas(statuses),
            history=history,
            reading_count=reading_count,
            latest_archive=fetch_latest_archive_run(current_settings.db_path),
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
        raise ValueError("mode must be 'summer' or 'range_test'.")

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


def _build_deltas(devices: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    greenhouse = devices.get("greenhouse")
    outdoor = devices.get("outdoor")
    if not greenhouse or not outdoor:
        return {"temperature_c": None, "humidity_pct": None, "light_lux": None}

    return {
        "temperature_c": _delta(greenhouse.get("temperature_c"), outdoor.get("temperature_c")),
        "humidity_pct": _delta(greenhouse.get("humidity_pct"), outdoor.get("humidity_pct")),
        "light_lux": _delta(greenhouse.get("light_lux"), outdoor.get("light_lux")),
    }


def _delta(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 2)


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
