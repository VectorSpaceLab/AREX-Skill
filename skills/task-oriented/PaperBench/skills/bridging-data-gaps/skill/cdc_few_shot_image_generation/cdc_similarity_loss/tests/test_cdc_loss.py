from cdc_loss import cdc_loss


def test_identical_activations_have_zero_loss():
    layers = {'l1': [[1,0], [0,1], [1,1]]}
    result = cdc_loss(layers, layers)
    assert result['total_loss'] < 1e-12


def test_collapsed_adapted_vectors_increase_loss():
    src = {'l1': [[1,0], [0,1], [1,1]]}
    adapted = {'l1': [[1,0], [1,0], [1,0]]}
    result = cdc_loss(src, adapted)
    assert result['total_loss'] > 0.01
