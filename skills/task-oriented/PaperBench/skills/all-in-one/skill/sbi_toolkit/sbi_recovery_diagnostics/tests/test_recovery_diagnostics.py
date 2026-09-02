from recovery_diagnostics import params_changed


def test_params_changed_accepts_parameter_update():
    trace = {"params_before": {"a": 0.0}, "params_after": {"a": 0.5}}
    assert params_changed(trace) is True


def test_params_changed_rejects_unchanged_parameters():
    trace = {"params_before": {"a": 0.0}, "params_after": {"a": 0.0}}
    assert params_changed(trace) is False
