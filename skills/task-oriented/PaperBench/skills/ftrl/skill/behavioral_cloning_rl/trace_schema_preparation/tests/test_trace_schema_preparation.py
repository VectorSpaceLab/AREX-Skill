from trace_schema_preparation import prepare_examples

def test_prepare_examples_labels_and_contract():
    rows=[{"height":2100,"distance":-4100,"elevation":50,"airspeed":120},{"height":500,"distance":-4200,"elevation":70,"airspeed":90}]
    examples=prepare_examples(rows, source="unit")
    assert examples[0]["goal_elevation"] == 20
    assert examples[1]["elevator_action"] == "raise"
    assert "grail_prediction" not in examples[0]


def test_prepare_examples_rejects_missing_fields():
    try:
        prepare_examples([{"height": 1, "distance": -1, "elevation": 0}])
    except ValueError as exc:
        assert "missing fields" in str(exc)
    else:
        raise AssertionError("missing required fields should fail")
