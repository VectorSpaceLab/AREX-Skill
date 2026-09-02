from verifier_training import train_verifier


def test_training_changes_params_and_reduces_loss():
    candidates = [
        {"solution": "Good <<2+2=4>>\n#### 4", "label": 1, "source": "gold_solution", "calculator_checks": [{"ok": True}]},
        {"solution": "Bad <<2+2=5>>\n#### 5", "label": 0, "source": "perturbed_final_answer_1", "calculator_checks": [{"ok": False}]},
    ]
    result = train_verifier(candidates, learning_rate=0.8, steps=5)
    assert result["params_before"] != result["params_after"]
    assert result["loss_after"] < result["loss_before"]
    assert all("verifier_score" in item for item in result["scored_candidates"])


def test_zero_step_training_records_no_optimizer_change():
    candidates = [
        {"solution": "Good <<2+2=4>>\n#### 4", "label": 1, "source": "gold_solution", "calculator_checks": [{"ok": True}]},
        {"solution": "Bad <<2+2=5>>\n#### 5", "label": 0, "source": "perturbed_final_answer_1", "calculator_checks": [{"ok": False}]},
    ]
    result = train_verifier(candidates, learning_rate=0.8, steps=0)
    assert result["params_before"] == result["params_after"]
    assert result["loss_before"] == result["loss_after"]
    assert result["optimizer_state_changed"] is False
