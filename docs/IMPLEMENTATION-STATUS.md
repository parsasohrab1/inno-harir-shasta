# HarirSmart AI — Implementation Status

- Repository branch: `main`
- Baseline: MVP 0.1.0
- Scope: local demonstrator; not approved for production or plant control.

## Existing implementation verified in repository

The repository already contains a FastAPI service, synthetic sample generator, input validation/DVR checks, dashboard KPI calculations, an advisory grid-search optimizer with Pareto alternatives, operator decision/audit capture, Persian RTL dashboard, and a dataset-only fitted-Q iteration scaffold in `app/offline_rl.py`.

The existing architecture document is authoritative for the current implementation. This status note supplements it and avoids duplicating the implementation in a second, conflicting application tree.

## Additional API regression coverage

`tests/test_api.py` covers:
- explicit read-only health status and disabled PLC writes;
- end-to-end simulator → dashboard → advisory proposal → operator decision flow;
- absence of PLC, actuator, setpoint, or command routes in the generated OpenAPI schema.

## Known limitations / next engineering increments

1. The current service stores latest sample, proposal and audit events in process memory; introduce durable storage and restart-safe audit retention.
2. The current KPI production rate is a proxy; replace it with validated good-product mass flow and calibrated steam/energy meters.
3. Replace illustrative process coefficients and demo bounds only after obtaining OEM-approved envelopes and plant historian/lab data.
4. Add read-only OT gateway and protocol adapters only after OT cybersecurity review; no write methods or control topics.
5. Extend the Digital Twin with validated mass/energy balances, uncertainty estimates and held-out-period validation.
6. Keep RL offline and dataset-only. Do not add online exploration or equipment actuation.
7. Evaluate energy-saving hypotheses against a normalized baseline; do not present the 10–20% research target as a guaranteed result.

## Verification

Run from repository root:

```bash
pip install -r requirements.txt
pytest -q
```

The regression tests are committed for CI execution. Passing tests demonstrate software behavior only, not process-model validity or operational safety certification.
