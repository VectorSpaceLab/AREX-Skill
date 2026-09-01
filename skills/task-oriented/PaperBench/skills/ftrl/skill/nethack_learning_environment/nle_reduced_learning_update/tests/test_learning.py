from learning import one_step_update

def test_update_changes_params_and_reduces_loss():
    out=one_step_update({"staircase_visible":1,"gold_visible":1}, reward=1.0, lr=0.1)
    assert out["optimizer_state_changed"] is True
    assert out["params_before"] != out["params_after"]
    assert out["loss_after"] < out["loss_before"]
