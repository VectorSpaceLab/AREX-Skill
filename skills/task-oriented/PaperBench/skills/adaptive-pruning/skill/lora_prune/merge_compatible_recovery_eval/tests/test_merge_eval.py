from merge_eval import evaluate_merge_compatibility, merge_weights


def test_merge_and_explicit_predictions_match():
    x = [[1.0, 0.0], [0.0, 1.0]]
    y = [[1.0, 0.0], [0.0, 1.0]]
    w0 = [[1.0, 0.0], [0.0, 1.0]]
    b = [[0.1], [0.2]]
    a = [[0.3, -0.1]]
    out = evaluate_merge_compatibility(x, y, w0, b, a, [1, 0], baseline_loss=2.0)
    assert out["mechanism_checks"]["merge_equivalence_passed"] is True
    assert out["mechanism_checks"]["structured_mask_applied"] is True
    assert out["relative_improvement_vs_baseline"] is not None


def test_merge_formula():
    merged = merge_weights([[1.0]], [[2.0]], [[3.0]])
    assert merged == [[7.0]]
