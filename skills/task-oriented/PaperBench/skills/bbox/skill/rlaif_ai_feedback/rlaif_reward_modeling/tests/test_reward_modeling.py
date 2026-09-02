from reward_modeling import softmax2, train_pairwise


def test_soft_label_training_decreases_loss_and_changes_params():
    examples = [
        {
            "context": "alpha beta gamma delta epsilon",
            "response1": "alpha beta",
            "response2": "unrelated words",
            "preference": [0.85, 0.15],
        }
    ]
    result = train_pairwise(examples, steps=50, lr=0.7)
    assert result["loss_after"] < result["loss_before"]
    assert result["params_after"] != result["params_before"]
    assert result["optimizer_state_changed"] is True


def test_prediction_tracks_preferred_soft_label_argmax():
    examples = [
        {
            "context": "the monitor cost two thousand and the computer five thousand",
            "response1": "computer monitor cost details",
            "response2": "short unrelated",
            "preference": [0.9, 0.1],
        }
    ]
    result = train_pairwise(examples, steps=80, lr=0.8)
    assert result["predictions"][0]["predicted_label"] == 1


def test_softmax2_is_normalized():
    probs = softmax2(-3.0, 4.0)
    assert abs(sum(probs) - 1.0) < 1e-9
    assert probs[1] > probs[0]
