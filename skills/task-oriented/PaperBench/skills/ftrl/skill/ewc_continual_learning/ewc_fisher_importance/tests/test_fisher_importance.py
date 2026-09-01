from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fisher_importance import diagonal_fisher, fisher_overlap, trace_normalize


def test_diagonal_fisher_averages_squared_gradients():
    fisher = diagonal_fisher([[1.0, -2.0], [3.0, 4.0]])
    assert fisher == [5.0, 10.0]


def test_trace_normalize_and_overlap():
    assert trace_normalize([2.0, 2.0]) == [0.5, 0.5]
    assert trace_normalize([0.0, 0.0]) == [0.0, 0.0]
    assert fisher_overlap([3.0, 1.0], [1.0, 3.0]) == 0.5


def test_dimension_mismatch_fails():
    try:
        diagonal_fisher([[1.0], [1.0, 2.0]])
    except ValueError as exc:
        assert "same dimension" in str(exc)
    else:
        raise AssertionError("expected dimension mismatch failure")
