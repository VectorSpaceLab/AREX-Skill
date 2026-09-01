import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "evaluate_2afc.py"
spec = importlib.util.spec_from_file_location("evaluate_2afc", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_mixed_accuracy_records_failures():
    result = module.evaluate_precomputed([
        {"id": "correct", "d0": 0.1, "d1": 0.5, "judge": 0},
        {"id": "wrong", "d0": 0.1, "d1": 0.5, "judge": 1},
    ])
    assert result["accuracy"] == 0.5
    assert result["items"][1]["correct"] is False
