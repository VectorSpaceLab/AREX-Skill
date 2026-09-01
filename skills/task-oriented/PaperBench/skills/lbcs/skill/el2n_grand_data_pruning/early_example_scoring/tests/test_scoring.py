import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from score_examples import average_el2n, compute_el2n, compute_grand


def approx_equal(left, right, tol=1e-9):
    assert abs(left - right) <= tol, (left, right)


def test_el2n_known_values():
    scores = compute_el2n([[0.8, 0.2], [0.45, 0.55]], [0, 0])
    approx_equal(scores[0], math.sqrt(0.2 ** 2 + 0.2 ** 2))
    approx_equal(scores[1], math.sqrt(0.55 ** 2 + 0.55 ** 2))
    assert scores[1] > scores[0]


def test_average_el2n_two_runs():
    scores = average_el2n([
        [[0.8, 0.2], [0.45, 0.55]],
        [[0.7, 0.3], [0.5, 0.5]],
    ], [0, 0])
    assert len(scores) == 2
    assert scores[1] > scores[0]


def test_grand_norms():
    assert compute_grand([[3, 4], [1, 2, 2]]) == [5.0, 3.0]


def test_reject_invalid_label():
    try:
        compute_el2n([[0.5, 0.5]], [2])
    except ValueError as exc:
        assert "out of range" in str(exc)
    else:
        raise AssertionError("invalid label was accepted")


if __name__ == "__main__":
    test_el2n_known_values()
    test_average_el2n_two_runs()
    test_grand_norms()
    test_reject_invalid_label()
    print("ok")
