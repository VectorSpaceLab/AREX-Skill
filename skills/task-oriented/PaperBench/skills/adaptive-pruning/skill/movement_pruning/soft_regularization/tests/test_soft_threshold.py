from soft_regularization import soft_movement_regularization

def test_threshold_keep_ratio_cannot_increase_under_regularizer():
    r = soft_movement_regularization([-.1, .1, 2.0], lambda_mvp=0.5, threshold=0.0, lr=0.5)
    d = r['threshold_diagnostics']
    assert d['keep_after'] <= d['keep_before']
