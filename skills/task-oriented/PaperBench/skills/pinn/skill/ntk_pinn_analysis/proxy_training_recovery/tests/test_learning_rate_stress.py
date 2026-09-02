from proxy_train import run_proxy


def test_proxy_improvement_survives_smaller_learning_rate():
    trace = run_proxy(101.0, 1.01, 0.0025)
    assert trace["optimizer_state_changed"] is True
    assert trace["adaptive_loss_ratio_improvement"] > 0
