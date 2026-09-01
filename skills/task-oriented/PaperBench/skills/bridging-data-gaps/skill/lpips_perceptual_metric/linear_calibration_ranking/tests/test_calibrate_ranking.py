import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "calibrate_ranking.py"
spec = importlib.util.spec_from_file_location("calibrate_ranking", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_calibration_keeps_weights_non_negative_and_updates():
    items = [
        {"id": "a", "layers0": [0.1, 0.9], "layers1": [0.5, 0.2], "judge": 0},
        {"id": "b", "layers0": [0.7, 0.2], "layers1": [0.2, 0.8], "judge": 1},
        {"id": "c", "layers0": [0.2, 0.8], "layers1": [0.6, 0.1], "judge": 0},
    ]
    result = module.calibrate(items, initial_weights=[0.1, 1.0], steps=20, learning_rate=0.5)
    assert all(weight >= 0.0 for weight in result["params_after"])
    assert result["optimizer_step_executed"]
    assert result["after"]["loss"] <= result["before"]["loss"]


def test_invalid_layer_lengths_fail():
    try:
        module.calibrate([{"layers0": [0.1], "layers1": [0.2, 0.3], "judge": 0}])
    except ValueError:
        return
    raise AssertionError("mismatched layer lengths should fail")
