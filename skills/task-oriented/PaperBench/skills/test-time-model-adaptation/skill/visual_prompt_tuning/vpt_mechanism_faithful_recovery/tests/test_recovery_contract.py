from proxy_contract import mechanism_checks


def test_mechanism_checks_require_skills_and_freeze():
    trace = {
        "base_sequence_length": 3,
        "prompted_sequence_length": 5,
        "deep_prompt_path_checked": True,
        "optimizer_step_executed": True,
        "params_before": {"prompt_bias": 0.0, "head_weight": 0.5, "backbone_weight": 2.0},
        "params_after": {"prompt_bias": 0.1, "head_weight": 0.6, "backbone_weight": 2.0},
    }
    invocations = [{"skill_name": "vpt_prompt_token_insertion"}, {"skill_name": "vpt_frozen_prompt_training"}, {"skill_name": "vpt_evaluation_protocol"}]
    result = {"metrics": {"accuracy_after_one_step": 1.0}}
    checks = mechanism_checks(trace, invocations, result)
    assert all(checks.values())


def test_detects_missing_metric():
    checks = mechanism_checks({"params_before": {}, "params_after": {}}, [], {"metrics": {}})
    assert checks["numeric_metric_present"] is False
    assert checks["required_skills_invoked"] is False
