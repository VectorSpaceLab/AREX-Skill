import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_ksd.py"
spec = importlib.util.spec_from_file_location("bootstrap_ksd", SCRIPT)
bootstrap_ksd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap_ksd)


def test_u_statistic_excludes_diagonal():
    matrix = [[100.0, 2.0], [4.0, 100.0]]
    assert abs(bootstrap_ksd.ksd_u_statistic(matrix) - 3.0) < 1e-12


def test_bootstrap_is_reproducible():
    matrix = [[0.0, 1.0, 0.5], [1.0, 0.0, 0.25], [0.5, 0.25, 0.0]]
    first = bootstrap_ksd.bootstrap_ksd_test(matrix, num_bootstrap=20, seed=7)
    second = bootstrap_ksd.bootstrap_ksd_test(matrix, num_bootstrap=20, seed=7)
    assert first["p_value"] == second["p_value"]
    assert first["bootstrap_scaled"] == second["bootstrap_scaled"]


def test_decision_matches_tail_probability_rule():
    matrix = [[0.0 if i == j else 2.0 for j in range(8)] for i in range(8)]
    result = bootstrap_ksd.bootstrap_ksd_test(matrix, alpha=0.2, num_bootstrap=200, seed=3)
    assert result["ksd_u"] == 2.0
    assert 0.0 <= result["p_value"] <= 1.0
    assert result["reject"] is (result["p_value"] < 0.2)
