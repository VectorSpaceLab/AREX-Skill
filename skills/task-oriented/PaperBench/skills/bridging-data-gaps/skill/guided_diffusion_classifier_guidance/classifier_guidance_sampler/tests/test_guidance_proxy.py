from guidance_proxy import run_proxy


def test_guidance_improves_target_distance():
    result = run_proxy(1.5)
    assert result["metrics"]["guided_distance_improvement"] > 0
    assert result["mechanism_checks"]["guided_distance_improved"] is True


def test_zero_scale_has_no_guidance():
    result = run_proxy(0.0)
    assert result["result"]["guidance"] == 0
    assert result["mechanism_checks"]["classifier_scale_applied"] is False
