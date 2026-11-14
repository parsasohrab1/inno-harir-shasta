# HarirSmart AI — Public Data Acquisition and Integration

## Objective

Use public pulp-and-paper sources to strengthen process taxonomy, reference scenarios, energy/water accounting methods and model-development tests before the factory historian and laboratory data are released.

**Public reference data are not Harir Khuzestan operating data.** They must never be relabelled as plant measurements, used to infer current machine setpoints, or treated as OEM-approved limits.

## Sources selected

| Source | Content | Intended role | Important limitation |
|---|---|---|---|
| US EPA UISIS-PNP dataset | Historical US mill/product, capacity, cost, fuel, emissions and energy-efficiency model inputs; tissue is one product category | Sector context and scenario/economic model structure | Historical; not high-frequency machine telemetry or tissue-machine time series |
| US EPA UISIS-PNP example outputs | Illustrative mitigation/economic model outputs | Scenario-analysis examples | Model outputs, not observations |
| EU JRC Pulp, Paper and Board BREF (2015) | Process descriptions, BAT context, indicative environmental/energy information | Process taxonomy and engineering reference | Values depend on process boundaries, grade, furnish and configuration |
| SFI Global Pulp and Paper Mill Database (2025) | 3,403 global mill records and facility attributes | Facility/peer-group context | Download requires request form; not process telemetry |

The machine-readable registry is `data/public_sources.json`. Direct downloads are configured in `scripts/download_public_data.py`.

## Download

From the repository root, with Python 3.10+:

```bash
python scripts/download_public_data.py --all
```

Or select one source:

```bash
python scripts/download_public_data.py --source epa_uisis_pnp_dataset
python scripts/download_public_data.py --source jrc_pp_bref_2015
```

Downloaded binaries are stored under `data/external/raw/`; retrieval metadata and SHA-256 hashes are written to `data/external/manifest.json`. Raw binaries are excluded from Git to avoid repository bloat and preserve source licensing. Do not commit them unless redistribution terms have been reviewed.

## Data placement and semantic mapping

| Public source content | HarirSmart data domain | Permitted use |
|---|---|---|
| Mill/product/capacity/fuel/economic attributes | `external_reference` | Contextual benchmark; annual/sector-level only |
| BREF process sections and reference values | `engineering_reference` | Documented assumptions and review notes with page citations |
| Global mill facility attributes | `facility_reference` | Facility metadata and peer-group discovery |
| Factory historian tags | `plant_observation` | Blocked until supplied and approved by plant OT/data owner |
| Laboratory results and grade/roll links | `quality_observation` | Blocked until supplied and approved by laboratory owner |
| OEM operating envelope | `approved_equipment_constraint` | Blocked until authenticated OEM document and plant engineering approval |

A future ETL step must preserve source ID, source URL, retrieval date, license, source vintage, units, geography, process boundary, transformation history and confidence. Every observation must carry a provenance class. Public reference data must not be merged into historian time series as if they shared timestamps or equipment identity.

## Product development enabled now

1. **Reference-data catalog:** traceable inventory of public sources and limitations.
2. **Process taxonomy:** stock preparation, approach flow, forming/dewatering, pressing, drying, steam/condensate, broke/recycle and utilities.
3. **Benchmark context:** annual or product-level comparisons only where definitions and system boundaries match.
4. **Mass/energy balance framework:** define variables, equations, units and uncertainty; do not fill missing plant values with public averages.
5. **Model development:** offline feature engineering and scenario tests using explicitly labelled reference data.
6. **Validation gates:** no plant calibration or performance claim until time-aligned plant historian, laboratory, production and metering data are approved.

## Required factory inputs still outstanding

- Approved tag register: canonical tag, source path, engineering unit, scale, timestamp semantics/timezone, scan interval, quality code, calibration and owner.
- Historian export with at least 4–8 weeks spanning stable production, grade changes, breaks and planned/unplanned stops (subject to plant approval).
- Laboratory/quality results linked to reel/roll/batch/order and sample timestamps.
- Production context: grade, basis weight, trim width, speed, saleable tonnes, broke and downtime reason codes.
- Calibrated water, steam, fuel and electricity meter readings and documented meter boundaries.
- OEM manuals and approved operating envelopes, with document revision and page-level traceability.
- Written approval from OT cybersecurity, operations, process engineering and HSE for the read-only data gateway.

## Safety and claims

- The application remains Read-only / Advisory. No PLC/DCS write path is introduced.
- Public data cannot establish safe operating limits or authorize control actions.
- RL remains offline in a simulator with no live exploration.
- Energy or water savings are hypotheses until measured against a normalized, independently reviewed plant baseline.
- Any benchmark must state geography, year, grade, furnish, process boundary and units; incomparable figures must be rejected.

## Source notes

- EPA Data.gov catalog: [Production, emissions and economic data for US pulp and paper industries](https://catalog.data.gov/dataset/production-emissions-and-economic-as-well-as-historical-marketing-data-for-the-pulp-and-pa).
- EPA workbook download: [UISIS-PNP Model Dataset](https://pasteur.epa.gov/uploads/10.23719/1390779/UISIS-PNP%20Model%20Dataset.xlsx).
- JRC: [Pulp, Paper and Board BREF](https://bureau-industrial-transformation.jrc.ec.europa.eu/sites/default/files/2019-11/PP_revised_BREF_2015.pdf).
- SFI: [Global Pulp and Paper Mill Database](https://cgfi.ac.uk/spatial-finance-initiative/geoasset-project/pulp-and-paper-database/).
- Peer-reviewed process benchmarking: [Benchmarking energy use in the paper industry](https://link.springer.com/article/10.1007/s12053-012-9163-9).
