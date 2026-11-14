# HarirSmart AI — Implementation Status

- Branch: main
- MVP increment: 0.2.0
- Scope: local demonstrator; not approved for production or plant control.

## Verified baseline reused

The repository already had FastAPI ingestion/dashboard endpoints, synthetic sample generation, basic sample validation, KPI proxies, a grid-search advisory optimizer, operator decision logging, a Persian RTL dashboard, and a dataset-only fitted-Q scaffold. These were retained rather than recreated in a parallel application tree.

## Increment 0.2 delivered

- app/storage.py: SQLite persistence for raw samples, quality/DVR results, proposals and audit events; WAL mode and bounded read APIs.
- app/dvr.py: tag registry, unit/range/time/duplicate/missing/source-quality checks, raw-value preservation, and explicit proxy-only reconciliation.
- app/process_model.py: deterministic illustrative digital twin, bounded what-if scenarios, three-objective enumeration and non-dominated Pareto output.
- app/main.py: history, DVR validation and twin simulation endpoints; durable sample/proposal/audit storage; optimizer quality gate.
- app/adapters/: explicit read-only tag-source contract and simulator implementation; no write method is defined.
- app/static/index.html: industrial RTL operator view for process KPIs, quality, history, Twin and Pareto recommendation.
- Tests cover DVR, digital-twin bounds, Pareto outputs, SQLite restart persistence, API workflow, and read-only route surface.

## Data and safety contract

1. Raw samples are persisted even when invalid; invalid/stale/uncertain critical data cannot become the current recommendation state.
2. DVR does not silently impute or overwrite raw sensor values. It preserves values and emits quality flags/issues.
3. Current production and steam-intensity values remain proxies because web width, dry mass flow, calibrated meters and product-good mass are not yet connected.
4. Twin coefficients and guardrails are synthetic test envelopes, not OEM limits, approved setpoints or a validated physical model.
5. Optimizer results are advisory records only. The API contains no PLC/DCS write, actuator, or command endpoint.
6. RL remains dataset-only and offline. No online exploration, environment stepping or equipment interaction is introduced.
7. 10–20% energy reduction remains a pilot hypothesis requiring normalized baseline, calibrated metering, and quality/production non-regression.

## Run and verify

From repository root: pip install -r requirements.txt, uvicorn app.main:app --reload, then pytest -q. The SQLite file defaults to data/harirsmart.db; override with HARIRSMART_DB_PATH.

Passing software tests do not validate the process model, machine safety envelope, cybersecurity, or production readiness. Before OT connection, complete tag mapping, time synchronization, historian validation, OEM envelope approval, OT security review, HAZOP/MOC as applicable, and FAT/SAT.
