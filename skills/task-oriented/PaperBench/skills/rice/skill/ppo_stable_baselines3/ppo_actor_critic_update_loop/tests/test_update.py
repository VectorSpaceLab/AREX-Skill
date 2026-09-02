import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ppo_rollout_advantage_protocol" / "scripts"))
sys.path.insert(0, str(ROOT / "ppo_clipped_surrogate_objective" / "scripts"))

from update_loop import run_reduced_update


def test_reduced_update_changes_parameters_and_runs_mechanisms():
    result = run_reduced_update({
        "steps": [
            {"reward": 1.0, "value": 0.2, "done": False},
            {"reward": 0.5, "value": 0.1, "done": True},
        ],
        "last_value": 0.0,
        "old_log_probs": [0.0, 0.0],
        "features": [1.0, -1.0],
        "policy_weight": 0.4,
        "value_bias": 0.0,
        "learning_rate": 0.01,
    })
    assert result["params_before"] != result["params_after"]
    assert result["mechanism_checks"]["gae_executed"] is True
    assert result["mechanism_checks"]["clipped_surrogate_executed"] is True
    assert result["mechanism_checks"]["optimizer_step_executed"] is True
    assert result["loss_before"] == result["loss_before"]
    assert result["loss_after"] == result["loss_after"]
