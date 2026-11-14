"""Pure domain logic for the read-only HarirSmart AI demonstrator.

All numeric envelopes in this module are synthetic demo bounds. They are NOT
machine limits, operating procedures, or approved setpoints.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

REQUIRED = {
    "moisture_in_pct": (0.0, 100.0),
    "moisture_out_pct": (0.0, 100.0),
    "press_load_pct": (0.0, 100.0),
    "dryer_temp_c": (-20.0, 250.0),
    "steam_flow_tph": (0.0, 100.0),
    "machine_speed_m_min": (0.0, 3000.0),
    "basis_weight_g_m2": (1.0, 200.0),
}

def validate_sample(sample: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Validate presence, numeric plausibility, timestamp and freshness."""
    issues: list[str] = []
    values: dict[str, float] = {}
    for name, (low, high) in REQUIRED.items():
        raw = sample.get(name)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            issues.append(f"{name}:missing_or_non_numeric")
            continue
        if not isfinite(value) or not low <= value <= high:
            issues.append(f"{name}:outside_demo_plausibility_range")
            continue
        values[name] = value

    raw_ts = sample.get("timestamp")
    try:
        timestamp = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age_s = (current - timestamp).total_seconds()
        if age_s < -30:
            issues.append("timestamp:in_future")
        elif age_s > 60:
            issues.append("timestamp:stale_over_60s")
    except (TypeError, ValueError):
        issues.append("timestamp:missing_or_invalid")

    if "moisture_in_pct" in values and "moisture_out_pct" in values:
        if values["moisture_out_pct"] > values["moisture_in_pct"]:
            issues.append("moisture_out_exceeds_moisture_in")

    return {
        "is_valid": not issues,
        "quality_flag": "GOOD" if not issues else "BAD",
        "issues": issues,
        "validated_values": values,
    }


def calculate_kpis(sample: dict[str, Any]) -> dict[str, float | None]:
    """Calculate demonstrator KPIs; production-normalized values need real meters."""
    speed = float(sample["machine_speed_m_min"])
    basis = float(sample["basis_weight_g_m2"])
    steam = float(sample["steam_flow_tph"])
    # Approximate web mass flow from width-free lineal proxy; not a plant KPI.
    production_proxy_tph = max(0.05, speed * basis * 0.001 / 60.0)
    return {
        "moisture_out_pct": float(sample["moisture_out_pct"]),
        "moisture_delta_pct_point": float(sample["moisture_in_pct"]) - float(sample["moisture_out_pct"]),
        "steam_to_production_proxy": steam / production_proxy_tph,
        "production_proxy_tph": production_proxy_tph,
    }


def optimize_advisory(sample: dict[str, Any]) -> dict[str, Any]:
    """Tiny transparent grid search; outputs deltas for simulation only."""
    current_temp = float(sample["dryer_temp_c"])
    current_press = float(sample["press_load_pct"])
    moisture_out = float(sample["moisture_out_pct"])
    steam = float(sample["steam_flow_tph"])
    candidates = []
    # Synthetic local perturbations, intentionally small and not plant setpoints.
    for press_delta in (-2.0, 0.0, 2.0):
        for temp_delta in (-1.0, 0.0, 1.0):
            predicted_moisture = moisture_out - 0.035 * press_delta - 0.12 * temp_delta
            energy_proxy = steam * (1.0 + 0.012 * temp_delta - 0.004 * press_delta)
            quality_penalty = max(0.0, 3.0 - predicted_moisture) + max(0.0, predicted_moisture - 7.0)
            # Demo hard guardrails on delta only; not engineering safety limits.
            feasible = abs(press_delta) <= 2.0 and abs(temp_delta) <= 1.0
            objective = energy_proxy + 2.0 * abs(predicted_moisture - 5.0) + 5.0 * quality_penalty
            candidates.append({
                "press_load_delta_pct": press_delta,
                "dryer_temp_delta_c": temp_delta,
                "predicted_moisture_out_pct": round(predicted_moisture, 3),
                "energy_proxy": round(energy_proxy, 4),
                "objective_score": round(objective, 4),
                "feasible_in_demo": feasible,
            })
    feasible = [c for c in candidates if c["feasible_in_demo"]]
    pareto = [
        c for c in feasible
        if not any(
            other is not c
            and other["energy_proxy"] <= c["energy_proxy"]
            and abs(other["predicted_moisture_out_pct"] - 5.0) <= abs(c["predicted_moisture_out_pct"] - 5.0)
            and (
                other["energy_proxy"] < c["energy_proxy"]
                or abs(other["predicted_moisture_out_pct"] - 5.0) < abs(c["predicted_moisture_out_pct"] - 5.0)
            )
            for other in feasible
        )
    ]
    best = min(feasible, key=lambda c: c["objective_score"])
    return {
        "mode": "ADVISORY_SIMULATION_ONLY",
        "status": "PROPOSAL",
        "basis": "synthetic_local_grid_search",
        "current_state": {"press_load_pct": current_press, "dryer_temp_c": current_temp},
        "recommended_delta": {
            "press_load_delta_pct": best["press_load_delta_pct"],
            "dryer_temp_delta_c": best["dryer_temp_delta_c"],
        },
        "predicted_outcomes": best,
        "alternatives": candidates,
        "pareto_front": pareto,
        "constraints_note": "Demo perturbation bounds only; not approved machine limits.",
        "execution": "NONE — no PLC/DCS write path exists in this MVP.",
    }


def make_simulated_sample() -> dict[str, Any]:
    """Deterministic sample generator for local demonstration."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "moisture_in_pct": 48.0,
        "moisture_out_pct": 5.2,
        "press_load_pct": 62.0,
        "dryer_temp_c": 112.0,
        "steam_flow_tph": 2.8,
        "machine_speed_m_min": 950.0,
        "basis_weight_g_m2": 18.0,
        "source": "built_in_simulator",
    }


def audit_record(action: str, actor: str, object_id: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "object_id": object_id,
        "details": details,
        "mode": "READ_ONLY_ADVISORY",
    }
