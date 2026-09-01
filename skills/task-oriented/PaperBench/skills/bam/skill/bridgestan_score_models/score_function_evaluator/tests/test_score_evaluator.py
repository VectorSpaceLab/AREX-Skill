import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_evaluator.py"
spec = importlib.util.spec_from_file_location("score_evaluator", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _contract():
    return {
        "parameters": [{"name": "theta", "type": "real", "lower": 0.0, "upper": 1.0}],
        "model_terms": [
            {"lhs": "theta", "distribution": "beta", "args": ["1", "1"]},
            {"lhs": "y", "distribution": "bernoulli", "args": ["theta"]},
        ],
    }


def test_score_derivatives_match_finite_difference():
    data = {"N": 4, "y": [1, 0, 1, 1]}
    for z in (-1.1, 0.4):
        result = mod.evaluate_score(_contract(), data, z)
        assert all(result["checks"].values())
        assert 0.0 < result["theta"] < 1.0
        assert result["sample_count"] == 4


if __name__ == "__main__":
    test_score_derivatives_match_finite_difference()
