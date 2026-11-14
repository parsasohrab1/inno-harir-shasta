"""FastAPI entry point. Deliberately exposes no actuator/PLC write endpoint."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import audit_record, calculate_kpis, make_simulated_sample, optimize_advisory, validate_sample

app = FastAPI(
    title="HarirSmart AI",
    version="0.1.0",
    description="Read-only tissue-line monitoring and advisory MVP. No PLC/DCS command interface.",
)
AUDIT: list[dict] = []
LATEST_SAMPLE: dict | None = None
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


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "mode": "READ_ONLY_ADVISORY", "plc_write_enabled": False}


@app.get("/api/v1/simulator/sample")
def simulator_sample():
    global LATEST_SAMPLE
    LATEST_SAMPLE = make_simulated_sample()
    return LATEST_SAMPLE


@app.post("/api/v1/samples")
def ingest_sample(sample: ProcessSample):
    global LATEST_SAMPLE
    payload = sample.model_dump()
    quality = validate_sample(payload)
    record = {
        "sample_id": str(uuid4()),
        "sample": payload,
        "quality": quality,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    AUDIT.append(audit_record("sample_ingested", "system", record["sample_id"], {"quality_flag": quality["quality_flag"]}))
    if quality["is_valid"]:
        LATEST_SAMPLE = payload
    return record


@app.get("/api/v1/dashboard")
def dashboard():
    if LATEST_SAMPLE is None:
        return {"message": "No sample yet. Call /api/v1/simulator/sample first.", "sample": None}
    quality = validate_sample(LATEST_SAMPLE)
    kpis = calculate_kpis(LATEST_SAMPLE) if quality["is_valid"] else {}
    return {"sample": LATEST_SAMPLE, "quality": quality, "kpis": kpis}


@app.post("/api/v1/optimize")
def optimize():
    global LATEST_PROPOSAL
    if LATEST_SAMPLE is None:
        raise HTTPException(status_code=409, detail="No process sample available")
    quality = validate_sample(LATEST_SAMPLE)
    if not quality["is_valid"]:
        raise HTTPException(status_code=422, detail={"message": "No recommendation: input quality is not GOOD", "issues": quality["issues"]})
    LATEST_PROPOSAL = optimize_advisory(LATEST_SAMPLE)
    LATEST_PROPOSAL["proposal_id"] = str(uuid4())
    AUDIT.append(audit_record("advisory_generated", "optimizer", LATEST_PROPOSAL["proposal_id"], {"status": "PROPOSAL"}))
    return LATEST_PROPOSAL


@app.post("/api/v1/proposals/{proposal_id}/decision")
def record_decision(proposal_id: str, decision: Decision):
    if not LATEST_PROPOSAL or LATEST_PROPOSAL.get("proposal_id") != proposal_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    item = audit_record("operator_decision", decision.actor, proposal_id, decision.model_dump())
    AUDIT.append(item)
    return {"recorded": True, "audit_event": item, "execution": "No process command was sent."}


@app.get("/api/v1/audit")
def audit():
    return {"items": AUDIT[-200:], "count": len(AUDIT)}


@app.get("/", response_class=HTMLResponse)
def home():
    from pathlib import Path
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory="app/static"), name="static")
