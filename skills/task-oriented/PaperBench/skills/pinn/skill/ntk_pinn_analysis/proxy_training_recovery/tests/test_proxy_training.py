from proxy_train import run_proxy


def test_proxy_training_updates_parameters_and_improves_balance():
    trace = run_proxy(101.0, 1.01, 0.005)
    assert trace["optimizer_state_changed"] is True
    assert trace["params_before"] != trace["params_after"]
    assert trace["adaptive_loss_ratio_improvement"] > 0
    assert trace["adaptive_weight"]["imbalance_gap"] < trace["equal_weight"]["imbalance_gap"]
