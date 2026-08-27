#!/usr/bin/env python3
"""Tiny Vaex expressions/analytics smoke checks.

The script uses only public Vaex APIs and in-memory data. It is safe to run from
any current working directory and does not read/write user data, access the
network, or require project files.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

np = None
pa = None
vaex = None


def _ensure_imports() -> None:
    """Import runtime dependencies after --help can be displayed."""
    global np, pa, vaex
    if vaex is not None:
        return
    try:
        import numpy as _np
        import pyarrow as _pa
        import vaex as _vaex
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "Missing runtime dependency for analytics_smoke.py: "
            f"{exc.name}. Run this script in an environment with Vaex installed."
        ) from exc
    np = _np
    pa = _pa
    vaex = _vaex


def _as_list(value: Any) -> list[Any]:
    """Convert tiny Vaex/NumPy/Arrow values to Python lists for assertions."""
    if hasattr(value, "tolist"):
        result = value.tolist()
    elif hasattr(value, "to_pylist"):
        result = value.to_pylist()
    else:
        result = list(value)
    return result


def _assert_close(actual: Any, expected: Any, *, rtol: float = 1e-7, atol: float = 1e-7) -> None:
    np.testing.assert_allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float), rtol=rtol, atol=atol)


def build_dataframe():
    return vaex.from_arrays(
        id=np.arange(1, 7, dtype=np.int64),
        key=np.array(["a", "b", "b", None, "a", "c"], dtype=object),
        x=np.array([1, 2, 3, 4, 5, 6], dtype=np.float64),
        y=np.array([10, 20, 30, 40, 50, 60], dtype=np.float64),
        when=np.array(
            [
                "2020-01-01T00:00:00",
                "2020-01-02T00:00:00",
                "2020-02-01T00:00:00",
                "2020-02-02T00:00:00",
                "2020-03-01T00:00:00",
                "2020-03-02T00:00:00",
            ],
            dtype="datetime64[ns]",
        ),
        text=np.array(["alpha", "beta", None, "delta", "alphabet", "gamma"], dtype=object),
    )


def check_expressions_virtual_columns(df) -> dict[str, Any]:
    df["double_x"] = df.x * 2
    df.add_virtual_column("score", "double_x + y")

    preview = df.evaluate("score", i1=0, i2=3).tolist()
    _assert_close(preview, [12, 24, 36])

    weird = vaex.from_arrays(**{"gross margin": np.array([0.1, 0.2, 0.3]), "x": np.array([1.0, 2.0, 3.0])})
    weird_preview = weird.evaluate(weird["gross margin"] + weird.x, i1=0, i2=3).tolist()
    _assert_close(weird_preview, [1.1, 2.2, 3.3])

    df.select(df.x > 3, name="large_x")
    assert int(df.count("x", selection="large_x")) == 3
    filtered = df[df.x > 3]
    assert filtered.x.tolist() == [4.0, 5.0, 6.0]

    return {"score_preview": preview, "selected_rows": int(df.count("x", selection="large_x"))}


def check_statistics(df) -> dict[str, Any]:
    assert int(df.count()) == 6
    assert int(df.count("x")) == 6
    assert float(df.sum("y")) == 210.0
    assert float(df.mean("x")) == 3.5
    _assert_close(df.std("y"), np.std([10, 20, 30, 40, 50, 60]))
    _assert_close(df.minmax("x"), [1, 6])
    _assert_close(df.correlation("x", "y"), 1.0)

    p50 = float(np.asarray(df.percentile_approx("x", 50)).reshape(-1)[0])
    assert 2.5 <= p50 <= 4.5, p50

    mi = float(np.asarray(df.mutual_information("x", "y")).reshape(-1)[0])
    assert math.isfinite(mi) and mi >= 0

    unique_keys = set(df.unique("key", dropna=True))
    assert unique_keys == {"a", "b", "c"}

    key_counts = df.key.value_counts(dropna=False)
    assert int(key_counts.sum()) == 6
    assert int(key_counts["a"]) == 2
    assert int(key_counts["b"]) == 2

    return {"mean_x": float(df.mean("x")), "p50_x_approx": p50, "mutual_information_xy": mi}


def check_groupby_binby(df) -> dict[str, Any]:
    grouped = df.groupby(
        by="key",
        agg={
            "rows": vaex.agg.count(),
            "mean_y": vaex.agg.mean("y"),
            "sum_score": vaex.agg.sum("score"),
        },
        sort=True,
        row_limit=10,
    )

    keys = grouped.key.tolist()
    rows_by_key = dict(zip(keys, grouped.rows.tolist()))
    sums_by_key = dict(zip(keys, grouped.sum_score.tolist()))
    means_by_key = dict(zip(keys, grouped.mean_y.tolist()))

    assert rows_by_key["a"] == 2
    assert rows_by_key["b"] == 2
    assert rows_by_key["c"] == 1
    assert rows_by_key[None] == 1
    _assert_close([sums_by_key["a"], sums_by_key["b"], sums_by_key["c"], sums_by_key[None]], [72, 60, 72, 48])
    _assert_close([means_by_key["a"], means_by_key["b"], means_by_key["c"], means_by_key[None]], [30, 25, 60, 40])

    counts = df.count(binby="x", limits=[0, 7], shape=3)
    means = df.mean("y", binby="x", limits=[0, 7], shape=3)
    assert counts.tolist() == [2, 2, 2]
    _assert_close(means, [15, 35, 55])

    try:
        df.groupby(["key", "id"], agg="count", row_limit=2)
    except vaex.RowLimitException:
        row_limit_guard = "raised"
    else:  # pragma: no cover - defensive against API change
        raise AssertionError("Expected RowLimitException for guarded high-cardinality groupby")

    return {"group_keys": ["<missing>" if k is None else k for k in keys], "bin_counts": counts.tolist(), "row_limit_guard": row_limit_guard}


def check_join_sort_accessors(df) -> dict[str, Any]:
    right = vaex.from_arrays(
        key=np.array(["a", "b", "c"], dtype=object),
        label=np.array(["A", "B", "C"], dtype=object),
        weight=np.array([100, 200, 300], dtype=np.int64),
    )
    joined = df.join(right, on="key", rsuffix="_right")
    assert len(joined) == len(df)
    assert joined.weight.tolist() == [100, 200, 200, None, 100, 300]
    assert joined["label"].tolist() == ["A", "B", "B", None, "A", "C"]

    dup_right = vaex.from_arrays(key=np.array(["a", "a"], dtype=object), value=np.array([1, 2]))
    try:
        df.join(dup_right, on="key")
    except ValueError as exc:
        assert "duplication" in str(exc)
        duplicate_guard = "raised"
    else:  # pragma: no cover - defensive against API change
        raise AssertionError("Expected duplicate-key join guard to raise")

    sorted_y = df.sort("y", ascending=False).y.tolist()
    assert sorted_y == [60.0, 50.0, 40.0, 30.0, 20.0, 10.0]

    contains_alpha = df.text.str.contains("alpha", regex=False).tolist()
    assert contains_alpha == [True, False, None, False, True, False]

    months = df.when.dt.month.tolist()
    assert months == [1, 1, 2, 2, 3, 3]

    struct_array = pa.StructArray.from_arrays([pa.array([1, 2, 3]), pa.array(["x", "y", "z"])], names=["num", "label"])
    struct_df = vaex.from_arrays(payload=struct_array)
    assert struct_df.payload.struct.get("num").tolist() == [1, 2, 3]
    assert struct_df.payload[:, "label"].tolist() == ["x", "y", "z"]

    geo_df = vaex.from_arrays(ra=np.array([0.0, 90.0]), dec=np.array([0.0, 0.0]), distance=np.array([1.0, 1.0]))
    assert hasattr(geo_df, "geo")
    geo_df.geo.spherical2cartesian("ra", "dec", "distance", "gx", "gy", "gz", inplace=True)
    _assert_close([geo_df.gx.tolist()[0], geo_df.gy.tolist()[1]], [1.0, 1.0], atol=1e-12)

    return {"joined_rows": len(joined), "duplicate_join_guard": duplicate_guard, "months": months}


def run_smoke() -> dict[str, Any]:
    _ensure_imports()
    df = build_dataframe()
    results = {
        "vaex_version": vaex.__version__,
        "expressions": check_expressions_virtual_columns(df),
        "statistics": check_statistics(df),
        "groupby_binby": check_groupby_binby(df),
        "join_sort_accessors": check_join_sort_accessors(df),
    }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tiny Vaex expressions and analytics smoke checks.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON summary instead of a compact success line.")
    args = parser.parse_args()

    results = run_smoke()
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True, default=str))
    else:
        print(json.dumps({"status": "ok", "checks": list(results.keys()), "vaex_version": str(results["vaex_version"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
