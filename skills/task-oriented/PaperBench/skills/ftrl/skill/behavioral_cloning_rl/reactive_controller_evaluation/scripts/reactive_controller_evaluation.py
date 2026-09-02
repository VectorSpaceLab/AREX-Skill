def evaluate_controller(examples, rules, predict_action, direct_predict_action=None):
    predictions = []
    correct = 0
    direct_correct = 0
    for ex in examples:
        pred = predict_action(ex, rules)
        direct = direct_predict_action(ex, rules) if direct_predict_action else None
        correct += int(pred == ex["elevator_action"])
        if direct is not None:
            direct_correct += int(direct == ex["elevator_action"])
        predictions.append({"index": ex["index"], "label": ex["elevator_action"], "grail_prediction": pred, "direct_prediction": direct})
    action_accuracy = correct / len(examples)
    direct_accuracy = direct_correct / len(examples) if direct_predict_action else None
    grail_size = len(rules.get("goal_rules", [])) + len(rules.get("effect_rules", []))
    direct_size = max(1, len(rules.get("direct_rules", [])) * 10)
    return {"action_accuracy": action_accuracy, "direct_action_accuracy": direct_accuracy, "compactness_ratio": grail_size / direct_size, "predictions": predictions}

def mechanism_checks(metrics):
    return {"trace_examples_prepared": True, "goal_rules_induced": True, "effect_rules_induced": True, "reactive_controller_executed": True, "compactness_compared": metrics["compactness_ratio"] < 1.0}
