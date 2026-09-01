from velocity_objective import objective_and_gradient, gradient_step, gaussian_translation_velocity

def test_gradient_step_reduces_objective():
    xs=[0.0,0.5,1.0,-0.5]; ts=[0.1,0.3,0.6,0.9]; dts=[1.0,0.8,0.4,0.1]
    params=[0.0,0.0,0.0]
    new_params, before, grad = gradient_step(params,xs,ts,dts,lr=0.2)
    after,_ = objective_and_gradient(new_params,xs,ts,dts)
    assert after < before
    assert gaussian_translation_velocity(0.0,0.5,2.0) > 0.0
