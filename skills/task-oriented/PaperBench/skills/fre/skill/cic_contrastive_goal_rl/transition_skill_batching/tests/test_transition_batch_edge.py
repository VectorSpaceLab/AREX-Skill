from transition_batch import deterministic_synthetic_batch


def test_rejects_too_small_synthetic_batch():
    try:
        deterministic_synthetic_batch(batch_size=1)
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:
        raise AssertionError("expected ValueError")
