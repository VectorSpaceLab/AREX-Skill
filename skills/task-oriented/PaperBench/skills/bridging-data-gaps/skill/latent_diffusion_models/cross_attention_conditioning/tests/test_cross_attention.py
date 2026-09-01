from cross_attention import cross_attention


def test_attention_rows_sum_to_one_and_shape_matches_features():
    identity = [[1.0, 0.0], [0.0, 1.0]]
    result = cross_attention([[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.5], [-0.5, 1.0]], identity, identity, identity)
    assert len(result["conditioned"]) == 2
    for row_sum in result["row_sums"]:
        assert abs(row_sum - 1.0) < 1e-9


def test_conditioning_tokens_change_output():
    identity = [[1.0, 0.0], [0.0, 1.0]]
    first = cross_attention([[1.0, 0.0]], [[1.0, 0.0], [0.0, 1.0]], identity, identity, identity)
    second = cross_attention([[1.0, 0.0]], [[-1.0, 0.0], [0.0, -1.0]], identity, identity, identity)
    assert first["conditioned"] != second["conditioned"]


def test_token_content_sensitivity_is_visible():
    identity = [[1.0, 0.0], [0.0, 1.0]]
    base = cross_attention([[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]], identity, identity, identity)
    changed = cross_attention([[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.25], [-0.5, 1.5]], identity, identity, identity)
    assert base["conditioned"] != changed["conditioned"]


def test_rejects_bad_matrix_shape():
    identity = [[1.0, 0.0], [0.0, 1.0]]
    try:
        cross_attention([[1.0]], [[1.0, 2.0]], identity, identity, identity)
    except ValueError as exc:
        assert "align" in str(exc) or "dimensions" in str(exc)
    else:
        raise AssertionError("expected ValueError")
