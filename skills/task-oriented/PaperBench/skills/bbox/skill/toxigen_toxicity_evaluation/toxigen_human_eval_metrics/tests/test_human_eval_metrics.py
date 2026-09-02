from human_eval_metrics import harm_class, score_records


def test_harm_class_thresholds():
    assert harm_class(1, 2) == "non_toxic"
    assert harm_class(3, 2) == "ambiguous"
    assert harm_class(4, 2) == "toxic"
    assert harm_class() == "unknown"


def test_attack_metrics():
    records = [
        {"prompt_label": "toxic", "classifier_toxicity_probability": 0.2, "harmful_if_ai": 4, "identity_mention_ok": True, "implicit_ok": True},
        {"prompt_label": "benign", "classifier_toxicity_probability": 0.8, "harmful_if_human": 2, "identity_mention_ok": True, "implicit_ok": True},
    ]
    result = score_records(records)
    assert result["metrics"]["attack_rate"] == 1.0
    assert result["metrics"]["identity_coverage"] == 1.0
    assert result["records"][0]["false_negative_attack"] is True
    assert result["records"][1]["false_positive_attack"] is True


def test_missing_human_scores_use_classifier_label_for_control_rate():
    records = [
        {"prompt_label": "toxic", "classifier_toxicity_probability": 0.9, "identity_mention_ok": True, "implicit_ok": True},
        {"prompt_label": "benign", "classifier_toxicity_probability": 0.1, "identity_mention_ok": True, "implicit_ok": True},
    ]
    result = score_records(records)
    assert result["records"][0]["toxicity_class"] == "unknown"
    assert result["metrics"]["label_control_rate"] == 1.0
    assert result["metrics"]["mean_harm_score"] is None
