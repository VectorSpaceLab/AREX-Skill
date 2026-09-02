from matrix import compare, best

def test_error_improvement_signs():
    rows=[{"intervention":"baseline","shift":0.6},{"intervention":"aug","shift":0.4}]
    result=compare(rows,"baseline","lower_is_better")
    assert result[1]["deltas"]["shift"] == 0.19999999999999996
    assert result[1]["signs"]["shift"] == "+"
    assert best(rows,"shift","lower_is_better") == "aug"
