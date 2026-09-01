from evaluate_bar_recovery import build_mechanism_checks


def test_loss_tolerance_allows_numerical_jitter_only():
    trace = {"params_before": [0.0], "params_after": [0.1], "loss_before": 1.0, "loss_after": 1.0 + 5e-7, "loss_tolerance": 1e-6, "query_count": 4}
    checks = build_mechanism_checks(trace)
    assert checks["loss_decreased"] is True
    bad = dict(trace)
    bad["loss_after"] = 1.0 + 1e-3
    assert build_mechanism_checks(bad)["loss_decreased"] is False
