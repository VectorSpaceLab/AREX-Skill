import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "evaluate_2afc.py"
spec = importlib.util.spec_from_file_location("evaluate_2afc", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_accuracy_and_tie_rule():
    result = module.evaluate_precomputed([
        {"id": "mild", "d0": 0.1, "d1": 0.9, "judge": 0},
        {"id": "severe", "d0": 0.9, "d1": 0.1, "judge": 1},
        {"id": "tie", "d0": 0.5, "d1": 0.5, "judge": 0},
    ])
    assert result["accuracy"] == 1.0
    assert result["items"][2]["prediction"] == 0


def test_rejects_invalid_label():
    try:
        module.evaluate_precomputed([{"d0": 0.1, "d1": 0.2, "judge": 3}])
    except ValueError:
        return
    raise AssertionError("invalid labels should fail")
