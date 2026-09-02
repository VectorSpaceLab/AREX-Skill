from visual_projection_training_step import train_projection_step

def test_projection_step_lowers_loss_and_changes_params():
    trace = train_projection_step([1.0, 2.0], [1.0, 2.0], params=[0.0, 0.0], lr=0.2, steps=3)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_before"] != trace["params_after"]
    assert trace["optimizer_state_changed"] is True
