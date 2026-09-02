from c2st_metric import c2st_accuracy


def test_identical_samples_score_half():
    xs = [[0.0, 0.0], [1.0, 1.0], [-1.0, -1.0], [0.5, -0.5]]
    out = c2st_accuracy(xs, xs)
    assert out['c2st_accuracy'] == 0.5
    assert out['accepted'] is True


def test_shifted_samples_are_detected():
    ref = [[0.0], [0.1], [-0.1], [0.2], [-0.2], [0.05]]
    app = [[2.0], [2.1], [1.9], [2.2], [1.8], [2.05]]
    out = c2st_accuracy(ref, app)
    assert out['c2st_accuracy'] > 0.8
    assert out['accepted'] is False


def test_empty_samples_are_rejected():
    try:
        c2st_accuracy([], [[0.0]])
    except ValueError as exc:
        assert 'non-empty' in str(exc)
    else:
        raise AssertionError('expected ValueError')
