from msp import score_rows, softmax

def test_logits_score_rows():
    rows=[[3.0, 1.0], [0.0, 0.0]]
    scored=score_rows(rows, 'logits')
    assert scored[0]['predicted_class'] == 0
    assert scored[0]['msp'] > 0.88
    assert abs(scored[1]['msp'] - 0.5) < 1e-9

def test_probability_auto_mode():
    scored=score_rows([[0.2, 0.8]], 'auto')
    assert scored[0]['predicted_class'] == 1
    assert abs(scored[0]['msp'] - 0.8) < 1e-9

def test_invalid_empty_row():
    try:
        softmax([])
    except ValueError:
        return
    raise AssertionError('expected ValueError')


def test_large_logits_are_stable():
    scored=score_rows([[1000.0, 999.0, 998.0]], 'logits')
    assert scored[0]['predicted_class'] == 0
    assert 0.66 < scored[0]['msp'] < 0.67
