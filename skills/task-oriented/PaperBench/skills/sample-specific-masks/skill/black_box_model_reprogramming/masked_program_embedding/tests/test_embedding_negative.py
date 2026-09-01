from masked_embedding import embed_sample


def test_sample_larger_than_canvas_is_rejected():
    try:
        embed_sample([[1.0, 2.0], [3.0, 4.0]], (1, 1), (0, 0))
    except ValueError as exc:
        assert "does not fit" in str(exc)
    else:
        raise AssertionError("oversized target sample should be rejected")
