import importlib.util
from pathlib import Path

script_path = Path(__file__).resolve().parents[1] / "scripts" / "score_counterfactuals.py"
spec = importlib.util.spec_from_file_location("score_counterfactuals", script_path)
score_counterfactuals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_counterfactuals)


def test_score_removal_sets_sums_weights():
    weights = [0.5, -0.2, 0.9, 0.1]
    removal_sets = [[0, 2], [1], [], [2, 3]]
    result = score_counterfactuals.score_removal_sets(weights, removal_sets, [1.4, -0.2, 0.0, 1.0])
    assert result["predicted_effects"] == [1.4, -0.2, 0, 1.0]
    assert result["ranked_indices_desc"][0] == 2
    assert result["effect_correlation"] > 0.999


def test_duplicate_index_rejected():
    try:
        score_counterfactuals.score_removal_sets([0.1, 0.2], [[1, 1]])
    except ValueError:
        return
    raise AssertionError("duplicate index should fail")


if __name__ == "__main__":
    test_score_removal_sets_sums_weights()
    test_duplicate_index_rejected()
