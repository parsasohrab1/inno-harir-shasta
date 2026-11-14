"""Provenance-aware public reference data catalog (not plant telemetry)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "public_sources.json"
MANIFEST = ROOT / "data" / "external" / "manifest.json"
RAW = ROOT / "data" / "external" / "raw"


def get_reference_data_catalog() -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8")).get("files", {})
        except (OSError, json.JSONDecodeError):
            manifest = {}
    items = []
    for source in registry.get("sources", []):
        source_id = source["id"]
        record = manifest.get(source_id, {})
        filename = record.get("filename")
        local_path = RAW / filename if filename else None
        items.append({
            **source,
            "provenance_class": "external_reference",
            "download_status": record.get("status", "not_downloaded"),
            "local_file_present": bool(local_path and local_path.is_file()),
            "sha256": record.get("sha256"),
        })
    return {
        "catalog_version": registry.get("version"),
        "policy": registry.get("policy"),
        "items": items,
        "plant_data_included": False,
        "plc_write_enabled": False,
    }
