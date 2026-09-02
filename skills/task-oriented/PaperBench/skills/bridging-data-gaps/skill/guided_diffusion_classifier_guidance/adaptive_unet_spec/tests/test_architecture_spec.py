from architecture_spec import example_spec, validate_architecture


def test_paper128_spec_passes():
    result = validate_architecture(example_spec("paper128"))
    assert result["ok"] is True
    assert result["errors"] == []


def test_missing_scale_shift_fails():
    spec = example_spec("paper128")
    spec["use_scale_shift_norm"] = False
    result = validate_architecture(spec)
    assert result["ok"] is False
    assert "scale-shift" in result["errors"][0]
