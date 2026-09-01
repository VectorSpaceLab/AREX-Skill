from cot_prompt_templates import build_prompt


EXEMPLARS = [
    {
        "question": "There are 15 trees. Later there are 21. How many were planted?",
        "reasoning": "There are 21 trees now and 15 before, so 21 - 15 = 6",
        "answer": "6",
    }
]


def test_standard_prompt_omits_reasoning():
    result = build_prompt(EXEMPLARS, "Target question?", "standard")
    assert "21 - 15 = 6" not in result.prompt
    assert "The answer is 6." in result.prompt
    assert result.metadata["reasoning_included"] is False


def test_chain_of_thought_reasoning_precedes_answer():
    result = build_prompt(EXEMPLARS, "Target question?", "chain_of_thought")
    assert result.prompt.index("21 - 15 = 6") < result.prompt.index("The answer is 6")
    assert result.metadata["reasoning_precedes_answer"] is True


def test_ablation_modes_are_distinct():
    equation = build_prompt(EXEMPLARS, "Target question?", "equation_only").prompt
    after = build_prompt(EXEMPLARS, "Target question?", "reasoning_after_answer").prompt
    assert equation != after
    assert after.index("The answer is 6") < after.index("Reasoning:")


def test_all_prompt_modes_remain_structurally_distinct():
    modes = ["standard", "chain_of_thought", "equation_only", "variable_compute_only", "reasoning_after_answer"]
    prompts = {mode: build_prompt(EXEMPLARS, "Target question?", mode) for mode in modes}
    assert len({result.prompt for result in prompts.values()}) == len(modes)
    assert prompts["reasoning_after_answer"].metadata["reasoning_precedes_answer"] is False
