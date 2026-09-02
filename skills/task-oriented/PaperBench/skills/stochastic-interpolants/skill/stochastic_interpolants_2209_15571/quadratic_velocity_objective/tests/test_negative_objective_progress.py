from velocity_objective import objective_and_gradient, gradient_step

def test_negative_objective_progress_is_detectable():
    xs=[0.0, 0.5, 1.0, 1.5]
    ts=[0.1, 0.3, 0.6, 0.9]
    dts=[1.2, 1.0, 0.6, 0.2]
    params=[0.0, 0.0, 0.0]
    for _ in range(20):
        params, _, _ = gradient_step(params, xs, ts, dts, lr=0.05)
    after, _ = objective_and_gradient(params, xs, ts, dts)
    assert after < 0.0
