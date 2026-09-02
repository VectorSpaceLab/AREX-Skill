#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def _load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_skill_root():
    return Path(__file__).resolve().parents[2]


def _load_dependencies(skill_root=None):
    root = Path(skill_root) if skill_root else _default_skill_root()
    nystrom = _load_script(root / "randomized_nystrom_factorization" / "scripts" / "nystrom.py", "generated_nystrom")
    preconditioner = _load_script(root / "nystrom_preconditioner" / "scripts" / "preconditioner.py", "generated_preconditioner")
    return nystrom, preconditioner


def cg_solve(A, b, mu, tol=1e-8, maxiter=500, M_inv=None):
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    x = np.zeros_like(b)
    rhs_norm = max(float(np.linalg.norm(b)), 1e-30)
    def A_mu(v):
        return A @ v + mu * v
    r = b - A_mu(x)
    z = M_inv(r) if M_inv else r.copy()
    p = z.copy()
    rz_old = float(r @ z)
    residuals = [float(np.linalg.norm(r))]
    preconditioner_applications = 1 if M_inv else 0
    converged = residuals[-1] / rhs_norm <= tol
    breakdown = ""
    iteration = 0
    while not converged and iteration < maxiter:
        Ap = A_mu(p)
        denom = float(p @ Ap)
        if denom <= 0 or not np.isfinite(denom):
            breakdown = "nonpositive_or_invalid_curvature"
            break
        alpha = rz_old / denom
        x = x + alpha * p
        r = r - alpha * Ap
        residuals.append(float(np.linalg.norm(r)))
        if residuals[-1] / rhs_norm <= tol:
            converged = True
            iteration += 1
            break
        z = M_inv(r) if M_inv else r.copy()
        preconditioner_applications += 1 if M_inv else 0
        rz_new = float(r @ z)
        if abs(rz_old) < 1e-300:
            breakdown = "zero_preconditioned_residual_inner_product"
            break
        beta = rz_new / rz_old
        p = z + beta * p
        rz_old = rz_new
        iteration += 1
    return {
        "x": x,
        "iterations": int(iteration),
        "residuals": residuals,
        "relative_residuals": [float(v / rhs_norm) for v in residuals],
        "converged": bool(converged),
        "breakdown": breakdown,
        "preconditioner_applications": int(preconditioner_applications),
    }


def nystrom_pcg_solve(A, b, mu, ell, tol=1e-8, maxiter=500, seed=0, skill_root=None):
    nystrom, preconditioner = _load_dependencies(skill_root)
    U, lambda_hat, nys_info = nystrom.randomized_nystrom(A, ell, seed=seed)
    def M_inv(r):
        return preconditioner.apply_inverse_preconditioner(U, lambda_hat, mu, r)
    trace = cg_solve(A, b, mu, tol=tol, maxiter=maxiter, M_inv=M_inv)
    trace["nystrom_diagnostics"] = nys_info
    trace["mechanism_checks"] = {
        "randomized_nystrom_factorization_executed": True,
        "preconditioner_applied": trace["preconditioner_applications"] > 0,
        "pcg_iterations_executed": trace["iterations"] > 0,
        "optimizer_step_executed": trace["iterations"] > 0,
        "reduced_training_executed": False,
    }
    trace["lambda_hat"] = lambda_hat.tolist()
    return trace


def synthetic_problem(n=96, seed=0):
    rng = np.random.default_rng(seed)
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    spectrum = np.concatenate([np.geomspace(1e4, 80.0, 12), np.geomspace(1.0, 1e-3, n - 12)])
    A = Q @ np.diag(spectrum) @ Q.T
    x_true = rng.standard_normal(n)
    mu = 1e-2
    b = (A + mu * np.eye(n)) @ x_true
    return A, b, x_true, mu, spectrum


def _self_test():
    A, b, x_true, mu, _ = synthetic_problem(n=64, seed=11)
    pcg = nystrom_pcg_solve(A, b, mu, ell=14, tol=1e-8, maxiter=300, seed=12)
    cg = cg_solve(A, b, mu, tol=1e-8, maxiter=300)
    assert pcg["converged"]
    assert np.linalg.norm(pcg["x"] - x_true) / np.linalg.norm(x_true) < 1e-5
    assert pcg["iterations"] < cg["iterations"]
    return {"ok": True, "pcg_iterations": pcg["iterations"], "cg_iterations": cg["iterations"]}


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
    A = np.asarray(payload["A"], dtype=float)
    b = np.asarray(payload["b"], dtype=float)
    result = nystrom_pcg_solve(A, b, payload["mu"], payload["ell"], payload.get("tol", 1e-8), payload.get("maxiter", 500), payload.get("seed", 0))
    serial = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in result.items()}
    args.output.write_text(json.dumps(serial, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
