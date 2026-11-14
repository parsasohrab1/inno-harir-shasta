from fastapi.testclient import TestClient

import app.main as main


def setup_function():
    main.AUDIT.clear()
    main.LATEST_SAMPLE = None
    main.LATEST_PROPOSAL = None


def test_health_explicitly_disables_plc_writes():
    client = TestClient(main.app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "READ_ONLY_ADVISORY"
    assert response.json()["plc_write_enabled"] is False


def test_simulator_dashboard_and_advisory_flow_is_read_only():
    client = TestClient(main.app)
    sample_response = client.get("/api/v1/simulator/sample")
    assert sample_response.status_code == 200

    dashboard_response = client.get("/api/v1/dashboard")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["sample"] is not None

    proposal_response = client.post("/api/v1/optimize")
    assert proposal_response.status_code == 200
    proposal = proposal_response.json()
    assert proposal["mode"] == "ADVISORY_SIMULATION_ONLY"
    assert "no PLC/DCS" in proposal["execution"]

    decision_response = client.post(
        f"/api/v1/proposals/{proposal['proposal_id']}/decision",
        json={"decision": "accepted", "reason": "Reviewed in test", "actor": "test-operator"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["execution"] == "No process command was sent."


def test_openapi_has_no_plc_or_actuator_write_endpoint():
    schema = main.app.openapi()
    paths = list(schema["paths"])
    assert not any(
        any(token in path.lower() for token in ("plc", "actuator", "setpoint", "command"))
        for path in paths
    )
