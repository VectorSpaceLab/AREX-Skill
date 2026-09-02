import importlib.util
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pcg.py"
spec = importlib.util.spec_from_file_location("pcg", SCRIPT)
pcg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcg)


def test_nystrom_pcg_beats_cg_on_synthetic_problem():
    A, b, x_true, mu, _ = pcg.synthetic_problem(n=64, seed=4)
    nys = pcg.nystrom_pcg_solve(A, b, mu, ell=14, tol=1e-8, maxiter=300, seed=5)
    plain = pcg.cg_solve(A, b, mu, tol=1e-8, maxiter=300)
    assert nys["converged"]
    assert nys["iterations"] < plain["iterations"]
    assert nys["relative_residuals"][-1] < 1e-8
    assert nys["mechanism_checks"]["randomized_nystrom_factorization_executed"]
    assert nys["mechanism_checks"]["preconditioner_applied"]
