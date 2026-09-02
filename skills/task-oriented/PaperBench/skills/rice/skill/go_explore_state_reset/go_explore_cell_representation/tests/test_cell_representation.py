from cell_representation import describe_cell_config, encode_cell


def test_domain_field_key_is_ordered_and_deterministic():
    state = {"room": 3, "x": 11, "y": 7, "score": 100}
    assert encode_cell(state, fields=["room", "x", "y"]) == (3, 11, 7)
    assert encode_cell(state, fields=["y", "x"]) == (7, 11)


def test_coordinate_bucket_collides_intentionally():
    assert encode_cell({"room": 1, "x": 4, "y": 5}, bucket_size=4) == (1, 1, 1)
    assert encode_cell({"room": 1, "x": 7, "y": 7}, bucket_size=4) == (1, 1, 1)


def test_missing_field_raises_clear_error():
    try:
        encode_cell({"x": 1}, fields=["x", "y"])
    except KeyError as exc:
        assert "missing field" in str(exc)
    else:
        raise AssertionError("missing field did not raise")


def test_config_description_has_mode():
    assert describe_cell_config(fields=["room"])["mode"] == "domain_fields"
    assert describe_cell_config(bucket_size=2)["mode"] == "coordinate_bucket"
