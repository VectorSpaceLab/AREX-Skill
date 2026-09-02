from integrated_gradients import integrated_gradients


def test_zero_delta_feature_has_zero_attribution():
    result = integrated_gradients(lambda p: [3.0, 4.0], [1, 2], [1, 0], 5)
    assert result['attributions'][0] == 0.0
    assert result['attributions'][1] == 8.0
