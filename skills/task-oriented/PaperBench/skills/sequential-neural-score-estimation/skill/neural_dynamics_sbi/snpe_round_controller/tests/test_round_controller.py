import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "posterior_estimator", "scripts"))
from posterior_estimator import infer_posterior
from round_controller import run_rounds


def simulate_summary(theta, rng):
    return [2.0 * theta[0] + rng.gauss(0.0, 0.01)]


def test_two_rounds_narrow_proposal():
    result = run_rounds([[-2.0, 2.0]], [1.0], simulate_summary, infer_posterior, rounds=2, simulations_per_round=8, seed=2)
    assert len(result["round_logs"]) == 2
    assert result["mechanism_flags"]["posterior_guided_round_executed"] is True
    assert result["mechanism_flags"]["proposal_narrowed"] is True
    assert len(result["parameters"]) == 16
