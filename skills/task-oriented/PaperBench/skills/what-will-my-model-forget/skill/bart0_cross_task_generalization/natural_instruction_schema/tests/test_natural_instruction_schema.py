from natural_instruction_schema import build_instruction_record


def test_builds_qasc_like_record():
    record = build_instruction_record(
        task_id="task040_qasc_question_generation",
        dataset="QASC",
        category="question_generation",
        definition="Generate a question from a science fact.",
        prompt="Write a question.",
        instances=[{"input": "Fact: Heat melts ice.", "output": "What melts ice?"}],
    )
    assert record["task_id"] == "task040_qasc_question_generation"
    assert record["negative_examples"] == []


def test_rejects_missing_instances():
    try:
        build_instruction_record("x", "QASC", "question_generation", prompt="Write a question.")
    except ValueError as exc:
        assert "instance" in str(exc)
    else:
        raise AssertionError("missing instances should fail")
