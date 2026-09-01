from induction_detect import predict_induction


def test_most_recent_previous_match_is_used():
    out = predict_induction(['A','B','A','C','A','C'])
    ex = [e for e in out['examples'] if e['destination_position'] == 4][0]
    assert ex['source_position'] == 2
    assert ex['predicted_next'] == 'C'
    assert ex['correct'] is True
