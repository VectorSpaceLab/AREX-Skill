import importlib.util
import math
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "agreement_statistics.py"
spec = importlib.util.spec_from_file_location("agreement_statistics", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_statistics_and_finite_probit():
    table = {
        "models": ["a", "b", "c"],
        "id_labels": [0, 1, 1, 0],
        "id_predictions": {"a": [0, 1, 1, 0], "b": [0, 1, 0, 0], "c": [1, 1, 1, 0]},
        "ood_predictions": {"a": [0, 1, 0, 1], "b": [0, 0, 0, 1], "c": [1, 1, 0, 1]},
        "evaluation_only": {"ood_labels": [0, 1, 0, 1]},
    }
    stats = mod.compute_statistics(table)
    assert stats["id_accuracy"]["a"] == 1.0
    assert stats["pairwise"]["a::b"]["id_agreement"] == 0.75
    assert stats["pairwise"]["a::c"]["ood_agreement"] == 0.75
    assert math.isfinite(stats["id_accuracy_probit"]["a"])
