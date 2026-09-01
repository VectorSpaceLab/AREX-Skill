#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np


def validate_inputs(U, lambda_hat, mu):
    U = np.asarray(U, dtype=float)
    lambda_hat = np.asarray(lambda_hat, dtype=float)
    if U.ndim != 2 or lambda_hat.ndim != 1 or U.shape[1] != lambda_hat.shape[0]:
        raise ValueError("U must be n x r and lambda_hat must have length r")
    if lambda_hat.size == 0:
        raise ValueError("lambda_hat must be nonempty")
    if mu <= 0:
        raise ValueError("mu must be positive")
    if not np.allclose(U.T @ U, np.eye(U.shape[1]), atol=1e-6):
        raise ValueError("U columns must be approximately orthonormal")
    return U, np.maximum(lambda_hat, 0.0), float(mu)


def apply_inverse_preconditioner(U, lambda_hat, mu, r):
    U, lambda_hat, mu = validate_inputs(U, lambda_hat, mu)
    r = np.asarray(r, dtype=float)
    sigma = float(lambda_hat[-1] + mu)
    coeff = sigma / (lambda_hat + mu) - 1.0
    projected = U.T @ r
    return r + U @ (coeff[..., None] * projected if projected.ndim == 2 else coeff * projected)


def dense_condition_numbers(A, U, lambda_hat, mu):
    U, lambda_hat, mu = validate_inputs(U, lambda_hat, mu)
    A = np.asarray(A, dtype=float)
    A_mu = (A + mu * np.eye(A.shape[0]) + (A + mu * np.eye(A.shape[0])).T) / 2.0
    sigma = float(lambda_hat[-1] + mu)
    p_inv_eigs = sigma / (lambda_hat + mu)
    P_inv = np.eye(A.shape[0]) + U @ np.diag(p_inv_eigs - 1.0) @ U.T
    evals, evecs = np.linalg.eigh((P_inv + P_inv.T) / 2.0)
    sqrt_P_inv = evecs @ np.diag(np.sqrt(np.maximum(evals, 0.0))) @ evecs.T
    preconditioned = sqrt_P_inv @ A_mu @ sqrt_P_inv
    cond_A = float(np.linalg.cond(A_mu))
    cond_pre = float(np.linalg.cond((preconditioned + preconditioned.T) / 2.0))
    return {"condition_A_mu": cond_A, "condition_preconditioned": cond_pre, "reduction_factor": cond_A / cond_pre}


def _self_test():
    A = np.diag([100.0, 20.0, 1.0, 0.5])
    U = np.eye(4, 2)
    lambda_hat = np.array([100.0, 20.0])
    stats = dense_condition_numbers(A, U, lambda_hat, 0.1)
    assert stats["condition_preconditioned"] < stats["condition_A_mu"]
    y = apply_inverse_preconditioner(U, lambda_hat, 0.1, np.ones(4))
    assert y.shape == (4,)
    return {"ok": True, **stats}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(_self_test(), indent=2))
        return 0
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --self-test is used")
    payload = json.loads(args.input.read_text())
    result = apply_inverse_preconditioner(payload["U"], payload["lambda_hat"], payload["mu"], payload["r"])
    args.output.write_text(json.dumps({"P_inv_r": result.tolist()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
