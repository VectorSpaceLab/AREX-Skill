from preference_data import normalize_records

def test_explicit_normalization_preserves_direction():
    out = normalize_records([{"prompt":"Q","chosen":" A","rejected":" B","source":"unit"}])
    assert out[0]["prompt"] == "Q"
    assert out[0]["chosen"] == " A"
    assert out[0]["rejected"] == " B"
    assert out[0]["source"] == "unit"

def test_hh_style_split():
    out = normalize_records([{"format":"hh","chosen":"\n\nHuman: hi\n\nAssistant: safe","rejected":"\n\nHuman: hi\n\nAssistant: unsafe"}])
    assert out[0]["prompt"] == "\n\nHuman: hi\n\nAssistant:"
    assert out[0]["chosen"] == " safe"
    assert out[0]["rejected"] == " unsafe"

def test_rejects_identical_responses():
    try:
        normalize_records([{"prompt":"Q","chosen":"same","rejected":"same"}])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "differ" in str(exc)


def test_rejects_hh_prompt_mismatch():
    try:
        normalize_records([{"format":"hh","chosen":"\n\nHuman: a\n\nAssistant: yes","rejected":"\n\nHuman: b\n\nAssistant: no"}])
        assert False, "expected mismatch failure"
    except ValueError as exc:
        assert "share a prompt" in str(exc)
