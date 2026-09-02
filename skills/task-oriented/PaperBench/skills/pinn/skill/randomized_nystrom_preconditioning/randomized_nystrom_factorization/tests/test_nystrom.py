import importlib.util
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "nystrom.py"
spec = importlib.util.spec_from_file_location("nystrom", SCRIPT)
nystrom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nystrom)


def test_randomized_nystrom_contract():
    A = np.diag([16.0, 8.0, 2.0, 0.5, 0.1])
    U, lambda_hat, diagnostics = nystrom.randomized_nystrom(A, 3, seed=7)
    assert U.shape == (5, 3)
    assert lambda_hat.shape == (3,)
    assert diagnostics["matvec_count"] == 3
    assert np.all(lambda_hat >= 0.0)
    assert np.allclose(U.T @ U, np.eye(3), atol=1e-9)


def test_larger_rank_improves_approximation():
    A = np.diag([25.0, 9.0, 4.0, 1.0, 0.25])
    U1, lambda1, _ = nystrom.randomized_nystrom(A, 1, seed=3)
    U4, lambda4, _ = nystrom.randomized_nystrom(A, 4, seed=3)
    assert nystrom.approximation_error(A, U4, lambda4) <= nystrom.approximation_error(A, U1, lambda1) + 1e-8
