from parameter_freezing import trainable_map, lora_state_dict

def test_only_lora_trainable_by_default():
    names=['encoder.weight','encoder.bias','attn.lora_A','attn.lora_B']
    m=trainable_map(names)
    assert m['attn.lora_A'] and m['attn.lora_B']
    assert not m['encoder.weight'] and not m['encoder.bias']

def test_lora_state_dict_excludes_backbone():
    params={'w':[1], 'layer.lora_A':[2], 'layer.lora_B':[3]}
    assert set(lora_state_dict(params)) == {'layer.lora_A','layer.lora_B'}
