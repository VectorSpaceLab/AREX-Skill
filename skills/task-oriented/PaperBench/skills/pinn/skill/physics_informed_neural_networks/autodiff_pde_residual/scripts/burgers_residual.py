from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class QuadraticSurrogate:
    bias: float = 0.0
    t_weight: float = 0.1
    x_weight: float = -0.2
    tx_weight: float = 0.05
    xx_weight: float = 0.03

    def value(self, t: float, x: float) -> float:
        return self.bias + self.t_weight * t + self.x_weight * x + self.tx_weight * t * x + self.xx_weight * x * x

    def derivatives(self, t: float, x: float) -> dict:
        return {
            "u": self.value(t, x),
            "u_t": self.t_weight + self.tx_weight * x,
            "u_x": self.x_weight + self.tx_weight * t + 2.0 * self.xx_weight * x,
            "u_xx": 2.0 * self.xx_weight,
        }


def burgers_residual(point: dict, model: QuadraticSurrogate, nu: float) -> dict:
    derivatives = model.derivatives(float(point["t"]), float(point["x"]))
    residual = derivatives["u_t"] + derivatives["u"] * derivatives["u_x"] - float(nu) * derivatives["u_xx"]
    return {**derivatives, "residual": residual}


def residual_batch(points: Iterable[dict], model: QuadraticSurrogate, nu: float) -> list[dict]:
    return [burgers_residual(point, model, nu) for point in points]


def mean_squared_residual(points: Iterable[dict], model: QuadraticSurrogate, nu: float) -> float:
    diagnostics = residual_batch(points, model, nu)
    if not diagnostics:
        raise ValueError("at least one collocation point is required")
    return sum(item["residual"] ** 2 for item in diagnostics) / len(diagnostics)
