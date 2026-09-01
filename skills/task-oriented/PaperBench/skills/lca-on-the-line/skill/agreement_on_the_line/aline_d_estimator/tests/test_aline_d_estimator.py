import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "aline_d_estimator.py"
spec = importlib.util.spec_from_file_location("aline_d_estimator", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_aline_d_solves_pairwise_system():
    stats = {
        "models": ["a", "b", "c"],
        "id_accuracy_probit": {"a": 0.0, "b": 0.0, "c": 0.0},
        "pairwise": {
            "a::b": {"models": ["a", "b"]},
            "a::c": {"models": ["a", "c"]},
            "b::c": {"models": ["b", "c"]},
        },
        "pairwise_probit": {
            "a::b": {"id_agreement": 0.0, "ood_agreement": 0.1},
            "a::c": {"id_agreement": 0.0, "ood_agreement": 0.2},
            "b::c": {"id_agreement": 0.0, "ood_agreement": 0.3},
        },
    }
    estimate = mod.estimate_aline_d(stats, {"slope": 1.0, "intercept": 0.0})
    assert estimate["equation_count"] == 3
    assert abs(estimate["predicted_ood_accuracy_probit"]["a"] - 0.0) < 1e-9
    assert abs(estimate["predicted_ood_accuracy_probit"]["b"] - 0.2) < 1e-9
    assert abs(estimate["predicted_ood_accuracy_probit"]["c"] - 0.4) < 1e-9
