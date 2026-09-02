from enhanced_mask_decoder import score_candidates


def test_emd_breaks_relative_only_tie():
    candidates = [
        {"label": "A", "text": "store", "absolute_position": 2},
        {"label": "B", "text": "mall", "absolute_position": 8},
    ]
    relative_scores = {"A": 1.0, "B": 1.0}
    result = score_candidates(candidates, relative_scores, target_position=8, emd_weight=1.0)
    assert result["predicted_without_emd"] == "A"
    assert result["predicted_label"] == "B"


def test_emd_score_is_separate_from_relative_score():
    candidates = [{"label": "A", "text": "answer", "absolute_position": 3}]
    result = score_candidates(candidates, {"A": 0.25}, target_position=3, emd_weight=0.5)
    score = result["scores"][0]
    assert score["relative_score"] == 0.25
    assert score["emd_score"] == 0.5
    assert score["logit"] == 0.75


def test_four_option_tie_records_no_emd_prediction():
    candidates = [
        {"label": "A", "text": "store", "absolute_position": 2},
        {"label": "B", "text": "mall", "absolute_position": 8},
        {"label": "C", "text": "park", "absolute_position": 4},
        {"label": "D", "text": "station", "absolute_position": 5},
    ]
    relative_scores = {"A": 1.0, "B": 1.0, "C": 0.8, "D": 0.8}
    result = score_candidates(candidates, relative_scores, target_position=8, emd_weight=1.0)
    assert result["predicted_without_emd"] == "A"
    assert result["predicted_label"] == "B"
    assert len(result["without_emd_scores"]) == 4
