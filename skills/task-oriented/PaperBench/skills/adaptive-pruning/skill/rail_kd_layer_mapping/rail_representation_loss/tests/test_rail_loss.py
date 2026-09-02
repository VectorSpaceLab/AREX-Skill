from rail_loss import concatenated_loss, layerwise_loss, mean_pool


def test_mean_pool_exact():
    assert mean_pool([[1.0, 3.0], [3.0, 5.0]]) == [2.0, 4.0]


def test_layerwise_zero_for_identical_vectors():
    layers = [[[1.0, 0.0], [1.0, 0.0]], [[0.0, 2.0], [0.0, 2.0]]]
    ident = [[1.0, 0.0], [0.0, 1.0]]
    loss, diag = layerwise_loss(layers, layers, ident, ident)
    assert abs(loss) < 1e-12
    assert diag["variant"] == "layerwise"
    assert diag["mean_pooling_used"] is True


def test_layerwise_positive_for_mismatch():
    teacher = [[[1.0, 0.0]], [[0.0, 1.0]]]
    student = [[[0.0, 1.0]], [[1.0, 0.0]]]
    ident = [[1.0, 0.0], [0.0, 1.0]]
    loss, _ = layerwise_loss(teacher, student, ident, ident)
    assert loss > 1.0


def test_concatenated_variant_runs():
    teacher = [[[1.0, 0.0]], [[0.0, 1.0]]]
    student = [[[1.0, 0.0]], [[0.2, 1.0]]]
    proj = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]
    loss, diag = concatenated_loss(teacher, student, proj, proj)
    assert loss >= 0.0
    assert diag["variant"] == "concatenated"


def test_invalid_empty_layer_raises():
    try:
        mean_pool([])
        assert False, "expected ValueError"
    except ValueError:
        pass
