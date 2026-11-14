from fastapi.testclient import TestClient

import app.main as main


def setup_function():
    main.AUDIT.clear()
    main.LATEST_SAMPLE = None
    main.LATEST_SAMPLE_ID = None
    main.LATEST_PROPOSAL = None
    main.STORE.clear()


def test_health_explicitly_disables_plc_writes():
    client = TestClient(main.app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "READ_ONLY_ADVISORY"
    assert response.json()["plc_write_enabled"] is False
    assert response.json()["storage"] == "sqlite"


def test_simulator_dashboard_and_advisory_flow_is_read_only():
    client = TestClient(main.app)
    sample_response = client.get("/api/v1/simulator/sample")
    assert sample_response.status_code == 200

    dashboard_response = client.get("/api/v1/dashboard")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["sample"] is not None
    assert dashboard_response.json()["dvr"]["quality_flag"] == "GOOD"

    proposal_response = client.post("/api/v1/optimize")
    assert proposal_response.status_code == 200
    proposal = proposal_response.json()
    assert proposal["mode"] == "ADVISORY_SIMULATION_ONLY"
    assert proposal["pareto_front"]
    assert "no PLC/DCS" in proposal["execution"]

    decision_response = client.post(
        f"/api/v1/proposals/{proposal['proposal_id']}/decision",
        json={"decision": "accepted", "reason": "Reviewed in test", "actor": "test-operator"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["execution"] == "No process command was sent."
    assert main.STORE.counts()["audit_events"] >= 3


def test_twin_and_history_endpoints():
    client = TestClient(main.app)
    client.get("/api/v1/simulator/sample")
    twin = client.post(
        "/api/v1/twin/simulate",
        json={"press_load_delta_pct": 1.0, "dryer_temp_delta_c": -0.5},
    )
    assert twin.status_code == 200
    assert twin.json()["model_validity"] == "ILLUSTRATIVE_ONLY_NOT_CALIBRATED"
    history = client.get("/api/v1/history?limit=5")
    assert history.status_code == 200
    assert history.json()["items"][0]["sample"]["source"] == "simulator"


def test_invalid_sample_is_stored_but_not_promoted_to_current_state():
    client = TestClient(main.app)
    payload = {
        "timestamp": "2026-11-14T12:00:00+00:00",
        "moisture_in_pct": 45,
        "moisture_out_pct": 80,
        "press_load_pct": 60,
        "dryer_temp_c": 110,
        "steam_flow_tph": 2.8,
        "machine_speed_m_min": 950,
        "basis_weight_g_m2": 18,
        "source": "test",
    }
    response = client.post("/api/v1/samples", json=payload)
    assert response.status_code == 200
    assert response.json()["quality"]["is_valid"] is False
    assert client.get("/api/v1/dashboard").json()["sample"] is None
    assert client.get("/api/v1/history").json()["count"] == 1


def test_openapi_has_no_plc_or_actuator_write_endpoint():
    schema = main.app.openapi()
    paths = list(schema["paths"])
    assert not any(
        any(token in path.lower() for token in ("plc", "actuator", "setpoint", "command"))
        for path in paths
    )
