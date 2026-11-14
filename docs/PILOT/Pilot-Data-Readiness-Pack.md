# HarirSmart AI — Industrial Pilot Data Readiness Pack

- Version: 0.1
- Status: data-request and engineering template; not an approved commissioning procedure
- Scope: read-only data acquisition, data qualification, mass/energy balance, Twin calibration and independent validation
- Safety boundary: Advisory only. No PLC/DCS writes, actuator commands, online RL, or setpoint changes.

## 1. Entry criteria

Do not connect to plant OT until the plant OT owner, process owner and cybersecurity owner approve the architecture, data path, accounts, firewall rules, gateway, retention and incident procedure in writing. Use an isolated approved read-only gateway/DMZ. No direct inbound connection from the application server to controllers. The adapter must expose reads only and must fail closed on authentication, timestamp, quality or communication errors.

Required plant approvals:
- Named process owner and shift/operator representatives.
- OT/IT network diagram and approved gateway/historian access method.
- Instrument list, loop diagrams, P&IDs, control narratives and machine configuration.
- OEM manuals and written operating/measurement envelopes for each relevant asset.
- Instrument calibration certificates and meter uncertainty.
- Laboratory methods, sample identity rules and quality specification by grade.
- Site HSE, MOC, cybersecurity and data-handling approvals as applicable.

## 2. Tag register and semantic mapping

Complete `templates/tag-register.csv` for every candidate tag. Do not infer tags from this template. Required fields include canonical tag, source system/path, equipment, process meaning, engineering unit, raw unit, conversion, scan/sample period, source timezone, timestamp semantics, quality semantics, approved physical range, criticality, calibration evidence, owner and approval status.

Rules:
1. Preserve raw value, raw unit, source timestamp, receive timestamp, source quality and original tag identity.
2. Convert to canonical units only in a derived field; retain conversion formula and version.
3. Use UTC internally while retaining source timezone and original timestamp.
4. Define whether timestamps represent acquisition, historian archive, batch event or laboratory sample time.
5. Do not forward-fill or interpolate critical values for live Advisory eligibility.
6. Quarantine unknown units, duplicate mappings, stale/future timestamps, bad source quality and unapproved tags.
7. OEM and plant-approved operating envelopes are configuration inputs, not inferred statistical ranges.

Suggested canonical dimensions (confirm applicability with the actual machine):
- Web/production: machine speed, web width, basis weight/grammage, grade, good-product mass/length.
- Stock and forming: stock flow, consistency, furnish identifiers, forming-section conditions and relevant drainage measurements.
- Press/dewatering: press load/pressure, nip condition, felt condition and available filtrate/flow measurements.
- Dryer/Yankee: shell/surface temperature, hood/air temperatures, pressure, burner/fuel flow, steam pressure/flow/condensate and exhaust conditions.
- Utilities: calibrated steam, fuel, electricity and water meters.
- Quality: reel/roll moisture, cross-direction profile if available, basis weight and other approved lab properties.
- Context: grade transitions, breaks, downtime, shift, maintenance and ambient conditions.

## 3. Historian data contract

Request a representative, continuous export covering stable production, grade changes, start-ups, shutdowns, breaks and known disturbances. The process owner must choose the period and confirm representativeness. Export native timestamps and quality flags; do not provide screenshots or manually transcribed charts as the calibration dataset.

Minimum columns: source_tag, source_timestamp, source_timezone, received/export_timestamp, raw_value, raw_unit, source_quality, historian_deadband/compression metadata (if available), source_system, batch/roll/order identifier (if available).

Document:
- historian platform/version and export method;
- configured scan and archive rates, deadband/compression and interpolation mode;
- daylight-saving/timezone handling and NTP/PTP clock sources;
- missing intervals, bad-quality codes, sensor replacement and calibration events;
- sampling/aggregation method used to align tags.

The provided `templates/historian-sample.csv` is a header template only, not plant data.

## 4. Laboratory and production context

Use `templates/lab-results.csv` for laboratory observations. Each result must link to an unambiguous sample, reel/roll, batch or order and include sample collection time, analysis time, method, unit, result, lab status and analyst/instrument reference where permitted.

Also provide grade master and production context: target and measured grammage, web width, furnish recipe/version, machine speed, good-product mass, reel boundaries, downtime/break events, reject/s broke mass and grade transition times. Never join a lab result to a process timestamp solely by nearest clock time when roll/sample identity is available.

## 5. OEM envelope and safety constraints

Complete `templates/oem-envelope.csv` from current OEM documentation and plant engineering approval. Record asset/tag, parameter, lower/upper bounds, unit, operating mode/grade applicability, source document and revision, page/section, approval authority, approval date and review date.

No default or demo range in the software is an OEM limit. Missing, conflicting or expired constraints block optimization for the affected variable. Keep hard safety/process constraints outside objective penalties. The optimizer may only enumerate approved advisory scenarios and must not write setpoints.

## 6. Time alignment and DVR acceptance

For each source, define timezone, clock source, timestamp semantics, expected cadence, allowed lateness and maximum age with the instrument/process owner. Establish a common analysis grid only after checking source cadence and process dynamics.

