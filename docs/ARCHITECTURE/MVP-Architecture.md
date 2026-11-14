# HarirSmart AI — MVP Architecture & Implementation Notes

- Version: 0.1.0
- Status: executable software foundation; not approved for plant deployment
- Reference requirements: [BRS](../BRS/BRS-HarirSmart-AI.md), [SRS](../SRS/SRS-HarirSmart-AI.md)

## 1. MVP boundary

The first increment is a local, read-only demonstrator for a tissue-machine process. It provides a synthetic sample source, ingestion and data-quality validation, dashboard KPIs, a transparent what-if optimizer, and operator decision/audit capture.

There is deliberately no PLC/DCS write client, actuator endpoint, OPC UA write method, MQTT publish-to-control topic, or automatic setpoint execution. A proposal is a software record only.

**All sample values, plausibility ranges, perturbations, and formula coefficients in app/core.py are illustrative. They are not actual Harir Khuzestan machine operating limits or a validated process model.** Do not use them to operate equipment.

## 2. Logical architecture

PLC / DCS / SCADA / Historian (future, read-only)
→ OT read-only gateway / protocol adapter (future)
→ Ingestion API
→ DVR / quality gate
→ validated process snapshot
→ KPI + Digital Twin / scenario model
→ constrained optimizer
→ Advisory API
→ operator dashboard
→ decision / audit log

Cross-cutting controls: RBAC, time synchronization, provenance, model/version registry, health monitoring, backup and OT/IT segmentation. These are design requirements; the current in-memory MVP does not yet implement production-grade persistence, identity management, or a deployed OT gateway.

## 3. Implemented components

| Component | Current implementation | Next production step |
|---|---|---|
| API | FastAPI endpoints under /api/v1 | Authentication, RBAC, versioned contracts |
| Simulator | Deterministic synthetic sample | Calibrated dynamic model using plant-approved data |
| DVR | Required fields, numeric plausibility, timestamp/freshness, moisture consistency | Per-tag rules, duplicate/out-of-order handling, drift detection, reconciliation |
| KPI | Moisture delta and steam/production proxy | Meter-backed kg steam/t good product and kWh/t with approved energy boundary |
| Optimizer | Transparent finite grid search and demo delta bounds | Engineering-approved constraints, multi-objective Pareto set and validated process surrogate |
| Dashboard | Persian RTL single-page view | Role-based views, trends, historian queries and alarm lifecycle |
| Audit | In-memory event list | Append-only durable store, user identity and retention controls |
| Digital twin | Static what-if surrogate coefficients | Dynamic mass/energy balance, parameter estimation and validation |
| RL | Not implemented in the MVP | Offline training/evaluation in simulator only; never online exploration on equipment |

## 4. API contract

- GET /api/v1/health — service health and explicit read-only mode.
- GET /api/v1/simulator/sample — create a synthetic sample.
- POST /api/v1/samples — validate and ingest a process sample.
- GET /api/v1/dashboard — latest sample, quality status and demo KPIs.
- POST /api/v1/optimize — produce a simulation-only advisory; returns 409 if no sample and 422 if data quality fails.
- POST /api/v1/proposals/{proposal_id}/decision — record accepted/rejected/deferred operator decision; does not execute it.
- GET /api/v1/audit — recent audit events.

No endpoint accepts or transmits a machine command.

## 5. Data model

The current API uses a compact process snapshot: timestamp, source, moisture_in_pct, moisture_out_pct, press_load_pct, dryer_temp_c, steam_flow_tph, machine_speed_m_min, and basis_weight_g_m2.

The next normalized storage model should follow the SRS entities: TagDefinition, ProcessSample, ProductionRun, LabResult, EnergyRecord, ModelVersion, Prediction, OptimizationProposal, OperatorDecision, AlarmEvent, and AuditEvent. Store raw and validated values separately, with unit, source timestamp, received timestamp, quality flag and provenance.

## 6. KPI definitions

Use the BRS definitions as the authoritative business definitions:
- Specific steam = metered steam mass / good-product mass (e.g. kg/t).
- Dryer specific energy = metered dryer energy / good-product mass (e.g. kWh/t or GJ/t).
- Outlet moisture = online measurement cross-checked against lab method.
- Moisture-profile uniformity = standard deviation/range of a validated cross-machine or machine-direction profile.
- Out-of-spec rate = nonconforming product mass / total produced mass.
- Waste rate = waste mass / total production mass.
- Good production rate = saleable tonnes / production time.
- Advisory acceptance = accepted valid proposals / valid proposals.

The MVP steam_to_production_proxy is explicitly a synthetic proxy, not a reportable plant KPI. Energy savings (including the BRS 10–20% research target) are hypotheses to test against a normalized baseline, not a guaranteed outcome.

## 7. DVR rules and fail-safe behavior

Current gate rejects missing/non-numeric/non-finite values, values outside broad demo plausibility ranges, invalid/future/stale timestamps and outlet moisture above inlet moisture. An invalid snapshot must not be used to generate a recommendation. Production DVR must additionally handle sensor quality codes, duplicate samples, out-of-order data, unit conversion, time alignment, drift, redundant-sensor reconciliation and immutable raw-data retention.

Fail closed for advisory generation: when critical data are stale, invalid, unavailable or out-of-domain, return no recommendation. Existing plant control remains independent and unaffected.

## 8. Optimization and safety boundary

The demonstrator scores a small set of synthetic press-load and dryer-temperature perturbations using a transparent objective combining an energy proxy and moisture deviation. It is an algorithm plumbing test, not a validated multi-objective process optimizer.

The demo delta bounds are software test bounds only. Real hard constraints must be obtained from machine OEM documentation and approved plant engineering documents, then versioned by grade, equipment state and operating mode. Safety constraints are hard filters and must never be represented only as reward penalties.

## 9. Digital twin and offline RL roadmap

1. Start with mass/energy balances and a transparent baseline.
2. Calibrate model parameters on time-aligned historian, lab and meter data.
3. Validate on held-out time periods and across grade/speed families.
4. Add disturbance and sensor-fault scenarios.
5. Benchmark constrained classical optimization against baseline.
6. Only then consider offline RL training on a versioned simulator/dataset.
7. Evaluate policy robustness, uncertainty, OOD behavior and constraint satisfaction.
8. Expose approved outputs in shadow/advisory mode only.

No exploration, policy execution, or automatic setpoint changes on live equipment are permitted in this scope.

## 10. Run locally

~~~bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
~~~

Open http://127.0.0.1:8000 for the dashboard and http://127.0.0.1:8000/docs for the API schema.

Run tests:

~~~bash
pytest -q
~~~

## 11. Required before any plant pilot

Obtain and approve the actual tag list, P&ID/process flow, machine configuration, OEM limits, PLC/DCS/historian interfaces, OT network design, calibrated steam/energy meters, grade recipes, lab quality data, cybersecurity requirements and HSE review. Perform FAT/SAT, access-control tests, failure-mode tests, backup/restore tests and formal operator training. A read-only network architecture and a separate security review are prerequisites.
