"""Illustrative tissue-machine digital twin and multi-objective scenario search.

The coefficients and envelopes are synthetic software-test values, not OEM limits or a
validated physical model. Never use this model to set or control real equipment.
"""
from __future__ import annotations

from typing import Any

from .core import calculate_kpis, validate_sample


DEMO_ENVELOPE = {
    "press_load_delta_pct": (-2.0, 2.0),
    "dryer_temp_delta_c": (-1.0, 1.0),
    "press_load_pct": (10.0, 90.0),
    "dryer_temp_c": (40.0, 180.0),
    "moisture_out_pct": (3.0, 7.0),
}


def simulate_tissue_process(
    sample: dict[str, Any],
    press_load_delta_pct: float = 0.0,
    dryer_temp_delta_c: float = 0.0,
) -> dict[str, Any]:
    """Run a deterministic local what-if scenario with explicit demo guardrails."""
    quality = validate_sample(sample)
    if not quality["is_valid"]:
        raise ValueError("Digital twin requires a GOOD process sample")
    press_delta = float(press_load_delta_pct)
    temp_delta = float(dryer_temp_delta_c)
    if not DEMO_ENVELOPE["press_load_delta_pct"][0] <= press_delta <= DEMO_ENVELOPE["press_load_delta_pct"][1]:
        raise ValueError("press_load_delta_pct is outside the demo scenario envelope")
    if not DEMO_ENVELOPE["dryer_temp_delta_c"][0] <= temp_delta <= DEMO_ENVELOPE["dryer_temp_delta_c"][1]:
        raise ValueError("dryer_temp_delta_c is outside the demo scenario envelope")

    current_press = float(sample["press_load_pct"])
    current_temp = float(sample["dryer_temp_c"])
    moisture = float(sample["moisture_out_pct"]) - 0.035 * press_delta - 0.12 * temp_delta
    steam = float(sample["steam_flow_tph"]) * (1.0 + 0.012 * temp_delta - 0.004 * press_delta)
    production = float(calculate_kpis(sample)["production_proxy_tph"])
    adjusted_press = current_press + press_delta
    adjusted_temp = current_temp + temp_delta
    moisture_low, moisture_high = DEMO_ENVELOPE["moisture_out_pct"]
    feasible = (
        DEMO_ENVELOPE["press_load_pct"][0] <= adjusted_press <= DEMO_ENVELOPE["press_load_pct"][1]
        and DEMO_ENVELOPE["dryer_temp_c"][0] <= adjusted_temp <= DEMO_ENVELOPE["dryer_temp_c"][1]
        and moisture_low <= moisture <= moisture_high
    )
    return {
        "model_id": "TISSUE-DEMO-EMPIRICAL-v0.2",
        "model_validity": "ILLUSTRATIVE_ONLY_NOT_CALIBRATED",
        "current_state": {
            "press_load_pct": current_press,
            "dryer_temp_c": current_temp,
            "moisture_out_pct": float(sample["moisture_out_pct"]),
        },
        "scenario": {
            "press_load_delta_pct": press_delta,
            "dryer_temp_delta_c": temp_delta,
        },
        "predicted": {
            "moisture_out_pct": round(moisture, 4),
            "steam_flow_tph": round(steam, 4),
            "production_proxy_tph": round(production, 5),
            "steam_per_production_proxy": round(steam / production, 5),
            "moisture_error_from_demo_target_pct_points": round(abs(moisture - 5.0), 4),
        },
        "constraints": {
            "feasible_in_demo": feasible,
            "demo_envelope": {key: list(value) for key, value in DEMO_ENVELOPE.items()},
        },
        "execution": "SIMULATION_ONLY — no PLC/DCS command was generated.",
    }


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    no_worse = (
        left["steam_per_production_proxy"] <= right["steam_per_production_proxy"]
        and left["moisture_error_pct_points"] <= right["moisture_error_pct_points"]
        and left["production_proxy_tph"] >= right["production_proxy_tph"]
    )
    strictly_better = (
        left["steam_per_production_proxy"] < right["steam_per_production_proxy"]
        or left["moisture_error_pct_points"] < right["moisture_error_pct_points"]
        or left["production_proxy_tph"] > right["production_proxy_tph"]
    )
    return no_worse and strictly_better


def optimize_multiobjective(sample: dict[str, Any]) -> dict[str, Any]:
    """Enumerate safe demo scenarios and return a non-dominated Pareto set."""
    candidates: list[dict[str, Any]] = []
    for press_delta in (-2.0, 0.0, 2.0):
        for temp_delta in (-1.0, 0.0, 1.0):
            result = simulate_tissue_process(sample, press_delta, temp_delta)
            predicted = result["predicted"]
            candidates.append(
                {
                    **result["scenario"],
                    "predicted_moisture_out_pct": predicted["moisture_out_pct"],
                    "predicted_steam_flow_tph": predicted["steam_flow_tph"],
                    "steam_per_production_proxy": predicted["steam_per_production_proxy"],
                    "production_proxy_tph": predicted["production_proxy_tph"],
                    "moisture_error_pct_points": predicted["moisture_error_from_demo_target_pct_points"],
                    "feasible_in_demo": result["constraints"]["feasible_in_demo"],
                    "model_id": result["model_id"],
                }
            )

    feasible = [item for item in candidates if item["feasible_in_demo"]]
    if not feasible:
        raise ValueError("No feasible scenario exists inside the demo envelope")

    pareto = [
        candidate for candidate in feasible
        if not any(other is not candidate and _dominates(other, candidate) for other in feasible)
    ]
    for candidate in feasible:
        candidate["objective_score"] = round(
            candidate["steam_per_production_proxy"]
            + 0.35 * candidate["moisture_error_pct_points"]
            - 0.10 * candidate["production_proxy_tph"],
            5,
        )
    best = min(feasible, key=lambda item: item["objective_score"])
    return {
        "mode": "ADVISORY_SIMULATION_ONLY",
        "status": "PROPOSAL",
        "basis": "digital_twin_demo_grid_search",
        "model_validity": "ILLUSTRATIVE_ONLY_NOT_CALIBRATED",
        "current_state": {
            "press_load_pct": float(sample["press_load_pct"]),
            "dryer_temp_c": float(sample["dryer_temp_c"]),
        },
        "recommended_delta": {
            "press_load_delta_pct": best["press_load_delta_pct"],
            "dryer_temp_delta_c": best["dryer_temp_delta_c"],
        },
        "predicted_outcomes": best,
        "alternatives": candidates,
        "pareto_front": pareto,
        "objective_directions": {
            "steam_per_production_proxy": "minimize",
            "moisture_error_pct_points": "minimize",
            "production_proxy_tph": "maximize",
        },
        "constraints_note": "Synthetic software-test envelope only; not approved machine limits or setpoints.",
        "execution": "NONE — advisory record only; no PLC/DCS write path exists.",
    }
