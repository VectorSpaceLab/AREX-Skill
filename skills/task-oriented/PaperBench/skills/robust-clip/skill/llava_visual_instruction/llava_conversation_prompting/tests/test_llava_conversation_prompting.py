from llava_conversation_prompting import format_llava_prompt

def test_prompt_has_image_and_no_answer_leakage():
    item = {"human_prompt":"What is shown?", "assistant_answer":"a plant"}
    out = format_llava_prompt(item, include_answer=True)
    assert "<image>" in out["user_prompt"]
    assert "a plant" not in out["user_prompt"]
    assert "a plant" in out["training_prompt"]
    assert out["answer_withheld_from_user"] is True


def test_visible_choices_are_not_assistant_leakage():
    item = {"human_prompt":"Choose A. sunlight or B. suitcase", "assistant_answer":"A. sunlight"}
    out = format_llava_prompt(item, include_answer=True)
    assert "A. sunlight" in out["user_prompt"]
    assert out["training_prompt"].endswith("A. sunlight")
