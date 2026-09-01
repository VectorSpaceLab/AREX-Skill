from merge_eval import evaluate_merge_compatibility


def test_dense_unstructured_mask_flag_stays_false():
    out = evaluate_merge_compatibility(
        [[1.0, 0.0]],
        [[1.0, 0.0]],
        [[1.0, 0.0], [0.0, 1.0]],
        [[0.1], [0.2]],
        [[0.3, -0.1]],
        [1, 0],
        1.0,
    )
    assert out["mechanism_checks"]["dense_unstructured_mask_used"] is False
    assert out["mechanism_checks"]["structured_mask_applied"] is True
