import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "optimizer.py"
spec = importlib.util.spec_from_file_location("optimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_adagrad_step_changes_parameters_in_gradient_direction():
    trace = module.optimizer_step([0.0, 1.0], [2.0, -1.0], method="adagrad", learning_rate=0.5)
    assert trace["params_after"][0] > trace["params_before"][0]
    assert trace["params_after"][1] < trace["params_before"][1]
    assert trace["optimizer_step_executed"] is True
    assert trace["state_after"] == [4.0, 1.0]


def test_scalar_step_matches_formula():
    trace = module.optimizer_step([1.0], [3.0], method="scalar", learning_rate=0.25)
    assert trace["params_after"] == [1.75]
