import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "harness_utils.py"
spec = importlib.util.spec_from_file_location("harness_utils", script)
harness_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness_utils)


def test_synthetic_clusters_are_separated():
    frequent_train, frequent_eval, rare_eval = harness_utils.synthetic_clusters()
    assert len(frequent_train) >= len(frequent_eval)
    assert min(row[0] for row in rare_eval) > max(row[0] for row in frequent_eval)
    target, predictor = harness_utils.default_matrices()
    assert target != predictor
    assert len(target) == len(predictor)
