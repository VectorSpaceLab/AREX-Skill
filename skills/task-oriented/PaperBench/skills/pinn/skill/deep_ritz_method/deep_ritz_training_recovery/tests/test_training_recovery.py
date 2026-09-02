import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "run_deep_ritz_recovery.py"
spec = importlib.util.spec_from_file_location("run_deep_ritz_recovery", script)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_scalar_fallback_changes_parameters():
    class Args:
        dimension = 10
        steps = 3
        interior_count = 8
        validation_count = 8
        learning_rate = 0.01
        seed = 5
    trace = runner.run_scalar_fallback(Args())
    assert trace["optimizer_step_count"] == 3
    assert trace["parameter_changed"]
    assert "params_before" in trace
    assert "params_after" in trace
    assert trace["final_relative_l2_error"] >= 0.0
    assert trace["loss_before"] >= trace["loss_after"] or trace["parameter_changed"]


if __name__ == "__main__":
    test_scalar_fallback_changes_parameters()
