import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from prompt_formatter import format_example

def test_direct_keeps_hidden_answer_out_of_prompt():
    record=format_example({"instruction":"Classify as positive or negative","input":"great","answer":"positive"})
    assert record["completion"] == "positive"
    assert record["metadata"]["answer_separated_from_prompt"] is True

def test_cot_completion_contains_rationale_only_after_prompt():
    record=format_example({"instruction":"Add","input":"1+1","answer":"2","rationale":"One plus one equals two."}, mode="cot")
    assert "Therefore" in record["completion"]
    assert "One plus one" not in record["prompt"]
    assert record["metadata"]["cot_used"] is True
if __name__ == "__main__": test_direct_keeps_hidden_answer_out_of_prompt(); test_cot_completion_contains_rationale_only_after_prompt()
