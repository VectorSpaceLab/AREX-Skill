from tent_step import run_tent_proxy


def test_entropy_step_reduces_entropy_and_changes_params():
    trace = run_tent_proxy([-2.0, -1.5, 1.5, 2.0], [0, 0, 1, 1], lr=1.0, steps=3)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["params_after"] != trace["params_before"]
    assert trace["optimizer_state_changed"] is True


def test_labels_are_only_for_metric():
    trace = run_tent_proxy([-2.0, 2.0], None, lr=1.0, steps=1)
    assert trace["accuracy_before"] is None
    assert trace["loss_after"] < trace["loss_before"]
