from ode import simulate

def test_constant_velocity_is_straight():
    params = {'w_x': [0.0], 'w_t': [0.0], 'b': [2.0]}
    result = simulate([[0.0]], params, steps=4)
    assert abs(result['paths'][0]['z1'][0] - 2.0) < 1e-9
    assert abs(result['mean_straightness_ratio'] - 1.0) < 1e-9
