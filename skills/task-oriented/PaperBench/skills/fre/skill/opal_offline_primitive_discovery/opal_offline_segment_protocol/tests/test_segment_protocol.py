from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from segment_trajectories import segment_trajectories


def test_non_overlapping_segments_preserve_initial_state_and_rewards():
    trajectories = [{
        "id": "demo",
        "states": [0, 1, 2, 3, 4],
        "actions": [1, 1, -1, -1],
        "rewards": [0, 1, 0, 2],
    }]
    result = segment_trajectories(trajectories, 2)
    assert result["summary"]["segment_count"] == 2
    assert result["segments"][0]["initial_state"] == 0
    assert result["segments"][0]["actions"] == [1, 1]
    assert result["segments"][1]["reward_sum"] == 2


def test_invalid_horizon_fails():
    try:
        segment_trajectories([], 0)
    except ValueError as exc:
        assert "horizon" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_non_overlapping_segments_preserve_initial_state_and_rewards()
    test_invalid_horizon_fails()
