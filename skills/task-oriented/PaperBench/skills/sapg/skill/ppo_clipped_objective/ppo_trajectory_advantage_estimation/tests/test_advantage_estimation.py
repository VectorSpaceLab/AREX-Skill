import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from estimate_advantages import estimate_advantages


def test_reverse_time_gae_with_terminal_mask():
    result = estimate_advantages([1.0, 1.0], [0.5, 0.25], [False, True], 0.0, 0.99, 0.95)
    expected_second = 1.0 - 0.25
    expected_first = 1.0 + 0.99 * 0.25 - 0.5 + 0.99 * 0.95 * expected_second
    assert abs(result["advantages"][1] - expected_second) < 1e-9
    assert abs(result["advantages"][0] - expected_first) < 1e-9
    assert abs(result["returns"][1] - 1.0) < 1e-9


def test_constant_advantages_normalize_safely():
    result = estimate_advantages([1.0, 1.0], [0.0, 0.0], [True, True], 0.0, 0.99, 0.95)
    assert result["advantages"] == [1.0, 1.0]
    assert result["normalized_advantages"] == [0.0, 0.0]


if __name__ == "__main__":
    test_reverse_time_gae_with_terminal_mask()
    test_constant_advantages_normalize_safely()
