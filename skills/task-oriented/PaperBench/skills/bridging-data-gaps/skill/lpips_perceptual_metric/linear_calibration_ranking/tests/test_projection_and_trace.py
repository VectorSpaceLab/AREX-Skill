import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "calibrate_ranking.py"
spec = importlib.util.spec_from_file_location("calibrate_ranking", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_negative_initial_weights_are_projected_and_trace_fields_exist():
    items = [
        {"layers0": [0.1, 0.4], "layers1": [0.5, 0.2], "judge": 0},
        {"layers0": [0.7, 0.2], "layers1": [0.2, 0.8], "judge": 1},
    ]
    result = module.calibrate(items, initial_weights=[-1.0, 0.5], steps=5, learning_rate=0.1)
    assert "params_before" in result and "params_after" in result
    assert all(weight >= 0.0 for weight in result["params_before"])
    assert all(weight >= 0.0 for weight in result["params_after"])
