from induction_detect import predict_induction


def test_repeated_sequence_induction_predictions():
    out = predict_induction(['A','B','C','A','B','C','A','B'])
    assert out['applicable_count'] == 4
    assert out['accuracy'] == 1.0
    assert out['mechanism_checks']['repeated_token_predictions_correct'] is True


def test_no_repetition_has_no_applicable_cases():
    out = predict_induction(['A','B','C'])
    assert out['applicable_count'] == 0
    assert out['accuracy'] == 0.0
