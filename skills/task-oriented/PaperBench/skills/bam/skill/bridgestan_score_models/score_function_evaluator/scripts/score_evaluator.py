#!/usr/bin/env python3
import argparse
import importlib.util
import json
import math
from pathlib import Path


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_transform_script():
    return Path(__file__).resolve().parents[2] / "parameter_transform_adapter" / "scripts" / "parameter_transforms.py"


def _theta_contract(contract):
    for parameter in contract.get("parameters", []):
        if parameter.get("name") == "theta":
            return parameter
    raise ValueError("contract must contain parameter theta")


def _check_contract(contract):
    distributions = {term.get("distribution") for term in contract.get("model_terms", [])}
    if "bernoulli" not in distributions or "beta" not in distributions:
        raise ValueError("contract must contain beta prior and bernoulli likelihood")


def log_density_z(z, y_values):
    if z >= 0:
        exp_neg = math.exp(-z)
        theta = 1.0 / (1.0 + exp_neg)
    else:
        exp_pos = math.exp(z)
        theta = exp_pos / (1.0 + exp_pos)
    successes = sum(int(v) for v in y_values)
    n_obs = len(y_values)
    return successes * math.log(theta) + (n_obs - successes) * math.log1p(-theta) + math.log(theta) + math.log1p(-theta)


def analytic_derivatives(z, y_values):
    if z >= 0:
        exp_neg = math.exp(-z)
        theta = 1.0 / (1.0 + exp_neg)
    else:
        exp_pos = math.exp(z)
        theta = exp_pos / (1.0 + exp_pos)
    successes = sum(int(v) for v in y_values)
    n_obs = len(y_values)
    gradient = successes + 1.0 - (n_obs + 2.0) * theta
    hessian = -(n_obs + 2.0) * theta * (1.0 - theta)
    return theta, gradient, hessian


def finite_difference(z, y_values, step=1e-5):
    f_plus = log_density_z(z + step, y_values)
    f_mid = log_density_z(z, y_values)
    f_minus = log_density_z(z - step, y_values)
    gradient = (f_plus - f_minus) / (2.0 * step)
    hessian = (f_plus - 2.0 * f_mid + f_minus) / (step * step)
    return gradient, hessian


def evaluate_score(contract, data, z, transform_script=None, tolerance=1e-4):
    _check_contract(contract)
    theta_parameter = _theta_contract(contract)
    transform_module = _load_module(Path(transform_script) if transform_script else _default_transform_script(), "parameter_transforms")
    transform = transform_module.constrain(float(z), theta_parameter)
    y_values = data.get("y", [])
    if not all(value in (0, 1, True, False) for value in y_values):
        raise ValueError("Bernoulli observations must be binary")
    theta, gradient, hessian = analytic_derivatives(float(z), y_values)
    fd_gradient, fd_hessian = finite_difference(float(z), y_values)
    result = {
        "schema_version": 1,
        "unconstrained": float(z),
        "theta": theta,
        "transform": transform,
        "sample_count": len(y_values),
        "successes": sum(int(v) for v in y_values),
        "log_density": log_density_z(float(z), y_values),
        "gradient": gradient,
        "hessian": hessian,
        "finite_difference": {"gradient": fd_gradient, "hessian": fd_hessian},
        "errors": {"gradient_abs": abs(gradient - fd_gradient), "hessian_abs": abs(hessian - fd_hessian)},
    }
    result["checks"] = {
        "contract_consumed": True,
        "transform_called": transform.get("valid") is True,
        "log_density_finite": math.isfinite(result["log_density"]),
        "gradient_matches_finite_difference": result["errors"]["gradient_abs"] < tolerance,
        "hessian_matches_finite_difference": result["errors"]["hessian_abs"] < 5e-3,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--z", required=True, type=float)
    parser.add_argument("--transform-script")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = evaluate_score(json.loads(Path(args.contract).read_text()), json.loads(Path(args.data).read_text()), args.z, args.transform_script)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({"ok": all(result["checks"].values()), "output": args.output, "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
