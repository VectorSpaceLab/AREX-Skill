#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import numpy as np


def randomized_nystrom(A, ell, seed=0):
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A must be a square matrix")
    n = A.shape[0]
    if not 1 <= ell <= n:
        raise ValueError("ell must satisfy 1 <= ell <= n")
    rng = np.random.default_rng(seed)
    omega = rng.standard_normal((n, ell))
    omega, _ = np.linalg.qr(omega, mode="reduced")
    Y = A @ omega
    eps = np.finfo(float).eps
    nu = eps * max(1.0, np.linalg.norm(Y, ord="fro"))
    retries = 0
    for multiplier in (1.0, 100.0, 10000.0):
        shift = nu * multiplier
        Y_shift = Y + shift * omega
        gram = omega.T @ Y_shift
        try:
            C = np.linalg.cholesky((gram + gram.T) / 2.0)
            break
        except np.linalg.LinAlgError:
            retries += 1
    else:
        raise np.linalg.LinAlgError("shifted sketch Gram matrix is not positive definite")
    B = np.linalg.solve(C, Y_shift.T).T
    U, singular_values, _ = np.linalg.svd(B, full_matrices=False)
    lambda_hat = np.maximum(singular_values ** 2 - shift, 0.0)
    order = np.argsort(lambda_hat)[::-1]
    U = U[:, order]
    lambda_hat = lambda_hat[order]
    diagnostics = {
        "n": int(n),
        "ell": int(ell),
        "returned_rank": int(len(lambda_hat)),
        "shift": float(shift),
        "matvec_count": int(ell),
        "cholesky_retries": int(retries),
    }
    return U, lambda_hat, diagnostics


def approximation_error(A, U, lambda_hat):
    approx = U @ np.diag(lambda_hat) @ U.T
    return float(np.linalg.norm(A - approx, ord="fro"))


def _self_test():
    diag = np.array([9.0, 4.0, 1.0, 0.25])
    A = np.diag(diag)
    U1, lam1, info1 = randomized_nystrom(A, 1, seed=1)
    U3, lam3, info3 = randomized_nystrom(A, 3, seed=1)
    assert U1.shape == (4, 1)
    assert U3.shape == (4, 3)
    assert np.all(lam3 >= -1e-12)
    assert np.allclose(U3.T @ U3, np.eye(3), atol=1e-10)
    assert info3["matvec_count"] == 3
    assert approximation_error(A, U3, lam3) <= approximation_error(A, U1, lam1) + 1e-8
    return {"ok": True, "error_rank_1": approximation_error(A, U1, lam1), "error_rank_3": approximation_error(A, U3, lam3)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-json", type=Path)
    parser.add_argument("--ell", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(_self_test(), indent=2))
        return 0
    if args.matrix_json is None or args.ell is None or args.output is None:
        parser.error("--matrix-json, --ell, and --output are required unless --self-test is used")
    A = np.asarray(json.loads(args.matrix_json.read_text())["A"], dtype=float)
    U, lambda_hat, diagnostics = randomized_nystrom(A, args.ell, args.seed)
    payload = {"U": U.tolist(), "lambda_hat": lambda_hat.tolist(), "diagnostics": diagnostics}
    args.output.write_text(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
