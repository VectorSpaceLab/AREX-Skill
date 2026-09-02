from policy_update import policy_gradient_update


def test_update_is_feasible_and_moves_values():
    result = policy_gradient_update([0.5, 0.5], [1, 0], 0.4, 0.1, 1.0)
    updated = result['updated_probabilities']
    assert all(0.0 <= value <= 1.0 for value in updated)
    assert sum(updated) <= 1.0 + 1e-8
    assert updated != [0.5, 0.5]


def test_gradient_diagnostics_are_returned():
    result = policy_gradient_update([0.25, 0.75], [0, 1], 1.0, 0.05, 1.0)
    assert 'score_gradient' in result
    assert len(result['score_gradient']) == 2
