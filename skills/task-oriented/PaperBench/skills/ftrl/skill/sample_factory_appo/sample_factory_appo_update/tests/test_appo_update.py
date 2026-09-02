import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "appo_update.py"
spec = importlib.util.spec_from_file_location("appo_update", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_vtrace_targets_have_expected_length_and_weights():
    result = module.vtrace_targets([1.0, 0.0], [0.9, 0.0], [0.2, 0.1], 0.0, [-0.7, -0.8], [-0.6, -0.9])
    assert len(result["value_targets"]) == 2
    assert len(result["ratios"]) == 2
    assert all(rho <= 1.0 for rho in result["rhos"])


def test_ppo_clipping_bounds_ratios():
    result = module.ppo_policy_loss([1.0, -0.5], [-2.0, -0.1], [0.0, -2.0], clip=0.2)
    assert all(0.8 <= ratio <= 1.2 for ratio in result["clipped_ratios"])
    assert isinstance(result["policy_loss"], float)


def test_scalar_optimizer_changes_parameter_and_loss():
    trace = module.scalar_optimizer_step(0.0, 1.0, 1, 1.0, learning_rate=0.5)
    assert trace["optimizer_step_executed"] is True
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] < trace["loss_before"]


def test_length_mismatch_fails():
    try:
        module.value_loss([1.0], [1.0, 2.0])
    except ValueError as exc:
        assert "matching" in str(exc)
    else:
        raise AssertionError("expected mismatched lengths to fail")
