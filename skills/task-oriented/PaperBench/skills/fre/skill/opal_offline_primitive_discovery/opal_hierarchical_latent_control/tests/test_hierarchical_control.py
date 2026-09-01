from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hierarchical_control import evaluate_hierarchical_control


def test_latent_controller_reaches_sparse_goal_with_reduced_horizon():
    segments = {"segments": [
        {"actions": [-1, -1, -1], "initial_state": -1, "horizon": 3},
        {"actions": [1, 1, 1], "initial_state": 1, "horizon": 3},
    ]}
    objective = {"assignments": [0, 1], "params_after": {"0": -1.0, "1": 1.0}}
    result = evaluate_hierarchical_control(segments, objective, goal=6.0)
    rollout = result["rollout"]
    assert rollout["success"] is True
    assert rollout["latent_decision_count"] < rollout["primitive_action_count"]
    assert result["latent_dataset"][1]["latent"] == 1


if __name__ == "__main__":
    test_latent_controller_reaches_sparse_goal_with_reduced_horizon()
