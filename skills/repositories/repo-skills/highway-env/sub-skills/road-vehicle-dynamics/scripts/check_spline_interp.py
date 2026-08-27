#!/usr/bin/env python3
"""Tiny deterministic smoke check for HighwayEnv's numpy_interp1d helper.

The helper is intentionally small: it checks exact knots, interpolation,
extrapolation, array output, and scalar output on a fixed fixture. If SciPy is
available, it also compares against scipy.interpolate.interp1d with
fill_value="extrapolate". It performs no benchmarking.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np


FIXTURE_X = np.array([0.0, 1.0, 3.0, 6.0], dtype=float)
FIXTURE_Y = np.array([2.0, 4.0, 0.0, 6.0], dtype=float)
QUERY = np.array([-1.0, 0.0, 0.5, 2.0, 4.5, 6.0, 8.0], dtype=float)
EXPECTED = np.array([0.0, 2.0, 3.0, 2.0, 3.0, 6.0, 10.0], dtype=float)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def main() -> int:
    summary: dict[str, Any] = {
        "helper": "check_spline_interp",
        "ok": False,
        "used_scipy": False,
        "fixture": {
            "x": FIXTURE_X.tolist(),
            "y": FIXTURE_Y.tolist(),
            "query": QUERY.tolist(),
        },
        "checks": [],
    }

    try:
        from highway_env.road.spline import numpy_interp1d
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        summary.update(
            {
                "stage": "import_highway_env.road.spline",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        print(json.dumps(summary, sort_keys=True, default=_json_default))
        return 2

    try:
        f_np = numpy_interp1d(FIXTURE_X, FIXTURE_Y)
        actual = np.asarray(f_np(QUERY), dtype=float)
        np.testing.assert_allclose(actual, EXPECTED, atol=1e-12, rtol=1e-12)
        summary["checks"].append("internal_expected_array")

        scalar_actual = f_np(2.0)
        if not isinstance(scalar_actual, float):
            raise AssertionError(f"scalar call returned {type(scalar_actual).__name__}")
        np.testing.assert_allclose(scalar_actual, 2.0, atol=1e-12, rtol=1e-12)
        summary["checks"].append("internal_expected_scalar")

        try:
            from scipy import interpolate  # type: ignore
        except Exception:
            summary["scipy_status"] = "not_available"
        else:
            f_sp = interpolate.interp1d(
                FIXTURE_X,
                FIXTURE_Y,
                fill_value="extrapolate",
            )
            scipy_actual = np.asarray(f_sp(QUERY), dtype=float)
            np.testing.assert_allclose(actual, scipy_actual, atol=1e-12, rtol=1e-12)
            summary["used_scipy"] = True
            summary["checks"].append("scipy_interp1d_array")

        summary.update(
            {
                "ok": True,
                "max_abs_diff_vs_expected": float(np.max(np.abs(actual - EXPECTED))),
                "actual": actual.tolist(),
            }
        )
        print(json.dumps(summary, sort_keys=True, default=_json_default))
        return 0
    except Exception as exc:
        summary.update(
            {
                "stage": "validation",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        print(json.dumps(summary, sort_keys=True, default=_json_default))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
