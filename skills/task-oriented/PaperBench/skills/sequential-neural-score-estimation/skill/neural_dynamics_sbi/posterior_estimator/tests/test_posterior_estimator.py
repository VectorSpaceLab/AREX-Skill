import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from posterior_estimator import infer_posterior


def distance(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right)) ** 0.5


def test_infer_posterior_moves_toward_known_parameter():
    summaries = [[-2.0], [-1.0], [0.0], [1.0], [2.0]]
    parameters = [[-1.0], [-0.5], [0.0], [0.5], [1.0]]
    result = infer_posterior(summaries, parameters, [1.5], sample_count=4, seed=1)
    prior_mean = [sum(row[0] for row in parameters) / len(parameters)]
    assert distance(result["posterior_mean"], [0.75]) < distance(prior_mean, [0.75])
    assert result["diagnostics"]["likelihood_evaluated"] is False
    assert len(result["posterior_samples"]) == 4
