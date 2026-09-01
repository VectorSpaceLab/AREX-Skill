from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ewc_penalty import ewc_gradient, ewc_penalty, summed_penalty


def test_penalty_and_gradient_match_paper_equation():
    theta = [2.0, -1.0]
    theta_star = [1.0, 1.0]
    fisher = [3.0, 0.5]
    assert ewc_penalty(theta, theta_star, fisher, 4.0) == 10.0
    assert ewc_gradient(theta, theta_star, fisher, 4.0) == [12.0, -4.0]


def test_summed_penalty_equals_individual_sum():
    theta = [2.0]
    anchors = [
        {"theta_star": [1.0], "fisher": [2.0], "lambda_value": 3.0},
        {"theta_star": [0.0], "fisher": [1.0], "lambda_value": 1.0},
    ]
    expected = ewc_penalty(theta, [1.0], [2.0], 3.0) + ewc_penalty(theta, [0.0], [1.0], 1.0)
    assert summed_penalty(theta, anchors) == expected


def test_negative_fisher_fails():
    try:
        ewc_penalty([1.0], [0.0], [-1.0], 1.0)
    except ValueError as exc:
        assert "nonnegative" in str(exc)
    else:
        raise AssertionError("expected negative fisher failure")


def test_dimension_mismatch_fails():
    try:
        ewc_gradient([1.0, 2.0], [1.0], [1.0], 1.0)
    except ValueError as exc:
        assert "identical dimensions" in str(exc)
    else:
        raise AssertionError("expected dimension mismatch failure")
