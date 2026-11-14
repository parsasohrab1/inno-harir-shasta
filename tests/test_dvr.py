from datetime import datetime, timedelta, timezone

from app.dvr import TAG_SPECS, build_tag_readings, validate_tag_readings
from app.core import make_simulated_sample


def test_complete_tag_batch_is_good_and_preserves_raw_values():
    sample = make_simulated_sample()
    readings = build_tag_readings(sample)
    result = validate_tag_readings(readings)
    assert result["quality_flag"] == "GOOD"
    assert result["recommendation_allowed"] is True
    assert result["raw_values_preserved"] is True
    assert result["correction_applied"] is False


def test_unit_mismatch_blocks_recommendation():
    readings = build_tag_readings(make_simulated_sample())
    readings[0]["unit"] = "bar"
    result = validate_tag_readings(readings)
    assert result["quality_flag"] == "BAD"
    assert result["recommendation_allowed"] is False
    assert any("unit_mismatch" in issue for issue in result["issues"])


def test_stale_critical_tag_blocks_recommendation():
    readings = build_tag_readings(make_simulated_sample())
    readings[0]["timestamp"] = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    result = validate_tag_readings(readings)
    assert result["quality_flag"] == "BAD"
    assert result["recommendation_allowed"] is False


def test_missing_critical_tag_is_not_imputed():
    readings = [item for item in build_tag_readings(make_simulated_sample()) if item["tag_id"] != "steam_flow_tph"]
    result = validate_tag_readings(readings)
    assert "steam_flow_tph" in result["missing_critical_tags"]
    assert result["correction_applied"] is False


def test_tag_registry_has_units_for_all_sample_fields():
    assert set(TAG_SPECS) == {
        "moisture_in_pct", "moisture_out_pct", "press_load_pct", "dryer_temp_c",
        "steam_flow_tph", "machine_speed_m_min", "basis_weight_g_m2",
    }
