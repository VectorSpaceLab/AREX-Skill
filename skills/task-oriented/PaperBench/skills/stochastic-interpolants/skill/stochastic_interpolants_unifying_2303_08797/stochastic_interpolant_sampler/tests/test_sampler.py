from sampler import integrate_ode, integrate_sde


def test_ode_constant_velocity_translation():
    result = integrate_ode([0.0, 1.0], lambda t, x: 2.0, steps=4)
    assert result["samples"] == [2.0, 3.0]
    assert result["trajectory"][0]["summary"]["mean"] == 0.5
    assert result["trajectory"][-1]["summary"]["mean"] == 2.5


def test_zero_epsilon_sde_is_drift_only():
    result = integrate_sde([0.0], lambda t, x: 1.0, lambda t, x: 999.0, epsilon=0.0, steps=5, seed=3)
    assert abs(result["samples"][0] - 1.0) < 1e-12


def test_ode_moves_mean_toward_positive_target_with_positive_velocity():
    result = integrate_ode([-1.0, 0.0, 1.0], lambda t, x: 0.5, steps=10)
    assert result["trajectory"][-1]["summary"]["mean"] > result["trajectory"][0]["summary"]["mean"]
