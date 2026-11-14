from datetime import datetime, timedelta, timezone

from app.core import make_simulated_sample, optimize_advisory, validate_sample


def test_simulated_sample_is_valid():
    sample = make_simulated_sample()
    assert validate_sample(sample)["is_valid"] is True


def test_stale_sample_is_rejected():
    sample = make_simulated_sample()
    sample["timestamp"] = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    result = validate_sample(sample)
    assert result["is_valid"] is False
    assert "timestamp:stale_over_60s" in result["issues"]


def test_non_numeric_and_impossible_moisture_are_rejected():
    sample = make_simulated_sample()
    sample["steam_flow_tph"] = "not-a-number"
    sample["moisture_out_pct"] = 60
    result = validate_sample(sample)
    assert result["is_valid"] is False
    assert any("steam_flow_tph" in issue for issue in result["issues"])
    assert "moisture_out_exceeds_moisture_in" in result["issues"]


def test_optimizer_is_advisory_and_bounded():
    result = optimize_advisory(make_simulated_sample())
    assert result["mode"] == "ADVISORY_SIMULATION_ONLY"
    assert abs(result["recommended_delta"]["press_load_delta_pct"]) <= 2
    assert abs(result["recommended_delta"]["dryer_temp_delta_c"]) <= 1
    assert "no PLC/DCS" in result["execution"]
