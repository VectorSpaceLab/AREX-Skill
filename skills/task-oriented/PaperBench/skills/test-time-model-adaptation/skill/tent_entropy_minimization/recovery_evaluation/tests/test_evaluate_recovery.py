from evaluate_recovery import REQUIRED_PROXY_CHECKS, evaluate_recovery


def test_valid_proxy_is_accepted():
    recovery = {"is_proxy": True, "metrics": {"entropy_reduction": 0.2}, "mechanism_checks": {key: True for key in REQUIRED_PROXY_CHECKS}}
    trace = {"loss_before": 0.6, "loss_after": 0.4, "params_before": {"scale": 1.0}, "params_after": {"scale": 1.2}}
    assert evaluate_recovery(recovery, trace, {"forbidden_sources_detected": []})["decision"] == "accept"


def test_unchanged_params_refine():
    recovery = {"is_proxy": True, "metrics": {"entropy_reduction": 0.0}, "mechanism_checks": {key: True for key in REQUIRED_PROXY_CHECKS}}
    trace = {"loss_before": 0.6, "loss_after": 0.6, "params_before": {"scale": 1.0}, "params_after": {"scale": 1.0}}
    report = evaluate_recovery(recovery, trace)
    assert report["ok"] is False
    assert "parameters_unchanged" in report["failures"]
