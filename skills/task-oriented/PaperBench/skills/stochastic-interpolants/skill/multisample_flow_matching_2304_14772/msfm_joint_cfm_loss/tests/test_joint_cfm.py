import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "joint_cfm.py"
spec = importlib.util.spec_from_file_location("joint_cfm", MODULE_PATH)
joint_cfm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint_cfm)


def test_interpolation_velocity_and_zero_loss():
    states, velocities = joint_cfm.interpolate([[0.0], [2.0]], [[2.0], [4.0]], [0.0, 1.0])
    assert states == [[0.0], [4.0]]
    assert velocities == [[2.0], [2.0]]
    assert joint_cfm.mean_squared_loss([[2.0], [2.0]], velocities) == 0.0


def test_gradient_step_changes_parameters_and_reduces_loss():
    states, velocities = joint_cfm.interpolate([[0.0], [2.0]], [[2.0], [4.0]], 0.5)
    update = joint_cfm.gradient_step(states, velocities, {"weights": [0.0], "bias": [0.0]}, 0.1)
    assert update["optimizer_step_executed"] is True
    assert update["params_before"] != update["params_after"]
    assert update["loss_after"] < update["loss_before"]
