"""FastAPI entry point. Read-only by design; no PLC/DCS command interface."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import audit_record, calculate_kpis, make_simulated_sample, validate_sample
from .dvr import build_tag_readings, reconcile_sample, validate_tag_readings
from .process_model import optimize_multiobjective, simulate_tissue_process
from .storage import SQLiteStore


app = FastAPI(
    title="HarirSmart AI",
    version="0.2.0",
    description="Read-only tissue-line monitoring, digital-twin scenarios, and advisory MVP. No PLC/DCS command interface.",
)
STORE = SQLiteStore()
AUDIT: list[dict] = []
LATEST_SAMPLE: dict | None = None
LATEST_SAMPLE_ID: str | None = None
LATEST_PROPOSAL: dict | None = None


class ProcessSample(BaseModel):
    timestamp: str
    moisture_in_pct: float
    moisture_out_pct: float
    press_load_pct: float
    dryer_temp_c: float
    steam_flow_tph: float
    machine_speed_m_min: float
    basis_weight_g_m2: float
    source: str = "api"


class Decision(BaseModel):
    decision: str = Field(pattern="^(accepted|rejected|deferred)$")
    reason: str = Field(default="", max_length=500)
    actor: str = Field(default="operator", max_length=80)


class TagReading(BaseModel):
    tag_id: str
    value: float | None
    unit: str
    timestamp: str
    source: str = "api"
    quality: str = "GOOD"


class TagBatch(BaseModel):
    readings: list[TagReading]


class ScenarioRequest(BaseModel):
    press_load_delta_pct: float = Field(default=0.0, ge=-2.0, le=2.0)
    dryer_temp_delta_c: float = Field(default=0.0, ge=-1.0, le=1.0)


def _record_audit(action: str, actor: str, object_id: str, details: dict) -> dict:
    event = audit_record(action, actor, object_id, details)
    event["event_id"] = str(uuid4())
    AUDIT.append(event)
    STORE.append_audit(event)
    return event


def _save_sample(sample: dict, sample_id: str | None = None) -> dict:
    global LATEST_SAMPLE, LATEST_SAMPLE_ID
    quality = validate_sample(sample)
    dvr = validate_tag_readings(build_tag_readings(sample))
    record = {
        "sample_id": sample_id or str(uuid4()),
        "sample": sample,
        "quality": quality,
        "dvr": dvr,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    STORE.save_sample(record)
    _record_audit(
        "sample_ingested",
        "system",
        record["sample_id"],
        {"quality_flag": quality["quality_flag"], "dvr_quality_flag": dvr["quality_flag"]},
    )
    if quality["is_valid"] and dvr["recommendation_allowed"]:
        LATEST_SAMPLE = sample
        LATEST_SAMPLE_ID = record["sample_id"]
    return record


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "version": "0.2.0",
        "mode": "READ_ONLY_ADVISORY",
        "plc_write_enabled": False,
        "storage": "sqlite",
        "storage_counts": STORE.counts(),
    }


@app.get("/api/v1/simulator/sample")
def simulator_sample():
    sample = make_simulated_sample()
    sample["source"] = "simulator"
    _save_sample(sample)
    return sample


@app.post("/api/v1/samples")
def ingest_sample(sample: ProcessSample):
    return _save_sample(sample.model_dump())


@app.get("/api/v1/history")
def history(limit: int = Query(default=50, ge=1, le=500)):
    return {"items": STORE.list_samples(limit), "count": STORE.counts()["samples"]}


@app.post("/api/v1/dvr/validate")
def validate_tag_batch(batch: TagBatch):
    readings = [reading.model_dump() for reading in batch.readings]
    result = validate_tag_readings(readings)
    return {
        "dvr": result,
        "reconciliation": reconcile_sample(result["normalized_values"]),
    }


@app.get("/api/v1/dashboard")
def dashboard():
    if LATEST_SAMPLE is None:
        return {"message": "No valid sample yet. Call /api/v1/simulator/sample first.", "sample": None}
    quality = validate_sample(LATEST_SAMPLE)
    dvr = validate_tag_readings(build_tag_readings(LATEST_SAMPLE))
    kpis = calculate_kpis(LATEST_SAMPLE) if quality["is_valid"] else {}
    return {
        "sample": LATEST_SAMPLE,
        "quality": quality,
        "dvr": dvr,
        "reconciliation": reconcile_sample(LATEST_SAMPLE),
        "kpis": kpis,
        "mode": "READ_ONLY_ADVISORY",
    }


@app.post("/api/v1/twin/simulate")
def twin_simulate(scenario: ScenarioRequest):
    if LATEST_SAMPLE is None:
        raise HTTPException(status_code=409, detail="No valid process sample available")
    try:
        return simulate_tissue_process(
            LATEST_SAMPLE,
            scenario.press_load_delta_pct,
            scenario.dryer_temp_delta_c,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/optimize")
def optimize():
    global LATEST_PROPOSAL
    if LATEST_SAMPLE is None:
        raise HTTPException(status_code=409, detail="No valid process sample available")
    quality = validate_sample(LATEST_SAMPLE)
    dvr = validate_tag_readings(build_tag_readings(LATEST_SAMPLE))
    if not quality["is_valid"] or not dvr["recommendation_allowed"]:
        raise HTTPException(
            status_code=422,
            detail={"message": "No recommendation: data quality gate is not GOOD", "issues": quality["issues"] + dvr["issues"]},
        )
    try:
        LATEST_PROPOSAL = optimize_multiobjective(LATEST_SAMPLE)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    LATEST_PROPOSAL["proposal_id"] = str(uuid4())
    LATEST_PROPOSAL["sample_id"] = LATEST_SAMPLE_ID
    LATEST_PROPOSAL["created_at"] = datetime.now(timezone.utc).isoformat()
    STORE.save_proposal(LATEST_PROPOSAL, LATEST_SAMPLE_ID)
    _record_audit(
        "advisory_generated",
        "optimizer",
        LATEST_PROPOSAL["proposal_id"],
        {"status": "PROPOSAL", "model_validity": LATEST_PROPOSAL["model_validity"]},
    )
    return LATEST_PROPOSAL


@app.post("/api/v1/proposals/{proposal_id}/decision")
def record_decision(proposal_id: str, decision: Decision):
    if not LATEST_PROPOSAL or LATEST_PROPOSAL.get("proposal_id") != proposal_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    item = _record_audit("operator_decision", decision.actor, proposal_id, decision.model_dump())
    return {"recorded": True, "audit_event": item, "execution": "No process command was sent."}


@app.get("/api/v1/audit")
def audit(limit: int = Query(default=200, ge=1, le=1000)):
    return {"items": STORE.list_audit(limit), "count": STORE.counts()["audit_events"]}


@app.get("/", response_class=HTMLResponse)
def home():
    from pathlib import Path
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory="app/static"), name="static")
