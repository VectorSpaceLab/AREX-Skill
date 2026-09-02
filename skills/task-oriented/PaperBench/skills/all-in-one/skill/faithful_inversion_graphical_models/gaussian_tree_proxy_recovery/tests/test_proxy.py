from gaussian_tree_proxy import run_reduced_training


def test_reduced_training_changes_params_and_reduces_loss():
    contracts = [
        {"variable": "x2", "feature_order": ["x3", "x4", "x5", "x6"]},
        {"variable": "x1", "feature_order": ["x2", "x3", "x4"]},
        {"variable": "x0", "feature_order": ["x1", "x2"]},
    ]
    result = run_reduced_training(contracts, depth=3, sample_count=6, seed=1712, learning_rate=0.08)
    trace = result["training_trace"]
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_before"] != trace["params_after"]
    assert result["metrics"]["mechanism_score"] == 1.0
    assert result["mechanism_checks"]["reduced_training_executed"] is True
    assert result["mechanism_checks"]["training_step_executed"] is False


def test_generated_data_has_observed_leaves():
    contracts = [{"variable": "x0", "feature_order": ["x1", "x2"]}]
    result = run_reduced_training(contracts, depth=3, sample_count=2, seed=7, learning_rate=0.02)
    data = result["data_item"]
    assert data["observed"] == ["x3", "x4", "x5", "x6"]
    assert all(name in data["samples"][0]["values"] for name in data["observed"])


def test_observed_parent_features_improve_reduced_training_signal():
    full_contracts = [
        {"variable": "x2", "feature_order": ["x3", "x4", "x5", "x6"]},
        {"variable": "x1", "feature_order": ["x2", "x3", "x4"]},
        {"variable": "x0", "feature_order": ["x1", "x2"]},
    ]
    ablated_contracts = [
        {"variable": "x2", "feature_order": []},
        {"variable": "x1", "feature_order": ["x2"]},
        {"variable": "x0", "feature_order": ["x1", "x2"]},
    ]
    full = run_reduced_training(full_contracts, depth=3, sample_count=8, seed=1712, learning_rate=0.08)
    ablated = run_reduced_training(ablated_contracts, depth=3, sample_count=8, seed=1712, learning_rate=0.08)
    assert full["metrics"]["loss_reduction_fraction"] > ablated["metrics"]["loss_reduction_fraction"]
