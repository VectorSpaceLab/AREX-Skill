import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "topology_contract.py"
spec = importlib.util.spec_from_file_location("topology_contract", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_policy_lag_estimate_and_queues():
    result = module.build_topology(2, 1, 1, 4, 8, 32)
    assert result["produced_samples_per_iteration"] == 64
    assert result["policy_lag_pressure"] == 1.0
    assert len(result["queue_contracts"]) == 4
    assert result["contract_ok"] is True


def test_forbidden_responsibility_detection():
    check = module.check_responsibilities("rollout_worker", ["step_environment", "compute_gradients"])
    assert check["ok"] is False
    assert "compute_gradients" in check["forbidden"]


def test_invalid_counts_fail():
    try:
        module.build_topology(0, 1, 1, 4, 8, 32)
    except ValueError as exc:
        assert "rollout_workers" in str(exc)
    else:
        raise AssertionError("expected invalid rollout worker count to fail")
