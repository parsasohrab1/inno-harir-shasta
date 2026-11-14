"""Tag-level data validation and reconciliation helpers.

Raw values are retained in the result. This module flags data; it never silently
rewrites a sensor value or fills a missing critical measurement.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any


TAG_SPECS: dict[str, dict[str, Any]] = {
    "moisture_in_pct": {"unit": "%", "minimum": 0.0, "maximum": 100.0, "critical": True},
    "moisture_out_pct": {"unit": "%", "minimum": 0.0, "maximum": 100.0, "critical": True},
    "press_load_pct": {"unit": "%", "minimum": 0.0, "maximum": 100.0, "critical": True},
    "dryer_temp_c": {"unit": "degC", "minimum": -20.0, "maximum": 250.0, "critical": True},
    "steam_flow_tph": {"unit": "t/h", "minimum": 0.0, "maximum": 100.0, "critical": True},
    "machine_speed_m_min": {"unit": "m/min", "minimum": 0.0, "maximum": 3000.0, "critical": True},
    "basis_weight_g_m2": {"unit": "g/m2", "minimum": 1.0, "maximum": 200.0, "critical": True},
}


def build_tag_readings(sample: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt the MVP sample shape to a tag/provenance envelope."""
    return [
        {
            "tag_id": name,
            "value": sample.get(name),
            "unit": spec["unit"],
            "timestamp": sample.get("timestamp"),
            "source": sample.get("source", "unknown"),
            "quality": "GOOD",
        }
        for name, spec in TAG_SPECS.items()
    ]


def validate_tag_readings(
    readings: list[dict[str, Any]],
    now: datetime | None = None,
    max_age_seconds: int = 60,
) -> dict[str, Any]:
    """Validate units, ranges, timestamps, source quality and duplicate tag IDs."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    seen: set[str] = set()
    values: dict[str, float] = {}
    checked: list[dict[str, Any]] = []
    issues: list[str] = []
    invalid_critical = False
    suspect = False

    for reading in readings:
        tag_id = str(reading.get("tag_id", "")).strip()
        status = "VALID"
        reasons: list[str] = []
        spec = TAG_SPECS.get(tag_id)

        if not spec:
            status = "UNKNOWN"
            reasons.append("unknown_tag")
            suspect = True
        elif tag_id in seen:
            status = "INVALID"
            reasons.append("duplicate_tag")
            invalid_critical = invalid_critical or bool(spec["critical"])
        else:
            seen.add(tag_id)
            if reading.get("unit") != spec["unit"]:
                status = "INVALID"
                reasons.append("unit_mismatch")
            try:
                value = float(reading.get("value"))
                if not isfinite(value):
                    raise ValueError
            except (TypeError, ValueError):
                value = None
                status = "INVALID"
                reasons.append("missing_or_non_numeric")
            if value is not None and not spec["minimum"] <= value <= spec["maximum"]:
                status = "INVALID"
                reasons.append("outside_demo_plausibility_range")

            quality = str(reading.get("quality", "GOOD")).upper()
            if quality in {"BAD", "INVALID"}:
                status = "INVALID"
                reasons.append("source_quality_bad")
            elif quality not in {"GOOD", "VALID"}:
                if status == "VALID":
                    status = "SUSPECT"
                reasons.append("source_quality_uncertain")

            raw_timestamp = reading.get("timestamp")
            try:
                timestamp = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                age = (current - timestamp).total_seconds()
                if age < -30:
                    status = "INVALID"
                    reasons.append("timestamp_in_future")
                elif age > max_age_seconds and status != "INVALID":
                    status = "STALE"
                    reasons.append("timestamp_stale")
            except (TypeError, ValueError):
                status = "INVALID"
                reasons.append("timestamp_invalid")

            if status == "VALID" and value is not None:
                values[tag_id] = value
            elif status in {"INVALID", "STALE"} and spec["critical"]:
                invalid_critical = True
            if status == "SUSPECT":
                suspect = True

        if reasons:
            issues.extend(f"{tag_id}:{reason}" for reason in reasons)
        checked.append(
            {
                "tag_id": tag_id,
                "raw_value": reading.get("value"),
                "unit": reading.get("unit"),
                "timestamp": reading.get("timestamp"),
                "source": reading.get("source"),
                "status": status,
                "issues": reasons,
            }
        )

    missing_critical = [
        tag for tag, spec in TAG_SPECS.items()
        if spec["critical"] and tag not in seen
    ]
    if missing_critical:
        issues.extend(f"{tag}:missing_critical_tag" for tag in missing_critical)
        invalid_critical = True

    quality_flag = "BAD" if invalid_critical else ("SUSPECT" if suspect or issues else "GOOD")
    return {
        "quality_flag": quality_flag,
        "recommendation_allowed": quality_flag == "GOOD",
        "checked_tags": checked,
        "normalized_values": values,
        "missing_critical_tags": missing_critical,
        "issues": issues,
        "raw_values_preserved": True,
        "correction_applied": False,
    }


def reconcile_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Expose safe proxies and explicitly report unavailable physical balances."""
    try:
        moisture_removed = float(sample["moisture_in_pct"]) - float(sample["moisture_out_pct"])
        speed = float(sample["machine_speed_m_min"])
        basis = float(sample["basis_weight_g_m2"])
        steam = float(sample["steam_flow_tph"])
        production_proxy = max(0.05, speed * basis * 0.001 / 60.0)
        steam_intensity_proxy = steam / production_proxy
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        moisture_removed = None
        production_proxy = None
        steam_intensity_proxy = None

    return {
        "moisture_removed_pct_points": moisture_removed,
        "production_rate_proxy_tph": production_proxy,
        "steam_per_production_proxy": steam_intensity_proxy,
        "mass_balance": "NOT_COMPUTABLE_WITHOUT_WEB_WIDTH_AND_DRY_MASS_FLOW",
        "energy_balance": "PROXY_ONLY_CALIBRATED_STEAM_AND_ENERGY_METERS_REQUIRED",
    }
