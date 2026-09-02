from reactive_controller_evaluation import evaluate_controller, mechanism_checks

def test_evaluate_controller_metrics():
    examples=[{"index":0,"elevator_action":"raise"}]
    rules={"goal_rules":[1],"effect_rules":[1],"direct_rules":[{"elevator_action":"hold"}]}
    metrics=evaluate_controller(examples, rules, lambda ex, r: "raise", lambda ex, r: "hold")
    checks=mechanism_checks(metrics)
    assert metrics["action_accuracy"] == 1.0
    assert checks["reactive_controller_executed"] is True


def test_compactness_check_requires_ratio_below_one():
    examples=[{"index":0,"elevator_action":"raise"}]
    compact={"goal_rules":[1],"effect_rules":[1],"direct_rules":[{"elevator_action":"hold"}]}
    metrics=evaluate_controller(examples, compact, lambda ex, r: "raise", lambda ex, r: "hold")
    assert mechanism_checks(metrics)["compactness_compared"] is True
    bloated={"goal_rules":[1,2,3,4,5],"effect_rules":[1,2,3,4,5],"direct_rules":[{"elevator_action":"hold"}]}
    metrics=evaluate_controller(examples, bloated, lambda ex, r: "raise", lambda ex, r: "hold")
    assert mechanism_checks(metrics)["compactness_compared"] is False
