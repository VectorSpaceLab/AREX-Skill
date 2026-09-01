from spatial_plan import make_spatial_plan


def test_valid_latent_grid():
    result = make_spatial_plan(256, 512, 8, 20)
    assert result["ok"] is True
    assert result["latent_grid"] == [32, 64]


def test_dense_conditioning_can_align_to_latent_grid():
    result = make_spatial_plan(256, 512, 8, 20, 32, 64)
    assert result["ok"] is True
    assert result["conditioning_alignment"] == "latent_space"


def test_rejects_non_divisible_and_mismatched_conditioning():
    result = make_spatial_plan(255, 512, 8, 20, 20, 20)
    assert result["ok"] is False
    assert any("divisible" in item for item in result["errors"])
    assert any("conditioning" in item for item in result["errors"])


def test_warns_for_unbounded_steps():
    result = make_spatial_plan(256, 256, 8, 100)
    assert result["ok"] is True
    assert result["warnings"]
