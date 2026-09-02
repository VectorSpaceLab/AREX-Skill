from eval_protocol import accuracy, select_candidate, pooling_warnings


def test_accuracy():
    assert accuracy([1, 0, 1], [1, 1, 1]) == 2 / 3


def test_selects_by_validation_then_efficiency():
    candidates = [
        {"name": "large", "val_predictions": [1, 1], "val_labels": [1, 1], "test_predictions": [0], "test_labels": [1], "trainable_parameters": 20, "backbone_parameters": 100, "prompt_tokens": 5, "pooling": "cls"},
        {"name": "small", "val_predictions": [1, 1], "val_labels": [1, 1], "test_predictions": [1], "test_labels": [1], "trainable_parameters": 10, "backbone_parameters": 100, "prompt_tokens": 2, "pooling": "cls"},
    ]
    result = select_candidate(candidates)
    assert result["selected_name"] == "small"
    assert result["test_accuracy"] == 1.0


def test_warns_on_prompt_pooling():
    assert pooling_warnings("prompt_pool")
    assert pooling_warnings("cls") == []
