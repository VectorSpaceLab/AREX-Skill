from pope_negative_sampling import co_occurrence_rankings, object_frequencies, select_negative


def fixture_records():
    return [
        {"image": "i1", "objects": ["cat", "sofa", "lamp"]},
        {"image": "i2", "objects": ["cat", "dog"]},
        {"image": "i3", "objects": ["cat", "sofa", "table"]},
    ]


def test_popular_negative_is_absent_and_frequent():
    selected = select_negative(fixture_records(), ["cat", "sofa"], strategy="popular")
    assert selected == "dog" or selected == "lamp" or selected == "table"
    assert selected not in {"cat", "sofa"}
    assert object_frequencies(fixture_records())["cat"] == 3


def test_adversarial_uses_co_occurrence_when_eligible():
    rankings = co_occurrence_rankings(fixture_records())
    assert rankings["cat"][0] == "sofa"
    selected = select_negative(fixture_records(), ["cat", "lamp"], strategy="adversarial", anchor="cat")
    assert selected == "sofa"


def test_no_present_object_selected():
    selected = select_negative(fixture_records(), ["cat", "sofa", "lamp"], history=["dog"], strategy="popular")
    assert selected not in {"cat", "sofa", "lamp", "dog"}


def test_no_eligible_object_raises_clear_error():
    try:
        select_negative([{"image": "only", "objects": ["cat"]}], ["cat"], strategy="random")
    except ValueError as exc:
        assert "no eligible absent object" in str(exc)
    else:
        raise AssertionError("expected no eligible absent object error")
