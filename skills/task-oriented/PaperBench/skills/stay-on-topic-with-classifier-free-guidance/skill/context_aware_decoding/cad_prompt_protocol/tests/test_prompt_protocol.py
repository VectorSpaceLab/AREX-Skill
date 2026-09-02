from prompt_protocol import build_prompt_record
def test_full_and_prior_branch_separation():
    rec=build_prompt_record("Doc says CEO is Alice.", "Who is CEO? ", "A")
    assert "Doc says CEO is Alice." in rec["full_prompt"]
    assert "Doc says CEO is Alice." not in rec["prior_prompt"]
    assert rec["context_absent_from_prior"] is True
def test_empty_context_rejected():
    try: build_prompt_record("", "Question?")
    except ValueError as exc: assert "context" in str(exc)
    else: raise AssertionError("empty context should fail")
