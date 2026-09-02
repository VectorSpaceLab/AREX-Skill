
from cofi_layer_distill import monotone_alignment, layerwise_distillation_loss

def test_alignment_is_monotone_for_surviving_layers():
    pairs=monotone_alignment(6, [1,0,1,1])
    assert [p[0] for p in pairs] == [0,2,3]
    assert [p[1] for p in pairs] == sorted([p[1] for p in pairs])

def test_loss_lower_for_matching_states():
    teacher=[[0,0],[1,1],[2,2]]
    good=[[0,0],[0,0],[2,2]]
    bad=[[5,5],[0,0],[-2,-2]]
    assert layerwise_distillation_loss(teacher, good, [1,0,1])['loss'] < layerwise_distillation_loss(teacher, bad, [1,0,1])['loss']

def test_nested_hidden_states_are_supported():
    from cofi_layer_distill import layerwise_distillation_loss
    out=layerwise_distillation_loss([[[1,2],[3,4]]], [[[1,2],[3,5]]], [1])
    assert out['valid'] and out['loss'] == 0.25
