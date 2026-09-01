from cic_loss import evaluate_cic_loss, identity_weights


def test_rejects_missing_negative_batch():
    try:
        evaluate_cic_loss([[1, 2]], [[1]], identity_weights(1, 1), [[1], [0]], temperature=0.5)
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:
        raise AssertionError("expected ValueError")
