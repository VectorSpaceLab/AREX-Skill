from latent_contract import validate_latent_contract


def test_valid_contract_shape_and_ratio():
    result = validate_latent_contract(16, 16, 3, 4, 3, "none")
    assert result["ok"] is True
    assert result["latent_shape"] == [4, 4, 3]
    assert result["spatial_reduction"] == 16
    assert result["compression_ratio"] == 16.0


def test_rejects_non_rgb_and_bad_factor():
    result = validate_latent_contract(15, 16, 1, 4, 3, "kl")
    assert result["ok"] is False
    assert any("RGB" in item for item in result["errors"])
    assert any("divisible" in item for item in result["errors"])


def test_rejects_unknown_regularization():
    result = validate_latent_contract(16, 16, 3, 4, 3, "gan_only")
    assert result["ok"] is False
    assert any("unsupported" in item for item in result["errors"])
