from reduced_ldm_step import compute_loss, run_reduced_step


def test_reduced_step_changes_params_and_reduces_loss():
    trace = run_reduced_step([1.0, 0.5, -0.5], [0.25, -0.1, 0.4], 0.8, 0.6, 0.0, 0.0, 0.5)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_before"] != trace["params_after"]
    assert trace["mechanism_checks"]["optimizer_step_executed"] is True


def test_loss_rejects_mismatched_lengths():
    try:
        compute_loss([1.0], [1.0, 2.0], 0.0, 0.0)
    except ValueError as exc:
        assert "lengths" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_trace_has_validator_fields():
    trace = run_reduced_step([1.0], [0.5], 0.7, 0.3, 0.0, 0.0, 0.1)
    assert "params_before" in trace
    assert "params_after" in trace
    assert "loss_before" in trace
    assert "loss_after" in trace


def test_zero_learning_rate_does_not_count_as_optimizer_step():
    trace = run_reduced_step([1.0], [0.5], 0.7, 0.3, 0.0, 0.0, 0.0)
    assert trace["params_before"] == trace["params_after"]
    assert trace["mechanism_checks"]["optimizer_step_executed"] is False
