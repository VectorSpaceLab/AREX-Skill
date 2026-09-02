from flow_diagnostics import mechanism_summary, euler_integrate_linear_velocity

def test_endpoint_failure_blocks_proxy_acceptance():
    assert mechanism_summary(0.0, -2.0, 0.9, endpoint_threshold=0.6)["proxy_threshold_passed"] is False

def test_linear_velocity_stable_with_many_steps():
    coarse = euler_integrate_linear_velocity(0.0, [2.0, 0.0, 0.0], steps=10)
    fine = euler_integrate_linear_velocity(0.0, [2.0, 0.0, 0.0], steps=100)
    assert abs(coarse - fine) < 1e-12
