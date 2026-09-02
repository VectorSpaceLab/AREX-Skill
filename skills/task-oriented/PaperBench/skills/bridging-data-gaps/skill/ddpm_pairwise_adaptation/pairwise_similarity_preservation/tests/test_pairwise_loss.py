from pairwise_loss import pairwise_distributions, pairwise_kl_loss


def test_identical_geometry_has_zero_loss():
    batch = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    result = pairwise_kl_loss(batch, batch)
    assert abs(result["loss"]) < 1e-12


def test_changed_geometry_has_positive_loss():
    source = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    adapted = [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
    result = pairwise_kl_loss(source, adapted)
    assert result["loss"] > 0.001


def test_self_pairs_are_excluded():
    rows = pairwise_distributions([[1.0], [2.0], [3.0]])
    for row in rows:
        assert row["anchor"] not in row["neighbors"]
        assert len(row["probabilities"]) == 2

def test_batch_size_one_is_rejected():
    try:
        pairwise_distributions([[1.0, 0.0]])
    except ValueError as exc:
        assert "batch size" in str(exc)
    else:
        raise AssertionError("batch size one should be rejected")
