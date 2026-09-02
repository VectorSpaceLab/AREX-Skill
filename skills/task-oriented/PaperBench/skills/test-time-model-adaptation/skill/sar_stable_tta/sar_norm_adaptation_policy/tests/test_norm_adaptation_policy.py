from norm_adaptation_policy import select_norm_affine_parameters, proxy_parameter_set

def test_selects_only_norm_affine():
    result = select_norm_affine_parameters(proxy_parameter_set())
    assert 'gn1.weight' in result['trainable']
    assert 'ln_head.weight' in result['trainable']
    assert 'encoder.weight' in result['frozen']
    assert 'classifier.bias' in result['frozen']
