from alice_decoding import copied_from_prompt, score_candidates, target_class


def test_false_negative_targets_benign_class():
    assert target_class("toxic", "false_negative") == "benign"
    assert target_class("benign", "false_positive") == "toxic"


def test_classifier_weight_can_select_lower_lm_candidate():
    candidates = [
        {"text": "fluent harmless continuation", "lm_logprob": -0.1, "classifier_logprobs": {"benign": -2.0, "toxic": -0.1}},
        {"text": "subtle coded continuation", "lm_logprob": -1.2, "classifier_logprobs": {"benign": -0.05, "toxic": -4.0}},
    ]
    result = score_candidates("prompt about a group", candidates, "toxic", "false_negative", lambda_l=0.2, lambda_c=0.8)
    assert result["selected"]["text"] == "subtle coded continuation"
    assert result["mechanism_checks"]["weighted_alice_score_used"] is True


def test_prompt_copy_detection():
    assert copied_from_prompt("group prompt", "group prompt")


def test_prompt_copy_candidate_cannot_win_even_with_high_scores():
    candidates = [
        {"text": "group prompt", "lm_logprob": 0.0, "classifier_logprobs": {"benign": 0.0, "toxic": -9.0}},
        {"text": "new subtle continuation", "lm_logprob": -2.0, "classifier_logprobs": {"benign": -0.1, "toxic": -4.0}},
    ]
    result = score_candidates("group prompt", candidates, "toxic", "false_negative", lambda_l=0.5, lambda_c=0.5)
    assert result["trace"][0]["excluded"] is True
    assert result["selected"]["text"] == "new subtle continuation"
