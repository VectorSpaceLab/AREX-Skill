
def select_norm_affine_parameters(parameters):
    trainable, frozen = {}, {}
    for name, value in parameters.items():
        lower = name.lower()
        is_norm = any(token in lower for token in ['norm', 'bn', 'gn', 'ln'])
        is_affine = lower.endswith('.weight') or lower.endswith('.bias') or lower.endswith('_weight') or lower.endswith('_bias')
        if is_norm and is_affine:
            trainable[name] = value
        else:
            frozen[name] = value
    return {'trainable': trainable, 'frozen': frozen, 'trainable_names': list(trainable), 'frozen_names': list(frozen)}

def proxy_parameter_set():
    return {'encoder.weight': 1.0, 'gn1.weight': 0.7, 'gn1.bias': 0.0, 'classifier.bias': 0.1, 'ln_head.weight': 1.2}
