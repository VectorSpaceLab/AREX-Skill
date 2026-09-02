from mmlu_fewshot_prompting import build_prompt
def item(i, ans="A"):
    return {"subject":"law","question":f"q{i}?","choices":{"A":"a","B":"b","C":"c","D":"d"},"answer":ans}
def test_prompt_hides_test_answer():
    prompt, meta=build_prompt("law", [item(1),item(2)], item(99,"D"), 2)
    assert meta["shot_count"]==2
    assert prompt.count("Answer: A")==2
    assert "q99?" in prompt and "Answer: D" not in prompt
