from collections import Counter

ACTIONS = ["lower", "hold", "raise"]

def induce_rules(examples):
    if not examples:
        raise ValueError("no examples")
    goal_rules = [
        {"if": "distance > -4000", "goal_elevation": 0},
        {"if": "height > 1900", "goal_elevation": 20},
        {"if": "height > 1000", "goal_elevation": 60},
        {"else": True, "goal_elevation": 100},
    ]
    action_counts = Counter(ex["elevator_action"] for ex in examples)
    majority_action = action_counts.most_common(1)[0][0]
    effect_rules = [
        {"if": "goal_elevation - elevation > 8", "elevator_action": "raise"},
        {"if": "goal_elevation - elevation < -8", "elevator_action": "lower"},
        {"else": True, "elevator_action": "hold"},
    ]
    direct_rules = [{"if": "majority", "elevator_action": majority_action}]
    return {"goal_rules": goal_rules, "effect_rules": effect_rules, "direct_rules": direct_rules}

def predict_goal(row, rules):
    height = float(row["height"]); distance = float(row["distance"])
    if distance > -4000:
        return 0
    if height > 1900:
        return 20
    if height > 1000:
        return 60
    return 100

def predict_action(row, rules):
    goal = predict_goal(row, rules.get("goal_rules", []))
    error = goal - float(row["elevation"])
    if error > 8:
        return "raise"
    if error < -8:
        return "lower"
    return "hold"

def direct_predict_action(row, rules):
    return rules.get("direct_rules", [{"elevator_action": "hold"}])[0]["elevator_action"]

def train_scalar_student(examples, learning_rate=0.001):
    params_before = {"bias": 0.0, "goal_weight": 0.0}
    def loss(params):
        total = 0.0
        for ex in examples:
            target = {"lower": -1.0, "hold": 0.0, "raise": 1.0}[ex["elevator_action"]]
            pred = params["bias"] + params["goal_weight"] * ((ex["goal_elevation"] - ex["elevation"]) / 100.0)
            total += (pred - target) ** 2
        return total / len(examples)
    loss_before = loss(params_before)
    grad_bias = 0.0; grad_weight = 0.0
    for ex in examples:
        target = {"lower": -1.0, "hold": 0.0, "raise": 1.0}[ex["elevator_action"]]
        feature = (ex["goal_elevation"] - ex["elevation"]) / 100.0
        pred = params_before["bias"] + params_before["goal_weight"] * feature
        grad_bias += 2 * (pred - target) / len(examples)
        grad_weight += 2 * (pred - target) * feature / len(examples)
    params_after = {"bias": params_before["bias"] - learning_rate * grad_bias, "goal_weight": params_before["goal_weight"] - learning_rate * grad_weight}
    return {"loss_before": loss_before, "loss_after": loss(params_after), "params_before": params_before, "params_after": params_after, "optimizer_state_changed": params_before != params_after}