DVR output must retain:
- raw record and provenance;
- normalized value/unit and conversion version;
- quality classification and reason codes;
- duplicate, missing, stale, future-skew and out-of-range evidence;
- reconciliation residuals and uncertainty where calculable;
- rule-set version and validation time.

Never silently overwrite raw data. Do not promote suspect/invalid/stale critical tags to the active snapshot. Any imputation for offline analysis must be explicitly labelled and excluded from primary acceptance metrics unless separately approved.

## 7. Mass and energy balance definitions

Define a consistent control volume and time window with process engineering. Use measured quantities and uncertainty; do not calculate a plant-grade balance from proxies.

Dry-solids balance (illustrative structure):
- dry solids in = stock/slurry mass flow × measured consistency (with consistent basis);
- dry solids out = good-product mass flow × dry-solids fraction, plus separately measured broke/reject streams;
- balance residual = measured in − measured out − accumulation/known losses.

Water balance:
- water in stock and added streams;
- water removed in forming/press filtrate and other measured drains;
- water evaporated in dryer, derived from independently measured/validated streams or a reconciled balance;
- water retained in product based on product mass and moisture on a clearly specified wet/dry basis.

Thermal/energy balance:
- steam energy from calibrated mass flow and pressure/temperature-dependent enthalpy (document steam quality/condensate return assumptions);
- fuel/electricity inputs from calibrated meters;
- useful evaporation duty and exhaust/condensate losses only where measurable or supported by a validated model;
- normalize by good-product dry mass or another process-owner-approved denominator.

Report uncertainty propagation, meter calibration status, missing terms and residuals. Agree acceptable residual bands with the process owner before looking at model performance. No universal tolerance is assumed by this template.

## 8. Digital Twin calibration and validation protocol

1. Freeze a versioned dataset and data dictionary; document exclusions before fitting.
2. Split chronologically, not randomly: earlier period for fitting, later untouched period for validation. Keep complete rolls/batches and grade-transition windows together to prevent leakage.
3. Fit only physically interpretable parameters supported by measurements. Record parameter bounds, units, optimizer, objective, seed and software commit.
4. Compare baseline model and calibrated model against held-out measurements by grade and operating regime.
5. Report bias, MAE/RMSE, residual plots, prediction interval coverage, drift and mass/energy balance closure.
6. Perform sensitivity and out-of-domain checks. Flag unsupported operating regimes; do not extrapolate beyond validated domain.
7. Require process-engineering review and signed acceptance before enabling model outputs in the pilot dashboard.
8. Recalibration requires a new model version, dataset lineage, review and rollback path.

Suggested minimum reporting: dataset dates and row counts, tag coverage, missingness, quality distribution, grade mix, train/validation split, model version, per-target metrics, uncertainty, OOD rate and unresolved limitations. Numeric pass thresholds must be agreed before model fitting; do not choose thresholds after seeing results.

## 9. Advisory optimization acceptance

Objectives may include specific steam/energy per good tonne, final moisture deviation/profile variability, production rate and quality loss. Define denominator, moisture basis, grade normalization and metering boundary before comparison.

Hard constraints must include only plant/OEM-approved envelopes and process/quality constraints. Add uncertainty margins and prohibit recommendations when inputs are stale, critical quality is bad, model is OOD, balance residual exceeds the approved band, or a relevant constraint is missing.

The output is a ranked what-if recommendation with predicted outcomes, confidence/uncertainty, active constraints, model/data versions and explanation. Operator acknowledgement is audit-only. No recommendation may be automatically applied.

## 10. Pilot evaluation and energy hypothesis

Pre-register baseline and evaluation periods, product/grade strata, exclusion rules, normalization method and statistical analysis. Compare like-for-like production and adjust for grade, grammage, width, speed, furnish, ambient conditions, downtime and quality/rejects where relevant.

Primary outcome proposal: calibrated energy or steam per tonne of good product, with uncertainty and meter boundary stated. Guardrails: moisture/spec compliance, basis weight, quality, production rate, breaks, rejects, equipment condition and safety events.

A 10–20% reduction is an unverified hypothesis only. Report measured effect with confidence interval and confounders; do not claim savings from simulation or non-comparable periods. No live setpoint experiment is part of this read-only phase.

## 11. Deliverables and stage gates

| Gate | Evidence | Exit decision |
|---|---|---|
| G0 — access approval | signed OT/IT/HSE and process approvals | permitted read-only path |
| G1 — data dictionary | approved tag register, units, timestamps, OEM source refs | mapping frozen |
| G2 — data qualification | historian and lab exports, DVR report, calibration evidence | dataset fit for analysis |
| G3 — balance closure | agreed control volumes, measured inputs/outputs, uncertainty | balance accepted or gaps documented |
| G4 — Twin validation | versioned fit/holdout results and engineering review | model accepted within stated domain |
| G5 — Advisory pilot | approved constraints, audit, operator training and rollback | read-only pilot authorization |

## 12. Inputs required from Harir Khuzestan

The factory must provide the actual tag list and historian export, laboratory records linked to rolls/batches, product/grade context, instrument calibration and meter details, OEM documentation and approved operating envelopes, OT network/gateway requirements, and named technical approvers. Until these inputs are received, plant adapter commissioning, balance closure and real-data Twin calibration remain blocked.
