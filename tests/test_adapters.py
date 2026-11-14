from app.adapters.simulator import SimulatorAdapter


def test_simulator_adapter_implements_read_only_snapshot_contract():
    adapter = SimulatorAdapter()
    snapshot = adapter.read_snapshot()
    assert snapshot.sample["source"] == "simulator"
    assert len(snapshot.readings) == 7
    assert callable(adapter.read_snapshot)
    assert not hasattr(adapter, "write")
    assert not hasattr(adapter, "write_tag")
