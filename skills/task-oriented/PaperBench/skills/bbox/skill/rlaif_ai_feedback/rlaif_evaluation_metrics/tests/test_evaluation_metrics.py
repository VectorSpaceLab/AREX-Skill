from evaluation_metrics import alignment_accuracy, harmless_rate, target_consistency, win_rate


def test_alignment_skips_ties_and_scores_argmaxes():
    result = alignment_accuracy(
        [
            {"preference": [0.9, 0.1], "human_label": 1},
            {"preference": [0.2, 0.8], "human_label": 1},
            {"preference": [0.5, 0.5], "human_label": 2},
        ]
    )
    assert result["alignment_count"] == 2
    assert result["alignment_ties"] == 1
    assert result["alignment_accuracy"] == 0.5


def test_win_rate_for_named_policy():
    result = win_rate([{"winner": "RLAIF"}, {"winner": "SFT"}, {"winner": "RLAIF"}], "RLAIF")
    assert result["win_rate"] == 2 / 3


def test_harmless_rate_average():
    result = harmless_rate([{"harmless": True}, {"harmless": False}, {"harmless": True}])
    assert result["harmless_rate"] == 2 / 3


def test_target_consistency_detects_match_and_mismatch():
    plan = {"dataset": "proxy", "metric": "alignment_accuracy", "paper_value": 0.742}
    recovery = {"dataset": "proxy", "metric": "alignment_accuracy", "paper_value": 0.742}
    assert target_consistency(plan, recovery)["target_consistency_ok"] is True
    recovery_bad = {"dataset": "other", "metric": "alignment_accuracy", "paper_value": 0.742}
    assert target_consistency(plan, recovery_bad)["target_consistency_ok"] is False
