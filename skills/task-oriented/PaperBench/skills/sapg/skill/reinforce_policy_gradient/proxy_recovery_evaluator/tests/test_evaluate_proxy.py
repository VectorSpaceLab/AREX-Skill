from evaluate_proxy import evaluate_proxy


def base_plan():
    return {"fast_recovery_target": {"dataset": "seeded_two_action_bandit", "split": "deterministic_proxy_128_episodes", "metric": "expected_reward_after_training", "paper_value": 0.7, "proxy": True}}


def base_invocations():
    return {"invocations": [{"module": "score_function_estimator"}, {"module": "reinforce_training_loop"}, {"module": "proxy_recovery_evaluator"}]}


def passing_recovery():
    return {
        "is_proxy": True,
        "metrics": {"expected_reward_after_training": 0.82},
        "paper_target": base_plan()["fast_recovery_target"],
        "mechanism_checks": {
            "stochastic_actions_sampled": True,
            "score_function_update_computed": True,
            "baseline_used": True,
            "reduced_training_executed": True,
            "optimizer_step_executed": True,
            "expected_reward_improved": True,
        },
    }


def test_accepts_mechanism_faithful_proxy():
    trace = {"params_before": {"theta": 0.0}, "params_after": {"theta": 1.0}, "mechanism_checks": {}}
    result = evaluate_proxy(base_plan(), passing_recovery(), trace, base_invocations())
    assert result["accepted"] is True
    assert result["metric_gap"] > 0


def test_rejects_high_metric_without_optimizer_evidence():
    recovery = passing_recovery()
    recovery["mechanism_checks"]["optimizer_step_executed"] = False
    trace = {"params_before": {"theta": 0.0}, "params_after": {"theta": 0.0}, "mechanism_checks": {}}
    result = evaluate_proxy(base_plan(), recovery, trace, base_invocations())
    assert result["accepted"] is False
    assert any("optimizer_step" in error or "parameters" in error for error in result["errors"])


def test_rejects_target_drift():
    recovery = passing_recovery()
    recovery["paper_target"] = dict(recovery["paper_target"], dataset="other")
    trace = {"params_before": {"theta": 0.0}, "params_after": {"theta": 1.0}, "mechanism_checks": {}}
    result = evaluate_proxy(base_plan(), recovery, trace, base_invocations())
    assert result["accepted"] is False
    assert any("dataset" in error for error in result["errors"])


def test_rejects_metric_below_proxy_threshold():
    recovery = passing_recovery()
    recovery["metrics"]["expected_reward_after_training"] = 0.55
    trace = {"params_before": {"theta": 0.0}, "params_after": {"theta": 1.0}, "mechanism_checks": {}}
    result = evaluate_proxy(base_plan(), recovery, trace, base_invocations())
    assert result["accepted"] is False
    assert any("below" in error for error in result["errors"])
