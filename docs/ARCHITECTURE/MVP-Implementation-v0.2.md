# HarirSmart AI — MVP Implementation Architecture v0.2

## 1. Scope and non-negotiable boundary

This increment extends the existing MVP; it does not recreate the FastAPI service or original dashboard. It remains a local, read-only demonstrator. No PLC/DCS write client, actuator endpoint, control topic, or setpoint execution path is implemented. Operator acceptance records acknowledgement only.

All sample ranges, coefficients and scenario envelopes are synthetic software-test values. They are not operating limits, OEM recommendations, or process guarantees.

## 2. Runtime service architecture

Synthetic simulator / read-only sample API
→ Ingestion API
→ Raw sample + provenance persistence (SQLite)
→ DVR quality gate
→ Validated process snapshot
→ KPI proxy + Digital Twin what-if
→ Constrained multi-objective scenario search / Pareto
→ Advisory API
→ RTL operator dashboard + decision/audit

Future OT source path (not enabled): PLC/DCS/SCADA/Historian → approved OT read-only gateway → tag adapter → ingestion. Any future adapter must expose read methods only, use network segmentation/DMZ and least privilege, and undergo OT cybersecurity review. Do not add a control topic or write method.

## 3. Implemented modules

| Module | Responsibility | Persistence / safety |
|---|---|---|
| app/main.py | FastAPI orchestration, request validation, quality gate, API | No write endpoint |
| app/storage.py | Samples, proposals, audit events | SQLite WAL; per-operation connection |
| app/dvr.py | Tag metadata, quality flags, reconciliation proxies | Raw values retained; no silent correction |
| app/process_model.py | Digital Twin and scenario/Pareto evaluation | Synthetic coefficients only |
| app/core.py | Existing sample validation, KPI proxies, simulator and audit utility | Retained baseline |
| app/offline_rl.py | Fitted-Q scaffold over fixed offline transitions | Rejects live source |
| app/static/index.html | Persian RTL operator dashboard | Read-only visualization |

## 4. Data model

### samples table
- sample_id: unique ingestion identifier.
- source_timestamp and received_at: source time and server receive time.
- source: simulator/API source label.
- payload_json: raw-as-ingested sample payload.
- quality_json and dvr_json: validation evidence, status and issues.

### proposals table
- proposal identifier, associated sample identifier, creation time, full advisory/Pareto payload.
- No executable command payload or actuator target is stored.

### audit_events table
- event identifier, UTC timestamp, actor, action, object identifier and full JSON payload.
- Events are append-only through the application API. SQLite is suitable for a single-node MVP; production retention, backup, tamper evidence and access controls require a hardened database/audit service.

## 5. DVR and data-quality semantics

Each tag has an expected unit, illustrative plausibility range and criticality flag. The DVR checks:
- tag identity and duplicates;
- numeric/finite value and unit;
- configured plausibility range;
- source quality flag;
- source timestamp, future skew and freshness;
- missing critical tags.

Statuses are VALID, SUSPECT, STALE, INVALID, or UNKNOWN; overall quality is GOOD, SUSPECT, or BAD. A recommendation is allowed only when all required critical tags are GOOD. Invalid raw samples are retained for diagnosis but are not promoted to the active process state. No automatic imputation or correction is performed.

Mass balance is deliberately reported as not computable until web width and dry mass flow are available. Steam-per-production is explicitly a proxy until calibrated meters and good-product mass flow are connected.

## 6. Digital Twin and optimization

The v0.2 Twin is a deterministic empirical scenario model for software integration testing. It estimates moisture, steam-flow and a lineal production proxy from press-load and dryer-temperature deltas. It labels every result ILLUSTRATIVE_ONLY_NOT_CALIBRATED.

The scenario search enumerates a small grid inside synthetic demo envelopes. It returns a non-dominated set for:
1. minimizing steam per production proxy;
2. minimizing distance from a demonstrator moisture target;
3. maximizing production-rate proxy.

Hard demo bounds are applied before ranking; they are not softened into reward penalties. The selected result is a proposal only. Replace this model only after process engineering supplies validated balances, OEM envelopes, uncertainty bounds, and held-out historian/laboratory validation.

## 7. KPI definitions and data prerequisites

| KPI | MVP expression | Required plant-grade source |
|---|---|---|
| Outlet moisture | sample moisture-out tag | calibrated online scanner + lab reference |
| Moisture removal | inlet minus outlet moisture, percentage points | aligned inlet/outlet measurements |
| Production rate | speed × basis weight proxy (width-free) | web width, dry mass flow, good-product scale |
| Steam intensity | steam flow / production proxy | calibrated steam meter + good-product mass |
| Dryer energy intensity | not yet computed as a plant KPI | fuel/steam/electric meters and agreed energy boundary |
| Moisture uniformity | not yet computed | cross-direction profile scanner / lab protocol |
| Off-spec and broke rate | not yet computed | QMS/MES and production reconciliation |
| System availability | operational telemetry, future | monitored service uptime |

The energy-saving target of 10–20% is a testable pilot hypothesis only. Use normalized baselines by grade, basis weight, furnish, speed, and operating condition. Require quality and production non-regression and calibrated metering before any savings claim.

## 8. API surface

- GET /api/v1/health — service mode and storage counts.
- GET /api/v1/simulator/sample — synthetic sample generation and persistence.
- POST /api/v1/samples — sample ingestion; invalid records retained.
- GET /api/v1/history — bounded recent sample history.
- POST /api/v1/dvr/validate — tag-batch validation.
- GET /api/v1/dashboard — current validated snapshot and KPI/DVR.
- POST /api/v1/twin/simulate — bounded what-if simulation.
- POST /api/v1/optimize — multi-objective advisory/Pareto proposal.
- POST /api/v1/proposals/{id}/decision — acknowledgement and audit only.
- GET /api/v1/audit — bounded audit event retrieval.

No API accepts a PLC address, actuator identifier, control command or real setpoint write.

## 9. Run, verification and next gate

Run: pip install -r requirements.txt, uvicorn app.main:app --reload, pytest -q. The local database defaults to data/harirsmart.db; override with HARIRSMART_DB_PATH.

Next gate: obtain approved tag list and units; verify historian timestamps and quality; obtain OEM process envelopes and machine drawings; add a read-only adapter behind an approved gateway; commission calibrated steam/energy and web-width measurements; validate Twin parameters on held-out production periods; conduct OT security and process-safety review before any plant pilot.
