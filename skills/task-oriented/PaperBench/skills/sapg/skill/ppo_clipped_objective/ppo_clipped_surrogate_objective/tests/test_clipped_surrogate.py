import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compute_clipped_surrogate import compute_clipped_surrogate


def test_positive_advantage_caps_improvement():
    result = compute_clipped_surrogate([0.0], [math.log(1.5)], [2.0], 0.2)
    assert abs(result["objective_terms"][0] - 2.4) < 1e-9
    assert result["unclipped"][0] > result["objective_terms"][0]
    assert result["clip_fraction"] == 1.0


def test_negative_advantage_caps_low_ratio_improvement():
    result = compute_clipped_surrogate([0.0], [math.log(0.5)], [-3.0], 0.2)
    assert abs(result["objective_terms"][0] - (-2.4)) < 1e-9
    assert result["unclipped"][0] > result["objective_terms"][0]


def test_inside_clip_matches_unclipped():
    result = compute_clipped_surrogate([0.0, 0.0], [math.log(1.1), math.log(0.95)], [1.0, -1.0], 0.2)
    for raw, term in zip(result["unclipped"], result["objective_terms"]):
        assert abs(raw - term) < 1e-9
    assert math.isfinite(result["loss"])


if __name__ == "__main__":
    test_positive_advantage_caps_improvement()
    test_negative_advantage_caps_low_ratio_improvement()
    test_inside_clip_matches_unclipped()
