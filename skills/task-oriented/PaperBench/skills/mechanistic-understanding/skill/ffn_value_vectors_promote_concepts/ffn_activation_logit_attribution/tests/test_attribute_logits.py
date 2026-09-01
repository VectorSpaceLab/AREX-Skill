from attribute_logits import attribution_margin

def test_active_positive_margin_passes():
    assert attribution_margin(2,[1,.8],[0,.1])['passes'] is True
def test_inactive_neuron_fails():
    assert attribution_margin(0,[1],[0])['passes'] is False
