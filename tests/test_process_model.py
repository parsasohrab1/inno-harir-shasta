import pytest

from app.core import make_simulated_sample
from app.process_model import optimize_multiobjective, simulate_tissue_process


def test_digital_twin_returns_explicit_illustrative_validity():
    result = simulate_tissue_process(make_simulated_sample(), 1.0, -0.5)
    assert result["model_validity"] == "ILLUSTRATIVE_ONLY_NOT_CALIBRATED"
    assert result["constraints"]["feasible_in_demo"] is True
    assert "no PLC/DCS" in result["execution"]


def test_digital_twin_rejects_scenario_outside_demo_envelope():
    with pytest.raises(ValueError):
        simulate_tissue_process(make_simulated_sample(), 3.0, 0.0)


def test_optimizer_returns_nonempty_pareto_front_and_three_objectives():
    result = optimize_multiobjective(make_simulated_sample())
    assert result["pareto_front"]
    assert result["objective_directions"]["steam_per_production_proxy"] == "minimize"
    assert result["objective_directions"]["production_proxy_tph"] == "maximize"
    assert all(item["feasible_in_demo"] for item in result["pareto_front"])
