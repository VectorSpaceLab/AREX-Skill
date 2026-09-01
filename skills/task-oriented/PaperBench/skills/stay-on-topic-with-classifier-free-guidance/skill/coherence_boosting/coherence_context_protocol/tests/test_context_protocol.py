from context_protocol import build_record, validate_record

def test_build_separates_contexts():
    ex={"premise":"Paris is in France.","prompt":"Answer:","candidates":["France","Italy"],"label":0}
    rec=build_record(ex)
    assert "Paris" in rec["full_context"]
    assert "Paris" not in rec["premise_free_context"]
    assert validate_record(rec)

def test_invalid_label_rejected():
    try:
        build_record({"premise":"p","prompt":"q","candidates":["a"],"label":2})
    except ValueError as exc:
        assert "label" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_candidate_order_preserved():
    ex={"premise":"A distant clue matters.","prompt":"Answer:","candidates":["first","second"],"label":1}
    rec=build_record(ex)
    assert rec["candidates"] == ["first","second"]
    assert rec["label"] == 1
