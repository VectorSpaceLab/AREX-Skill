from compose_scores import compose_score


def test_single_condition_reduces_to_condition_score():
    result = compose_score([2.0], [[-3.0]], progress=1.0)
    assert result["prior_correction"] == [-0.0]
    assert result["composed_score"] == [-3.0]


def test_standard_normal_prior_correction_sign():
    result = compose_score([2.0], [[1.0], [1.5]], progress=0.5)
    assert result["prior_correction"] == [1.0]
    assert result["composed_score"] == [3.5]


def test_pf_npse_uses_subset_count():
    result = compose_score([1.0], [[0.2], [0.3]], progress=1.0, condition_count=2, mode="pf_npse")
    assert result["condition_count"] == 2
    assert result["composed_score"] == [1.5]
