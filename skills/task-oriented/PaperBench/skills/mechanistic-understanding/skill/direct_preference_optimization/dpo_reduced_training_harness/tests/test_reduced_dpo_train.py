from reduced_dpo_train import run_reduced_training

def test_reduced_training_decreases_loss_and_changes_params():
    examples = [{"prompt":"p1","chosen":"good","rejected":"bad"}, {"prompt":"p2","chosen":"safe","rejected":"unsafe"}]
    out = run_reduced_training(examples, beta=0.5, lr=0.8, steps=25)
    assert out["loss_after"] < out["loss_before"]
    assert out["params_before"] != out["params_after"]
    assert out["mechanism_checks"]["optimizer_step_executed"] is True

def test_accuracy_reaches_one_on_tiny_problem():
    examples = [{"prompt":"p","chosen":"c","rejected":"r"} for _ in range(3)]
    out = run_reduced_training(examples, steps=30)
    assert out["preference_accuracy_after_update"] == 1.0
    assert min(out["margins_after"]) > max(out["margins_before"])

def test_rejects_empty_dataset():
    try:
        run_reduced_training([])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "at least one" in str(exc)


def test_full_training_flags_remain_false_for_reduced_proxy():
    out = run_reduced_training([{"prompt":"p","chosen":"c","rejected":"r"}], steps=5)
    checks = out["mechanism_checks"]
    assert checks["reduced_training_executed"] is True
    assert checks["training_step_executed"] is False
    assert checks["qwen3_model_loaded"] is False
