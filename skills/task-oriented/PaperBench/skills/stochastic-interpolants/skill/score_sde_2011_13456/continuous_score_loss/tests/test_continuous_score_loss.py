from continuous_score_loss import make_batch, step

def test_target_score_signs():
    batch = make_batch([0.0, 0.0], [0.25, 0.75], [0.5, -0.5])
    assert batch[0]["target_score"] < 0
    assert batch[1]["target_score"] > 0

def test_optimizer_reduces_loss():
    batch = make_batch([-1.0, 1.0], [0.2, 0.8], [0.4, -0.3])
    trace = step({"a": 0.0, "b": 0.0, "c": 0.0}, batch, lr=0.01)
    assert trace["params_before"] != trace["params_after"]
    assert trace["loss_after"] < trace["loss_before"]
