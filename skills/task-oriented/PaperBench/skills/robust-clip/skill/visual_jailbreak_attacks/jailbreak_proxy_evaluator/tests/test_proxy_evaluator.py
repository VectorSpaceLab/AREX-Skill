from proxy_evaluator import evaluate_proxy


def test_obedience_delta_and_category():
    target = {"metric": "obedience_delta", "paper_value": 0.1}
    protocol = {"heldout_prompts": [{"id": "h0", "category": "cat"}], "split_checks": {"heldout_distinct": True}}
    result = evaluate_proxy(target, protocol, {"h0": 0.1}, {"h0": 0.4}, {"visual_prompt_changed": True, "loss_decreased": True})
    assert round(result["metrics"]["obedience_delta"], 6) == 0.3
    assert result["category_metrics"]["cat"]["delta"] == 0.30000000000000004


def test_missing_score_rejected():
    target = {"metric": "obedience_delta", "paper_value": 0.1}
    protocol = {"heldout_prompts": [{"id": "h0"}], "split_checks": {"heldout_distinct": True}}
    try:
        evaluate_proxy(target, protocol, {}, {"h0": 0.2})
    except ValueError as exc:
        assert "missing scores" in str(exc)
    else:
        raise AssertionError("expected missing score rejection")


def test_subthreshold_delta_is_not_success():
    target = {"metric": "obedience_delta", "paper_value": 0.5}
    protocol = {"heldout_prompts": [{"id": "h0"}], "split_checks": {"heldout_distinct": True}}
    result = evaluate_proxy(target, protocol, {"h0": 0.2}, {"h0": 0.3}, {"visual_prompt_changed": True, "loss_decreased": True})
    assert result["mechanism_checks"]["proxy_threshold_met"] is False
