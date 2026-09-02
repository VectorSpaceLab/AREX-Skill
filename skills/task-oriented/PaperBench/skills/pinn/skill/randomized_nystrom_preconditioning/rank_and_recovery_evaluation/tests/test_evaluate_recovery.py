import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_recovery.py"
spec = importlib.util.spec_from_file_location("evaluate_recovery", SCRIPT)
evaluate_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate_recovery)


def test_choose_rank_caps_theoretical_rank():
    rank = evaluate_recovery.choose_rank([100.0, 10.0, 1.0, 0.1], 0.5, rank_cap=3)
    assert rank["selected_rank"] == 3
    assert rank["effective_dimension"] > 0


def test_evaluate_trace_accepts_and_rejects():
    mechanism = {"randomized_nystrom_factorization_executed": True, "preconditioner_applied": True, "pcg_iterations_executed": True}
    condition = {"condition_A_mu": 100.0, "condition_preconditioned": 5.0}
    accepted = evaluate_recovery.evaluate_trace({"iterations": 40}, {"iterations": 8, "converged": True, "relative_residuals": [1.0, 1e-9]}, condition, mechanism)
    rejected = evaluate_recovery.evaluate_trace({"iterations": 6}, {"iterations": 8, "converged": True, "relative_residuals": [1.0, 1e-9]}, condition, mechanism)
    assert accepted["ok"]
    assert not rejected["ok"]
