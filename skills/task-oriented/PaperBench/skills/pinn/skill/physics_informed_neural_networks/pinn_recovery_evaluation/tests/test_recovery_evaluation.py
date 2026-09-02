from evaluate_recovery import build_mechanism_checks, compute_metrics


def test_metrics_and_checks_from_trace():
    trace = {
        "loss_before": 2.0,
        "loss_after": 1.5,
        "data_loss_before": 1.0,
        "data_loss_after": 0.8,
        "residual_loss_before": 1.0,
        "residual_loss_after": 0.7,
        "params_before": {"bias": 0.0},
        "params_after": {"bias": 0.1},
    }
    metrics = compute_metrics(trace)
    checks = build_mechanism_checks(trace, ["pde_problem_specification", "autodiff_pde_residual"])
    assert metrics["loss_reduction"] == 0.5
    assert checks["optimizer_step_executed"] is True
    assert checks["burgers_residual_computed"] is True
