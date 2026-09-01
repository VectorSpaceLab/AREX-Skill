#!/usr/bin/env python3
"""One-dimensional diffusion Stein kernel and DKSD U-statistic helpers."""

from __future__ import annotations

import argparse
import json
import math
from typing import Callable, Iterable

ScoreFn = Callable[[float, float], float]
DiffusionFn = Callable[[float, float], float]


def student_t_score(theta: float, x: float, nu: float = 5.0, scale: float = 1.0) -> float:
    z = (x - theta) / scale
    return -((nu + 1.0) * z) / (scale * (nu + z * z))


def imq_terms(x: float, y: float, c: float = 1.0, beta: float = -0.5) -> dict[str, float]:
    r = x - y
    base = c * c + r * r
    k = base ** beta
    dk_dx = 2.0 * beta * r * (base ** (beta - 1.0))
    dk_dy = -dk_dx
    d2_dxdy = -2.0 * beta * (base ** (beta - 1.0)) - 4.0 * beta * (beta - 1.0) * r * r * (base ** (beta - 2.0))
    return {"k": k, "dk_dx": dk_dx, "dk_dy": dk_dy, "d2_dxdy": d2_dxdy}


def rbf_terms(x: float, y: float, lengthscale: float = 1.0) -> dict[str, float]:
    r = x - y
    inv_l2 = 1.0 / (lengthscale * lengthscale)
    k = math.exp(-0.5 * r * r * inv_l2)
    dk_dx = -r * inv_l2 * k
    dk_dy = r * inv_l2 * k
    d2_dxdy = (inv_l2 - r * r * inv_l2 * inv_l2) * k
    return {"k": k, "dk_dx": dk_dx, "dk_dy": dk_dy, "d2_dxdy": d2_dxdy}


def stein_kernel(
    theta: float,
    x: float,
    y: float,
    score: ScoreFn = student_t_score,
    diffusion: DiffusionFn | None = None,
    kernel: str = "imq",
    nu: float = 5.0,
    scale: float = 1.0,
) -> float:
    diffusion = diffusion or (lambda _theta, _x: 1.0)
    if kernel == "imq":
        terms = imq_terms(x, y)
    elif kernel == "rbf":
        terms = rbf_terms(x, y)
    else:
        raise ValueError(f"unsupported kernel: {kernel}")
    sx = score(theta, x, nu, scale) if score is student_t_score else score(theta, x)
    sy = score(theta, y, nu, scale) if score is student_t_score else score(theta, y)
    mx = diffusion(theta, x)
    my = diffusion(theta, y)
    return mx * my * (
        sx * sy * terms["k"]
        + sx * terms["dk_dy"]
        + sy * terms["dk_dx"]
        + terms["d2_dxdy"]
    )


def dksd_u_statistic(
    samples: Iterable[float],
    theta: float,
    score: ScoreFn = student_t_score,
    diffusion: DiffusionFn | None = None,
    kernel: str = "imq",
    nu: float = 5.0,
    scale: float = 1.0,
) -> dict[str, object]:
    xs = [float(x) for x in samples]
    if len(xs) < 2:
        raise ValueError("at least two samples are required for an off-diagonal U-statistic")
    values: list[float] = []
    max_asymmetry = 0.0
    for i, x in enumerate(xs):
        for j, y in enumerate(xs):
            if i == j:
                continue
            value = stein_kernel(theta, x, y, score, diffusion, kernel, nu, scale)
            reverse = stein_kernel(theta, y, x, score, diffusion, kernel, nu, scale)
            max_asymmetry = max(max_asymmetry, abs(value - reverse))
            values.append(value)
    finite = all(math.isfinite(v) for v in values)
    loss = sum(values) / len(values)
    return {
        "theta": theta,
        "loss": loss,
        "pair_count": len(values),
        "finite": finite,
        "max_asymmetry": max_asymmetry,
        "score_only": True,
        "kernel": kernel,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-json", required=True)
    parser.add_argument("--theta", type=float, required=True)
    parser.add_argument("--kernel", default="imq", choices=["imq", "rbf"])
    parser.add_argument("--nu", type=float, default=5.0)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    samples = json.loads(args.samples_json)
    result = dksd_u_statistic(samples, args.theta, kernel=args.kernel, nu=args.nu, scale=args.scale)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
