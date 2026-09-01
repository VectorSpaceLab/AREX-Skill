from mmlu_item_schema import validate_item, canonical_label, format_question
def test_validate_and_format():
    item={"subject":"abstract algebra","question":"2+2?","choices":{"A":"3","B":"4","C":"5","D":"6"},"answer":"b"}
    assert validate_item(item)["answer"]=="B"
    assert "Answer:" in format_question(item) and "Answer: B" not in format_question(item)
def test_reject_bad_options():
    try: validate_item({"subject":"x","question":"q","choices":{"A":"a"},"answer":"A"})
    except ValueError: return
    assert False
