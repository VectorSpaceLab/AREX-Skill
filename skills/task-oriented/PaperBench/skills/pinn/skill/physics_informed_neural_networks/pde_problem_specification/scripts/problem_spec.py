from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Domain:
    t_min: float
    t_max: float
    x_min: float
    x_max: float

    def contains(self, point: dict) -> bool:
        return self.t_min <= point["t"] <= self.t_max and self.x_min <= point["x"] <= self.x_max


def reference_burgers_proxy(t: float, x: float) -> float:
    return -0.5 * x + 0.25 * t


def _grid_points(domain: Domain, count: int) -> list[dict]:
    if count <= 0:
        raise ValueError("point count must be positive")
    if count == 1:
        return [{"t": domain.t_min, "x": domain.x_min}]
    points = []
    for index in range(count):
        alpha = index / (count - 1)
        beta = ((index * 3) % count) / (count - 1)
        points.append({
            "t": domain.t_min + alpha * (domain.t_max - domain.t_min),
            "x": domain.x_min + beta * (domain.x_max - domain.x_min),
        })
    return points


def build_burgers_problem(
    observation_count: int = 8,
    collocation_count: int = 16,
    nu: float = 0.01,
    reference: Callable[[float, float], float] = reference_burgers_proxy,
) -> dict:
    domain = Domain(0.0, 1.0, -1.0, 1.0)
    observations = []
    for point in _grid_points(domain, observation_count):
        observations.append({**point, "u": float(reference(point["t"], point["x"]))})
    collocation_points = _grid_points(domain, collocation_count)
    item = {
        "schema_version": 1,
        "pde": "burgers",
        "domain": domain.__dict__,
        "coefficients": {"nu": float(nu)},
        "observations": observations,
        "collocation_points": collocation_points,
        "target": {"metric": "loss_reduction", "proxy": True},
        "is_resource_derived": False,
        "provenance": "synthetic current-attempt reduced recovery item",
        "resource_files": [],
    }
    validate_problem(item)
    return item


def validate_problem(item: dict) -> dict:
    domain = Domain(**item["domain"])
    observations = item.get("observations", [])
    collocation_points = item.get("collocation_points", [])
    if not observations:
        raise ValueError("observations must be nonempty")
    if not collocation_points:
        raise ValueError("collocation_points must be nonempty")
    if "nu" not in item.get("coefficients", {}):
        raise ValueError("Burgers coefficient nu is required")
    for point in observations + collocation_points:
        if not domain.contains(point):
            raise ValueError(f"point outside domain: {point}")
    if any("u" in point for point in collocation_points):
        raise ValueError("collocation points must not include solution labels")
    return {"ok": True, "observation_count": len(observations), "collocation_count": len(collocation_points)}


def main() -> None:
    print(json.dumps(build_burgers_problem(), indent=2))


if __name__ == "__main__":
    main()
