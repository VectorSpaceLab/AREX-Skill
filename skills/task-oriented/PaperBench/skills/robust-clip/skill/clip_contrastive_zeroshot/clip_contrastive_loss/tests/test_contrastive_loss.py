from contrastive_loss import symmetric_contrastive


def test_diagonal_pairs_have_good_accuracy():
    out = symmetric_contrastive([[1,0],[0,1]], [[1,0],[0,1]], logit_scale=10)
    assert out["retrieval_accuracy"] == 1.0
    assert out["loss"] < 0.01


def test_mismatched_pairs_worse_than_aligned():
    aligned = symmetric_contrastive([[1,0],[0,1]], [[1,0],[0,1]], 5)["loss"]
    swapped = symmetric_contrastive([[1,0],[0,1]], [[0,1],[1,0]], 5)["loss"]
    assert aligned < swapped
