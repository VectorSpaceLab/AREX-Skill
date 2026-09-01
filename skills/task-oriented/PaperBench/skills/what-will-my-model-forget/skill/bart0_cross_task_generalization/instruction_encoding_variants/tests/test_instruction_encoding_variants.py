from instruction_encoding_variants import render_encoding

TASK = {
    "definition": "Generate a useful science question.",
    "prompt": "Write a question.",
    "things_to_avoid": "Do not copy the fact.",
    "emphasis": "The question must be answerable.",
    "positive_examples": [{"input": "Fact: Heat melts ice.", "output": "What melts ice?", "reason": "answerable"}],
    "negative_examples": [{"input": "Fact: Plants need light.", "output": "Do plants?", "reason": "vague"}],
}


def test_prompt_only_excludes_definition():
    encoded = render_encoding(TASK, "Fact: Gravity pulls objects.", "prompt")
    assert "Prompt:" in encoded["text"]
    assert "Definition:" not in encoded["text"]
    assert encoded["text"].endswith("output:")


def test_full_instruction_includes_examples_without_current_answer():
    encoded = render_encoding(TASK, "Fact: Gravity pulls objects.", "full_instruction")
    assert "Things to Avoid" in encoded["text"]
    assert "PositiveExample1" in encoded["text"]
    assert "What pulls objects?" not in encoded["text"]
