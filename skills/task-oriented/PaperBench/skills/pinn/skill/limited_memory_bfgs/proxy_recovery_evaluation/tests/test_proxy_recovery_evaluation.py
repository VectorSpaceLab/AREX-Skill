from proxy_recovery_evaluation import gradient_norm_ratio, build_mechanism_checks

def test_ratio_and_checks():
    trace = [{"memory_length": 0, "step": 1.0, "descent_dot": -1.0, "scaling": 1.0}, {"memory_length": 1, "step": 1.0, "descent_dot": -0.5, "scaling": 0.25}]
    assert gradient_norm_ratio(2.0, 8.0) == 0.25
    checks = build_mechanism_checks(trace, 3, 8.0, 2.0)
    assert checks["limited_memory_used"]
    assert checks["memory_bound_respected"]
    assert checks["scalar_scaling_used"]
