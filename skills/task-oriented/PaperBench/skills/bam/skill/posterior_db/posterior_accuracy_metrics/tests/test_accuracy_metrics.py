from accuracy_metrics import compute_accuracy


def test_computes_rmse_and_missing_parameters():
    approximate = [{"a": 1.0, "b": 2.0}, {"a": 3.0, "b": 4.0}]
    reference = {"a": 1.0, "b": 4.0, "c": 9.0}
    result = compute_accuracy(approximate, reference)
    assert round(result["mean_rmse"], 6) == 1.0
    assert result["missing_approximate"] == ["c"]
    assert result["per_parameter"]["a"]["approx_mean"] == 2.0
