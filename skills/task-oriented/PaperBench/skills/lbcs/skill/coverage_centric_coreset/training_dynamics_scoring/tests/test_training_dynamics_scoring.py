from score_training_dynamics import compute_scores


def test_margin_forgetting_and_el2n():
    records = [
        {'index': 0, 'epoch': 0, 'label': 0, 'probabilities': [0.8, 0.2]},
        {'index': 0, 'epoch': 1, 'label': 0, 'probabilities': [0.4, 0.6]},
        {'index': 1, 'epoch': 0, 'label': 1, 'probabilities': [0.3, 0.7]},
    ]
    scores = compute_scores(records, num_classes=2, max_el2n_epoch=2)
    assert scores['indices'] == [0, 1]
    assert scores['correctness'] == [1, 1]
    assert scores['forgetting'] == [1, 0]
    assert round(scores['accumulated_margin'][0], 6) == 0.4
    assert scores['el2n'][0] > scores['el2n'][1]
