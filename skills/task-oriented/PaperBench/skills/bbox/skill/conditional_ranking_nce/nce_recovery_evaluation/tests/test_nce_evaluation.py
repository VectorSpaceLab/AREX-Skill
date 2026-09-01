import math

from nce_evaluation import evaluate_recovery, kl_divergence, params_changed, validate_target


def test_evaluate_recovery_mechanism_checks():
    target = {"dataset": "Section 4.3 finite conditional counterexample", "metric": "ranking_ratio_absolute_error", "paper_value": 0.0}
    ranking = {
        "ratio_x1": 0.334,
        "true_ratio_x1": 1.0 / 3.0,
        "loss_before": 1.0,
        "loss_after": 0.5,
        "params_before": {"log_theta1": 0.0, "log_theta2": 0.0},
        "params_after": {"log_theta1": -0.4, "log_theta2": 0.7},
        "candidate_posterior_sum": 1.0,
    }
    binary = {
        "analytic_limit": {"ratio_x1": 3.0 / 7.0},
        "self_normalization": {"constant_partition": False},
    }
    result = evaluate_recovery(target, ranking, binary)
    assert result["metrics"]["ranking_ratio_absolute_error"] < 0.01
    assert result["metrics"]["binary_inconsistency_gap"] > 0.09
    assert result["mechanism_checks"]["ranking_ratio_recovered"] is True
    assert result["mechanism_checks"]["optimizer_step_executed"] is True


def test_kl_and_param_change_helpers():
    true_dist = {"x": {"a": 0.5, "b": 0.5}}
    estimated = {"x": {"a": 0.5, "b": 0.5}}
    assert math.isclose(kl_divergence(true_dist, estimated), 0.0)
    assert params_changed({"a": 1.0}, {"a": 1.1}) is True


def test_target_validation_detects_drift():
    valid = validate_target(
        {"dataset": "Section 4.3 finite conditional counterexample", "metric": "ranking_ratio_absolute_error", "paper_value": 0.0},
        "Section 4.3 finite conditional counterexample",
        "ranking_ratio_absolute_error",
    )
    assert valid["ok"] is True
    invalid = validate_target(
        {"dataset": "other", "metric": "accuracy", "paper_value": 1.0},
        "Section 4.3 finite conditional counterexample",
        "ranking_ratio_absolute_error",
    )
    assert invalid["ok"] is False
    assert len(invalid["errors"]) == 3
