from reduced_instruction_training_evaluation import rouge_l, train_one_step, choose_prediction


def test_rouge_l_boundaries():
    assert rouge_l("What melts ice?", "What melts ice?") == 1.0
    assert rouge_l("", "What melts ice?") == 0.0


def test_training_changes_parameters_and_selects_question():
    params = {"instruction_overlap": 0.0, "input_overlap": 0.0, "question_bonus": 0.0, "copy_penalty": 0.0}
    item = {"encoding": "Prompt: Write a question. input: Fact: Heat melts ice. output:", "input": "Fact: Heat melts ice.", "reference": "What melts ice?", "distractor": "Heat melts ice"}
    trace = train_one_step(item, params)
    assert trace["params_before"] != trace["params_after"]
    pred = choose_prediction(["Heat melts ice", "What melts ice?"], item["encoding"], item["input"], trace["params_after"])
    assert pred == "What melts ice?"
