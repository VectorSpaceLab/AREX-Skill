import os
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
for skill in ["pql_parallel_topology", "mixed_exploration_scheduler", "speed_ratio_replay_diagnostics"]:
    sys.path.insert(0, os.path.join(SKILL_ROOT, skill, "scripts"))

from reduced_pql import run_reduced_pql


def test_reduced_pql_runs_mechanism_and_changes_parameters():
    result = run_reduced_pql(actor_count=16, rollout_steps=4, replay_capacity=128, updates=8, seed=3)
    checks = result["mechanism_checks"]
    assert checks["reduced_training_executed"] is True
    assert checks["optimizer_step_executed"] is True
    assert checks["parallel_actors_executed"] is True
    assert checks["mixed_exploration_executed"] is True
    assert result["training_trace"]["params_before"] != result["training_trace"]["params_after"]
    assert result["metrics"]["loss_reduction"] > 0.0
