import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_posterior import validate_recovery, vector_correlation


def flags():
    return {
        "simulator_executed": True,
        "summary_conditioning_executed": True,
        "posterior_estimator_fit": True,
        "posterior_samples_generated": True,
        "likelihood_evaluated_false": True,
        "original_repo_not_used": True,
    }


def test_vector_correlation_identical_and_opposite():
    assert abs(vector_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-9
    assert vector_correlation([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) < -0.99


def test_validate_recovery_requires_mechanism_flags():
    bad_flags = flags()
    bad_flags["posterior_estimator_fit"] = False
    result = validate_recovery([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, 0.2], [[0.1, 0.2]], bad_flags)
    assert result["accepted"] is False
    assert "posterior_estimator_fit" in result["missing_mechanism_flags"]


def test_validate_recovery_accepts_good_proxy():
    result = validate_recovery([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, 0.2], [[0.11, 0.19]], flags())
    assert result["accepted"] is True
