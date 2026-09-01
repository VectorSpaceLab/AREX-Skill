import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_gradient.py"
spec = importlib.util.spec_from_file_location("score_gradient", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_score_gradient_matches_hand_calculation():
    result = module.estimate_score_gradient(
        logp=[-1.0, -2.0, -3.0],
        logq=[-2.0, -2.5, -4.0],
        score=[[1.0, 2.0], [0.0, 1.0], [-1.0, 0.5]],
    )
    assert result["learning_signal"] == [1.0, 0.5, 1.0]
    assert result["gradient_terms"] == [[1.0, 2.0], [0.0, 0.5], [-1.0, 0.5]]
    assert result["gradient_estimate"] == [0.0, 1.0]
    assert result["diagnostics"]["finite"] is True


def test_rejects_mismatched_samples():
    try:
        module.estimate_score_gradient([1.0], [1.0, 2.0], [0.0])
    except ValueError as exc:
        assert "same sample count" in str(exc)
    else:
        raise AssertionError("expected ValueError")
