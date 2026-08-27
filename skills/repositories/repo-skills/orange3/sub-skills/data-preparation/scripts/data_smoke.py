#!/usr/bin/env python3
"""Non-mutating smoke check for Orange data-preparation surfaces."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from Orange.data import (  # noqa: F401 - imported for the smoke path
    ContinuousVariable,
    DiscreteVariable,
    Domain,
    StringVariable,
    Table,
)
from Orange.preprocess import Continuize, Discretize, Impute, Normalize


def main() -> int:
    iris = Table("iris")
    toy_domain = Domain(
        [ContinuousVariable("x"), DiscreteVariable("y", values=("no", "yes"))],
        metas=[StringVariable("tag")],
    )
    toy = Table.from_numpy(
        toy_domain,
        [[1.0, 0.0], [2.0, 1.0]],
        metas=[["a"], ["b"]],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        saved = Path(tmpdir) / "iris.tab"
        iris.save(saved.as_posix())
        round_trip = Table.from_file(saved.as_posix())

    summary = {
        "iris_rows": len(iris),
        "iris_domain": str(iris.domain),
        "round_trip_rows": len(round_trip),
        "round_trip_domain": str(round_trip.domain),
        "toy_rows": len(toy),
        "toy_domain": str(toy.domain),
        "continuize_cols": len(Continuize()(Table("zoo")).domain.attributes),
        "discretize_cols": len(Discretize()(Table("iris")).domain.attributes),
        "imputed_rows": len(Impute()(Table("iris"))),
        "normalized_rows": len(Normalize()(Table("iris"))),
    }
    try:
        from Orange.data.sql.backend import Backend
    except Exception as exc:  # optional, service-bound path
        summary["sql_backends"] = f"unavailable:{exc.__class__.__name__}"
    else:
        summary["sql_backends"] = len(Backend.available_backends())
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
