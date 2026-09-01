from movement_scores import update_movement_scores

def test_zero_weight_is_neutral_not_away():
    r = update_movement_scores([0.0], [0.0], [-10.0], lr_score=1.0)
    assert r['diagnostics'][0]['away_from_zero'] is False
    assert r['updated_scores'] == [0.0]
