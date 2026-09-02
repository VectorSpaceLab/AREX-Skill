"""F-NPSE and PF-NPSE score composition utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable


Vector = list[float]
Matrix = list[Vector]
Rows = Vector | Matrix


def is_matrix(value: Rows) -> bool:
    return bool(value) and isinstance(value[0], list)  # type: ignore[index]


def as_rows(value: Rows) -> Matrix:
    if is_matrix(value):
        return [[float(item) for item in row] for row in value]  # type: ignore[union-attr]
    return [[float(item) for item in value]]  # type: ignore[union-attr]


def restore_shape(rows: Matrix, template: Rows) -> Rows:
    return rows if is_matrix(template) else rows[0]


def standard_normal_prior_score(theta: Rows) -> Rows:
    rows = as_rows(theta)
    out = [[-value for value in row] for row in rows]
    return restore_shape(out, theta)


def add_rows(a: Matrix, b: Matrix) -> Matrix:
    return [[x + y for x, y in zip(row_a, row_b)] for row_a, row_b in zip(a, b)]


def scale_rows(scale: float, rows: Matrix) -> Matrix:
    return [[scale * value for value in row] for row in rows]


def sum_row_terms(terms: list[Rows], template: Rows) -> Matrix:
    total = [[0.0 for _ in row] for row in as_rows(template)]
    for term in terms:
        total = add_rows(total, as_rows(term))
    return total


def prior_coefficient(count: int, t: int | float, total_steps: int | float) -> float:
    if count < 1:
        raise ValueError("count must be positive")
    if total_steps <= 0:
        raise ValueError("total_steps must be positive")
    if t < 0 or t > total_steps:
        raise ValueError("t must be between 0 and total_steps")
    return float((1.0 - count) * (total_steps - t) / total_steps)


def partition_observations(observations: Matrix, group_size: int) -> list[Matrix]:
    if not observations:
        raise ValueError("observations must be non-empty")
    if group_size < 1:
        raise ValueError("group_size must be positive")
    return [observations[i : i + group_size] for i in range(0, len(observations), group_size)]


def compose_f_npse_score(
    theta: Rows,
    t: int | float,
    total_steps: int | float,
    observations: Matrix,
    score_fn: Callable[[Rows, int | float, Vector], Rows],
    prior_score_fn: Callable[[Rows], Rows] = standard_normal_prior_score,
) -> tuple[Rows, dict]:
    if not observations:
        raise ValueError("observations must be non-empty")
    coeff = prior_coefficient(len(observations), t, total_steps)
    terms = [score_fn(theta, t, [float(value) for value in obs]) for obs in observations]
    prior_rows = scale_rows(coeff, as_rows(prior_score_fn(theta)))
    composed_rows = add_rows(prior_rows, sum_row_terms(terms, theta))
    return restore_shape(composed_rows, theta), {
        "method": "f_npse",
        "observation_count": int(len(observations)),
        "group_count": int(len(observations)),
        "prior_coefficient": coeff,
        "term_scores": terms,
    }


def compose_pf_npse_score(
    theta: Rows,
    t: int | float,
    total_steps: int | float,
    observations: Matrix,
    group_size: int,
    group_score_fn: Callable[[Rows, int | float, Matrix], Rows],
    prior_score_fn: Callable[[Rows], Rows] = standard_normal_prior_score,
) -> tuple[Rows, dict]:
    groups = partition_observations(observations, group_size)
    coeff = prior_coefficient(len(groups), t, total_steps)
    terms = [group_score_fn(theta, t, group) for group in groups]
    prior_rows = scale_rows(coeff, as_rows(prior_score_fn(theta)))
    composed_rows = add_rows(prior_rows, sum_row_terms(terms, theta))
    return restore_shape(composed_rows, theta), {
        "method": "pf_npse",
        "observation_count": int(len(observations)),
        "group_count": int(len(groups)),
        "group_size": int(group_size),
        "prior_coefficient": coeff,
        "term_scores": terms,
    }


def linear_observation_score(theta: Rows, t: int | float, observation: Vector) -> Rows:
    rows = as_rows(theta)
    out = [[obs - value for value, obs in zip(row, observation)] for row in rows]
    return restore_shape(out, theta)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta", required=True, help="JSON vector or rows.")
    parser.add_argument("--observations", required=True, help="JSON rows.")
    parser.add_argument("--t", type=float, required=True)
    parser.add_argument("--total-steps", type=float, required=True)
    parser.add_argument("--method", choices=["f_npse", "pf_npse"], default="f_npse")
    parser.add_argument("--group-size", type=int, default=1)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    theta = json.loads(args.theta)
    observations = json.loads(args.observations)
    if args.method == "f_npse":
        score, meta = compose_f_npse_score(theta, args.t, args.total_steps, observations, linear_observation_score)
    else:
        def group_score(th: Rows, tt: int | float, group: Matrix) -> Rows:
            means = [sum(row[j] for row in group) / len(group) for j in range(len(group[0]))]
            return linear_observation_score(th, tt, means)

        score, meta = compose_pf_npse_score(theta, args.t, args.total_steps, observations, args.group_size, group_score)
    result = {"score": score, "metadata": meta}
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
