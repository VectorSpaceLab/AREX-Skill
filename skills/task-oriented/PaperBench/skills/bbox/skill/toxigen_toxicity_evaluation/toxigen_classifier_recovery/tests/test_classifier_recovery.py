from classifier_recovery import features, train_once


def test_feature_extractor_counts_cues():
    values = features("A coded toxic stereotype says Asian people are dangerous.")
    assert values[0] > 0.0
    assert values[2] > 0.0


def test_training_updates_parameters_and_loss():
    examples = [
        {"text": "Black families deserve fair respect.", "label": "benign"},
        {"text": "Asian community culture deserves support.", "label": "benign"},
        {"text": "A coded toxic stereotype calls Muslim people dangerous.", "label": "toxic"},
        {"text": "A hateful stereotype says women are inferior.", "label": "toxic"},
    ]
    result = train_once(examples, learning_rate=2.0, steps=5)
    assert result["params_before"] != result["params_after"]
    assert result["loss_after"] <= result["loss_before"]


def test_single_class_auc_is_none_but_training_trace_is_valid():
    examples = [
        {"text": "Black families deserve fair respect.", "label": "benign"},
        {"text": "Asian community culture deserves support.", "label": "benign"},
    ]
    result = train_once(examples, learning_rate=1.0, steps=1)
    assert result["auc_before"] is None
    assert result["auc_after"] is None
    assert "params_before" in result
    assert "params_after" in result
