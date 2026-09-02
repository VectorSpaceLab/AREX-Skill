from factor_contracts import build_and_validate, feature_vector


def test_contracts_keep_observed_as_parents_only():
    inverse = {
        "x0": ["x1", "x2"],
        "x1": ["x2", "x3", "x4"],
        "x2": ["x3", "x4", "x5", "x6"],
    }
    result = build_and_validate(
        inverse,
        ["x0", "x1", "x2"],
        ["x3", "x4", "x5", "x6"],
        ["x0", "x1", "x2"],
        families={"x0": "gaussian", "x1": "gaussian", "x2": "gaussian"},
    )
    assert result["validation"]["ok"], result["validation"]["issues"]
    assert [item["variable"] for item in result["contracts"]] == ["x2", "x1", "x0"]
    assert any(item["observed_parents"] for item in result["contracts"])
    assert all(item["family"] == "gaussian" for item in result["contracts"])


def test_feature_vector_uses_contract_order():
    contract = {"feature_order": ["b", "a"]}
    assert feature_vector(contract, {"a": 1, "b": 2}) == [2.0, 1.0]


def test_missing_feature_value_fails():
    try:
        feature_vector({"feature_order": ["missing"]}, {})
    except KeyError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("missing feature should fail")


def test_unknown_parent_contract_is_invalid_and_feature_extraction_fails_fast():
    result = build_and_validate({"z": ["x", "missing_parent"]}, ["z"], ["x"], ["z"])
    assert not result["validation"]["ok"]
    assert any(item["check"] == "unknown_parent" for item in result["validation"]["issues"])
    try:
        feature_vector(result["contracts"][0], {"x": 1.0})
    except KeyError as exc:
        assert "missing_parent" in str(exc)
    else:
        raise AssertionError("unknown parent should not be silently zero-filled")
