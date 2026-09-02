from influence import influence_hypergradients, update_weights


def test_influence_signs_and_projection():
    hyper = influence_hypergradients([1.0, 0.0], [[-1.0, 0.0], [1.0, 0.0]], [1.0, 1.0], damping=0.0)
    assert hyper == [1.0, -1.0]
    updated, diagnostics = update_weights({'a': 0.2, 'b': 0.2}, ['a', 'b'], hyper, lr=0.5)
    assert updated['a'] == 0.0
    assert updated['b'] == 0.7
    assert diagnostics[0]['delta'] < 0 and diagnostics[1]['delta'] > 0


def test_damping_keeps_hypergradients_finite():
    hyper = influence_hypergradients([1.0, 1.0], [[1.0, -1.0]], [0.0, 0.0], damping=0.5)
    assert len(hyper) == 1
    assert abs(hyper[0]) < 1e-9
