from visual_instruction_data_builder import build_instruction_item

def test_builds_grounded_reasoning_item():
    item = build_instruction_item("x", ["A red car is parked."], [{"label":"car", "bbox":[0,0,1,1]}], "reasoning")
    assert item["response_type"] == "reasoning"
    assert "car" in item["assistant_answer"]
    assert "assistant_answer" not in item["human_prompt"]

def test_requires_boxes():
    try:
        build_instruction_item("x", ["caption"], [], "conversation")
    except ValueError as exc:
        assert "boxes" in str(exc)
    else:
        raise AssertionError("expected ValueError")
