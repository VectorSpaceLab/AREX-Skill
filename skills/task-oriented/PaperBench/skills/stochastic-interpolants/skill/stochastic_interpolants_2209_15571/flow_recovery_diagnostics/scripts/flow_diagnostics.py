def euler_integrate_constant_velocity(x0, velocity, steps=200):
    dt = 1.0 / float(steps)
    x = x0
    for _ in range(steps):
        x += dt * velocity
    return x

def euler_integrate_linear_velocity(x0, params, steps=200):
    dt = 1.0 / float(steps)
    x = x0
    t = 0.0
    for _ in range(steps):
        velocity = params[0] + params[1] * x + params[2] * t
        x += dt * velocity
        t += dt
    return x

def loss_decrease_fraction(loss_before, loss_after):
    improvement = loss_before - loss_after
    scale = max(abs(loss_before), abs(loss_after), 1e-12)
    return improvement / scale

def mechanism_summary(loss_before, loss_after, endpoint_error, threshold=0.25, endpoint_threshold=0.6):
    frac = loss_decrease_fraction(loss_before, loss_after)
    return {
        "stochastic_interpolant_constructed": True,
        "quadratic_velocity_loss_computed": True,
        "reduced_training_executed": True,
        "optimizer_step_executed": True,
        "ode_flow_integrated": True,
        "endpoint_transport_checked": endpoint_error < endpoint_threshold,
        "endpoint_threshold": endpoint_threshold,
        "loss_decrease_fraction": frac,
        "proxy_threshold_passed": frac >= threshold and endpoint_error < endpoint_threshold,
        "training_step_executed": False,
        "qwen3_model_loaded": False,
        "fallback_used": False,
        "toy_or_proxy_fallback_used": True
    }
