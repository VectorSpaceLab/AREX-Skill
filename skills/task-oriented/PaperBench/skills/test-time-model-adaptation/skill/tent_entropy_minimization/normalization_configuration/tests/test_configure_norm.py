from configure_norm import configure_inventory


def test_only_bn_affine_is_trainable():
    inventory = {"modules": [
        {"name": "bn", "type": "BatchNorm2d", "parameters": {"weight": {}, "bias": {}}},
        {"name": "fc", "type": "Linear", "parameters": {"weight": {}, "bias": {}}},
    ]}
    report = configure_inventory(inventory)
    assert report["ok"] is True
    assert report["trainable_parameters"] == ["bn.weight", "bn.bias"]


def test_missing_norm_is_rejected():
    report = configure_inventory({"modules": [{"name": "fc", "type": "Linear", "parameters": {"weight": {}}}]})
    assert report["ok"] is False
    assert "no_normalization_layers" in report["errors"]
