#!/usr/bin/env python3
"""Download public HarirSmart reference files.

Files are written to data/external/raw and are intentionally not committed.
The script records URL, retrieval time, byte size and SHA-256 in manifest.json.
It never downloads plant telemetry, credentials, or vendor/OEM operating limits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "raw"
MANIFEST = ROOT / "data" / "external" / "manifest.json"

SOURCES = {
    "epa_uisis_pnp_dataset": {
        "filename": "epa_uisis_pnp_model_dataset.xlsx",
        "url": "https://pasteur.epa.gov/uploads/10.23719/1390779/UISIS-PNP%20Model%20Dataset.xlsx",
    },
    "epa_uisis_pnp_outputs": {
        "filename": "epa_uisis_pnp_model_outputs_example.xlsx",
        "url": "https://pasteur.epa.gov/uploads/10.23719/1390779/UISIS-PNP%20Model%20Outputs%20Example.xlsx",
    },
    "jrc_pp_bref_2015": {
        "filename": "jrc_pulp_paper_board_bref_2015.pdf",
        "url": "https://bureau-industrial-transformation.jrc.ec.europa.eu/sites/default/files/2019-11/PP_revised_BREF_2015.pdf",
    },
}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def download(source_id: str, timeout: int = 90) -> dict:
    item = SOURCES[source_id]
    RAW.mkdir(parents=True, exist_ok=True)
    destination = RAW / item["filename"]
    request = urllib.request.Request(
        item["url"],
        headers={"User-Agent": "HarirSmartAI-public-data-loader/1.0"},
    )
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as out:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"HTTP status {status}")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        if temporary.stat().st_size == 0:
            raise RuntimeError("Downloaded file is empty")
        # Basic file signature checks prevent HTML error pages being stored as data.
        with temporary.open("rb") as stream:
            signature = stream.read(8)
        if destination.suffix == ".xlsx" and not signature.startswith(b"PK"):
            raise RuntimeError("Expected XLSX/ZIP signature; server may have returned an error page")
        if destination.suffix == ".pdf" and not signature.startswith(b"%PDF"):
            raise RuntimeError("Expected PDF signature; server may have returned an error page")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "id": source_id,
        "filename": destination.name,
        "url": item["url"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "status": "downloaded",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES) + ["all"], default="all")
    args = parser.parse_args()
    selected = list(SOURCES) if args.source == "all" else [args.source]
    existing = {}
    if MANIFEST.exists():
        try:
            existing = json.loads(MANIFEST.read_text(encoding="utf-8")).get("files", {})
        except (json.JSONDecodeError, OSError):
            existing = {}
    for source_id in selected:
        try:
            record = download(source_id)
            existing[source_id] = record
            print(f"OK {source_id}: {record['filename']} ({record['bytes']} bytes)")
        except Exception as exc:
            existing[source_id] = {
                "id": source_id,
                "url": SOURCES[source_id]["url"],
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(exc),
            }
            print(f"FAILED {source_id}: {exc}")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": existing,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(existing[s]["status"] == "downloaded" for s in selected) else 1

if __name__ == "__main__":
    raise SystemExit(main())
