from neural_training import demo_records, train_conditional_gaussian_proxy


def test_reduced_training_changes_parameters_and_reduces_loss():
    result = train_conditional_gaussian_proxy(demo_records(), steps=60, learning_rate=0.05)
    trace = result["trace"]
    assert trace["params_before"] != trace["params_after"]
    assert trace["optimizer_state_changed"] is True
    assert trace["loss_after"] < trace["loss_before"]
    assert result["estimator"]["family"] == "SNPE"


def test_unsupported_family_fails_clearly():
    try:
        train_conditional_gaussian_proxy(demo_records(), family="ABC")
    except ValueError as exc:
        assert "unsupported SBI family" in str(exc)
    else:
        raise AssertionError("unsupported family should fail")
