from diagnostics import relative_l2, summarize


def test_relative_error_orders_predictions():
    target = [[0.0, 1.0], [0.0, -1.0]]
    exact = [[0.0, 1.0], [0.0, -1.0]]
    shifted = [[0.5, 1.0], [0.0, -0.5]]
    constant = [[0.0, 0.0], [0.0, 0.0]]
    assert relative_l2(exact, target) == 0.0
    assert relative_l2(shifted, target) < relative_l2(constant, target)


def test_summarize_records_loss_improvement():
    summary = summarize([[1.0]], [[1.0]], loss_trace=[2.0, 1.0])
    assert summary["loss_improved"] is True
    assert summary["high_relative_error"] is False
