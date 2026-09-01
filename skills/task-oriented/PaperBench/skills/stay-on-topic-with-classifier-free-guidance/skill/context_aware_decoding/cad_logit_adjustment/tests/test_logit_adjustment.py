from cad_logits import adjust_logits
def test_alpha_zero_matches_context_argmax():
    adjusted, diag=adjust_logits({"a":2,"b":1},{"a":-5,"b":5},alpha=0)
    assert adjusted=={"a":2.0,"b":1.0}; assert diag["adjusted_argmax"]=="a"
def test_conflict_keeps_context_supported_token():
    adjusted, diag=adjust_logits({"Paris":2.0,"London":2.2},{"Paris":5.0,"London":0.0},alpha=1)
    assert diag["adjusted_argmax"]=="London"; assert adjusted["London"]>adjusted["Paris"]
def test_vocab_mismatch_errors():
    try: adjust_logits({"a":1},{"b":1})
    except ValueError as exc: assert "vocabularies" in str(exc)
    else: raise AssertionError("mismatch should fail")
