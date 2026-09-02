from p3o_loss import p3o_components

def test_loss_decomposition_arithmetic():
    out = p3o_components([1.0], [0.2], [2.0], [0.5], [4.0], 0.25, 0.3, [0.5,0.5], [0.7,0.3])
    assert out['clipped_ratios'] == [0.25]
    assert out['kl_penalty'] >= 0.0
    assert abs(out['objective'] - (out['on_policy'] + out['off_policy'] - 0.3*out['kl_penalty'])) < 1e-12
