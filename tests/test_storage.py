from datetime import datetime, timezone

from app.storage import SQLiteStore


def test_samples_proposals_and_audit_survive_store_recreation(tmp_path):
    path = tmp_path / "harir-test.db"
    first = SQLiteStore(path)
    sample = {
        "sample_id": "sample-1",
        "sample": {"timestamp": datetime.now(timezone.utc).isoformat(), "source": "simulator"},
        "quality": {"is_valid": True},
        "dvr": {"quality_flag": "GOOD"},
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    first.save_sample(sample)
    first.save_proposal(
        {"proposal_id": "proposal-1", "created_at": datetime.now(timezone.utc).isoformat()},
        "sample-1",
    )
    first.append_audit(
        {
            "event_id": "event-1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "test",
            "action": "sample_ingested",
            "object_id": "sample-1",
            "details": {},
        }
    )

    second = SQLiteStore(path)
    assert second.list_samples(10)[0]["sample_id"] == "sample-1"
    assert second.list_audit(10)[0]["event_id"] == "event-1"
    assert second.counts() == {"samples": 1, "proposals": 1, "audit_events": 1}
