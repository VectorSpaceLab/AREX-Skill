from pope_answer_evaluator import evaluate_answers, normalize_answer


def test_normalize_sentence_answers():
    assert normalize_answer("No, there is not a dog in the image.") == "no"
    assert normalize_answer("not visible in this image") == "no"
    assert normalize_answer("Yes, there is a cat.") == "yes"
    assert normalize_answer("The object is visible.") == "yes"


def test_metrics_and_confusion():
    answers = [
        {"answer": "Yes."},
        {"answer": "No, not present."},
        {"answer": "Yes."},
        {"answer": "No."},
    ]
    labels = [{"label": "yes"}, {"label": "no"}, {"label": "no"}, {"label": "yes"}]
    result = evaluate_answers(answers, labels)
    assert result["confusion"] == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    assert result["accuracy"] == 0.5
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["yes_ratio"] == 0.5
