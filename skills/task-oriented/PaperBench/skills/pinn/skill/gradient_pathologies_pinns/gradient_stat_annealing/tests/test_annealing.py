from annealing import update_lambdas

def test_update_matches_algorithm():
    out = update_lambdas([2.0, -4.0], [[1.0, -1.0]], [1.0], alpha=0.5)
    assert out["lambda_hats"] == [4.0]
    assert out["updated_lambdas"] == [2.5]
    assert out["residual_max_abs_grad"] == 4.0
