from lora_importance import lora_guided_importance


def test_formula_and_no_base_gradient():
    w0 = [[1.0, 2.0], [3.0, 4.0]]
    b = [[0.5], [1.0]]
    a = [[2.0, -1.0]]
    gb = [[0.1], [0.2]]
    ga = [[0.3, -0.4]]
    out = lora_guided_importance(w0, b, a, gb, ga)
    # grad approx = gb@a + b@ga - gb@ga
    expected_grad00 = 0.1 * 2.0 + 0.5 * 0.3 - 0.1 * 0.3
    expected_merged00 = 1.0 + 0.5 * 2.0
    assert abs(out["importance"][0][0] - (expected_grad00 * expected_merged00) ** 2) < 1e-12
    assert out["diagnostics"]["uses_base_gradients"] is False


def test_zero_gradients_zero_importance():
    out = lora_guided_importance([[1.0]], [[2.0]], [[3.0]], [[0.0]], [[0.0]])
    assert out["importance"] == [[0.0]]


def test_shape_mismatch_raises():
    try:
        lora_guided_importance([[1.0, 2.0]], [[1.0]], [[1.0]], [[1.0]], [[1.0]])
    except ValueError:
        return
    raise AssertionError("expected ValueError")
