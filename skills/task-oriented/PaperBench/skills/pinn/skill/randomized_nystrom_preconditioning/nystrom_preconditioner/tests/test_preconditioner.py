import importlib.util
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preconditioner.py"
spec = importlib.util.spec_from_file_location("preconditioner", SCRIPT)
preconditioner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preconditioner)


def test_inverse_preconditioner_shape():
    U = np.eye(3, 2)
    y = preconditioner.apply_inverse_preconditioner(U, np.array([10.0, 2.0]), 0.5, np.ones(3))
    assert y.shape == (3,)
    assert y[2] == 1.0


def test_condition_number_reduction():
    A = np.diag([200.0, 40.0, 2.0, 1.0])
    U = np.eye(4, 2)
    stats = preconditioner.dense_condition_numbers(A, U, np.array([200.0, 40.0]), 0.2)
    assert stats["condition_preconditioned"] < stats["condition_A_mu"]
