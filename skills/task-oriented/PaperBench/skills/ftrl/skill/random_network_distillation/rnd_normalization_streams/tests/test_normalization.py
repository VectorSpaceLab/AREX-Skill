import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "normalization.py"
spec = importlib.util.spec_from_file_location("normalization", script)
normalization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalization)


def test_observation_normalization_clips_and_reward_scaling():
    observations = [[0.0, 10.0], [2.0, 14.0], [100.0, -100.0]]
    stats = normalization.running_stats(observations[:2])
    normalized = normalization.normalize_observations(observations, stats, clip=5.0)
    assert stats["count"] == 2
    assert normalized[0][0] < 0 and normalized[1][0] > 0
    assert normalized[2][0] == 5.0
    scaled = normalization.scale_rewards([2.0, -2.0], 2.0)
    assert abs(scaled[0] - 1.0) < 1e-6
    assert abs(scaled[1] + 1.0) < 1e-6
