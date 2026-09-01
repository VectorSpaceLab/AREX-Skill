from flow_diagnostics import euler_integrate_constant_velocity, euler_integrate_linear_velocity, loss_decrease_fraction, mechanism_summary

def test_diagnostics_thresholds():
    assert abs(euler_integrate_constant_velocity(0.0,2.0,steps=20)-2.0) < 1e-12
    assert loss_decrease_fraction(0.0,-2.0) == 1.0
    assert mechanism_summary(0.0,-2.0,0.1)["proxy_threshold_passed"] is True

def test_linear_velocity_changes_endpoint():
    end = euler_integrate_linear_velocity(0.0, [2.0, 0.0, 0.0], steps=20)
    assert abs(end - 2.0) < 1e-12
