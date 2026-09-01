from minibatch_ot import assignment_cost, cost_matrix, exact_minibatch_ot


def test_identity_like_assignment_minimizes_cost():
    source = [[0.0], [10.0]]
    target = [[0.2], [9.8]]
    result = exact_minibatch_ot(source, target)
    assert result["permutation"] == [0, 1]
    crossed = assignment_cost(cost_matrix(source, target), [1, 0])
    assert result["transport_cost"] < crossed
