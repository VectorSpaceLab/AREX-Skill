import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_minibatch_ppo import run_reduced_ppo


def test_reduced_ppo_changes_parameters_and_reward():
    result = run_reduced_ppo(epochs=4)
    assert result["optimizer_step_executed"] is True
    assert result["old_log_probs_frozen"] is True
    assert result["params_before"] != result["params_after"]
    assert result["expected_reward_after"] > result["expected_reward_before"]


def test_trace_contains_diagnostics():
    result = run_reduced_ppo(epochs=3)
    assert len(result["trace"]) == 3
    assert math.isfinite(result["loss_after"])
    assert "clip_fraction" in result["final_diagnostics"]
    assert "approx_kl" in result["final_diagnostics"]


if __name__ == "__main__":
    test_reduced_ppo_changes_parameters_and_reward()
    test_trace_contains_diagnostics()
