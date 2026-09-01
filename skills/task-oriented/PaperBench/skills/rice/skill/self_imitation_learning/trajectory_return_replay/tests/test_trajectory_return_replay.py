import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "trajectory_replay.py"
spec = importlib.util.spec_from_file_location("trajectory_replay", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_sparse_reward_returns_and_capacity():
    steps = [
        {"state": "s0", "action": 0, "reward": 0.0},
        {"state": "s1", "action": 1, "reward": 0.0},
        {"state": "s2", "action": 1, "reward": 1.0, "done": True},
    ]
    records = mod.build_replay_records(steps, gamma=0.9)
    assert [round(item["return"], 3) for item in records] == [0.81, 0.9, 1.0]
    assert records[1]["action"] == 1
    truncated = mod.build_replay_records(steps, gamma=0.9, capacity=2)
    assert [item["state"] for item in truncated] == ["s1", "s2"]


if __name__ == "__main__":
    test_sparse_reward_returns_and_capacity()
