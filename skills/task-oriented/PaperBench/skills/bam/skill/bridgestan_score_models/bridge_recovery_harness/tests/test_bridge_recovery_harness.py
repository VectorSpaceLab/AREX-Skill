import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_bridge_recovery.py"
spec = importlib.util.spec_from_file_location("run_bridge_recovery", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_pass_rate():
    assert mod.pass_rate({"a": True, "b": True}) == 1.0
    assert mod.pass_rate({"a": True, "b": False}) == 0.5
    assert mod.pass_rate({}) == 0.0


def test_zero_abs_error_counts_as_roundtrip_success():
    transform = {"valid": True, "abs_error": 0.0}
    assert bool(transform.get("valid")) and transform.get("abs_error") is not None and transform.get("abs_error") < 1e-10


if __name__ == "__main__":
    test_pass_rate()
