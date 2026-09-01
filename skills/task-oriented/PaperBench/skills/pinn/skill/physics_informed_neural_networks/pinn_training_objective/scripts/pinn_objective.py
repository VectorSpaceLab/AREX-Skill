from __future__ import annotations

from copy import deepcopy
from typing import Callable

try:
    from burgers_residual import QuadraticSurrogate, mean_squared_residual
except ImportError:
    QuadraticSurrogate = None
    mean_squared_residual = None

PARAM_NAMES = ["bias", "t_weight", "x_weight", "tx_weight", "xx_weight"]


def model_from_params(params: dict):
    if QuadraticSurrogate is None:
        raise ImportError("burgers_residual.QuadraticSurrogate is required on PYTHONPATH")
    return QuadraticSurrogate(**{name: float(params[name]) for name in PARAM_NAMES})


def data_loss(problem: dict, params: dict) -> float:
    model = model_from_params(params)
    observations = problem["observations"]
    return sum((model.value(point["t"], point["x"]) - point["u"]) ** 2 for point in observations) / len(observations)


def residual_loss(problem: dict, params: dict) -> float:
    model = model_from_params(params)
    return mean_squared_residual(problem["collocation_points"], model, problem["coefficients"]["nu"])


def total_loss(problem: dict, params: dict, data_weight: float = 1.0, residual_weight: float = 1.0) -> dict:
    data = data_loss(problem, params)
    residual = residual_loss(problem, params)
    return {"data_loss": data, "residual_loss": residual, "total_loss": data_weight * data + residual_weight * residual}


def finite_difference_gradient(problem: dict, params: dict, objective: Callable[[dict, dict], dict], epsilon: float = 1e-5) -> dict:
    gradient = {}
    for name in PARAM_NAMES:
        plus = deepcopy(params)
        minus = deepcopy(params)
        plus[name] += epsilon
        minus[name] -= epsilon
        gradient[name] = (objective(problem, plus)["total_loss"] - objective(problem, minus)["total_loss"]) / (2.0 * epsilon)
    return gradient


def train_steps(problem: dict, params: dict, learning_rate: float = 0.05, steps: int = 1) -> dict:
    current = {name: float(params[name]) for name in PARAM_NAMES}
    before = deepcopy(current)
    loss_before = total_loss(problem, current)
    for _ in range(steps):
        gradient = finite_difference_gradient(problem, current, total_loss)
        for name in PARAM_NAMES:
            current[name] -= learning_rate * gradient[name]
    loss_after = total_loss(problem, current)
    return {
        "schema_version": 1,
        "loss_before": loss_before["total_loss"],
        "loss_after": loss_after["total_loss"],
        "data_loss_before": loss_before["data_loss"],
        "residual_loss_before": loss_before["residual_loss"],
        "data_loss_after": loss_after["data_loss"],
        "residual_loss_after": loss_after["residual_loss"],
        "params_before": before,
        "params_after": current,
        "parameters_before": before,
        "parameters_after": current,
        "optimizer_state_changed": before != current,
        "steps": steps,
        "learning_rate": learning_rate,
    }
