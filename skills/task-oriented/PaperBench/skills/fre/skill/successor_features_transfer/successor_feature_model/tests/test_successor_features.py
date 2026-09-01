import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "successor_features.py"
spec = importlib.util.spec_from_file_location("successor_features", SCRIPT)
sf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sf)


def test_successor_features_reweight_without_recompute():
    model = {
        "states": ["s0", "s1"],
        "actions": ["left", "right"],
        "feature_dim": 2,
        "transitions": {
            "s0": {
                "left": {"next_state": "s1", "features": [1.0, 0.0], "terminal": True},
                "right": {"next_state": "s1", "features": [0.0, 1.0], "terminal": True},
            },
            "s1": {
                "left": {"next_state": "s1", "features": [0.0, 0.0], "terminal": True},
                "right": {"next_state": "s1", "features": [0.0, 0.0], "terminal": True},
            },
        },
    }
    result = sf.compute_successor_features(model, {"s0": "left", "s1": "left"}, gamma=0.9)
    assert result["converged"]
    values_a = sf.values_from_successor_features(result["psi"], [2.0, -1.0])
    values_b = sf.values_from_successor_features(result["psi"], [-1.0, 3.0])
    assert values_a["s0"]["left"] == 2.0
    assert values_b["s0"]["right"] == 3.0


if __name__ == "__main__":
    test_successor_features_reweight_without_recompute()


def test_stochastic_transition_expectation_contract():
    model = {
        "states": ["s0", "s1"],
        "actions": ["a"],
        "feature_dim": 1,
        "transitions": {
            "s0": {"a": [
                {"next_state": "s1", "features": [1.0], "terminal": True, "prob": 0.25},
                {"next_state": "s1", "features": [3.0], "terminal": True, "prob": 0.75},
            ]},
            "s1": {"a": {"next_state": "s1", "features": [0.0], "terminal": True}},
        },
    }
    result = sf.compute_successor_features(model, {"s0": "a", "s1": "a"}, gamma=0.9)
    assert abs(result["psi"]["s0"]["a"][0] - 2.5) < 1e-9

