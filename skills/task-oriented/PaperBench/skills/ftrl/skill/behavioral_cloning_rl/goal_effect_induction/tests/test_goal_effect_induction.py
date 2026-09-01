from goal_effect_induction import induce_rules, predict_action, train_scalar_student

def test_induce_rules_predicts_and_trains():
    examples=[{"height":2100,"distance":-4100,"elevation":50,"goal_elevation":20,"elevator_action":"lower"},{"height":500,"distance":-4200,"elevation":70,"goal_elevation":100,"elevator_action":"raise"}]
    rules=induce_rules(examples)
    assert predict_action(examples[0], rules) == "lower"
    trace=train_scalar_student(examples)
    assert trace["params_before"] != trace["params_after"]
    assert "loss_before" in trace and "loss_after" in trace
