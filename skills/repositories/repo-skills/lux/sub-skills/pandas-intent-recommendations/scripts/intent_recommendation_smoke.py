#!/usr/bin/env python3
"""Offline Lux Pandas intent/recommendation smoke check.

The script creates a small in-memory dataframe and validates Lux's Pandas
monkeypatch, dataframe/series classes, intent compilation, recommendation
access, current-visualization export facts, and the expected non-widget
`exported` behavior. It does not read external files or use the network.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import Any, Dict, Iterable, Optional


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local, offline Lux Pandas intent/recommendation smoke check."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the JSON success summary and print only failures.",
    )
    return parser


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_smoke() -> Dict[str, Any]:
    # Import Lux before creating any Pandas objects that should receive Lux behavior.
    import lux  # noqa: F401
    import pandas as pd
    from lux.core.frame import LuxDataFrame
    from lux.core.series import LuxSeries
    from lux.vis.Vis import Vis

    df = pd.DataFrame(
        {
            "sales": [10, 13, 15, 20, 21, 25, 30, 35],
            "profit": [1, 2, 1, 4, 3, 5, 6, 7],
            "discount": [0.0, 0.1, 0.0, 0.2, 0.1, 0.0, 0.3, 0.2],
            "category": ["A", "A", "B", "B", "C", "C", "A", "B"],
        }
    )

    _assert(isinstance(df, LuxDataFrame), "pd.DataFrame did not create a LuxDataFrame")
    _assert(isinstance(df["category"], LuxSeries), "column selection did not create a LuxSeries")
    plain_df = df.to_pandas()
    _assert(not isinstance(plain_df, LuxDataFrame), "to_pandas() did not return a plain Pandas dataframe")
    _assert(plain_df.__class__.__name__ == "DataFrame", "to_pandas() return type is not DataFrame")

    default_recs = df.recommendation
    _assert(isinstance(default_recs, dict), "default recommendations are not a dictionary")
    _assert(default_recs, "default recommendations are empty")
    _assert(
        any(len(vlist) > 0 for vlist in default_recs.values()),
        "default recommendation collections are all empty",
    )
    default_expected = {"Correlation", "Distribution", "Occurrence", "Temporal", "Geographical"}
    _assert(
        bool(default_expected.intersection(default_recs)),
        f"default recommendation keys look unexpected: {list(default_recs)}",
    )

    df.intent = ["sales", "category=A"]
    _assert([clause.attribute for clause in df.intent] == ["sales", "category"], "intent was not parsed")
    _assert(df.intent[1].value == "A", "filter intent value was not parsed")

    current = df.current_vis
    _assert(current is not None and len(current) == 1, "intent did not compile to one current visualization")
    current_vis = current[0]
    _assert(current_vis.mark != "", "current visualization did not infer a mark")
    vegalite = current_vis.to_code(language="vegalite", prettyOutput=False)
    _assert(isinstance(vegalite, dict), "current visualization did not export a Vega-Lite dict")
    _assert(
        "mark" in vegalite or "encoding" in vegalite,
        "current visualization export lacks mark/encoding facts",
    )

    intent_recs = df.recommendation
    intent_expected = {"Enhance", "Filter", "Generalize", "Similarity"}
    _assert(
        bool(intent_expected.intersection(intent_recs)),
        f"intent recommendation keys look unexpected: {list(intent_recs)}",
    )
    _assert(
        any(len(vlist) > 0 for vlist in intent_recs.values()),
        "intent recommendation collections are all empty",
    )

    vis = Vis(["category", "sales"], df)
    df.set_intent_as_vis(vis)
    _assert(df.intent, "set_intent_as_vis did not set dataframe intent")
    _assert(df.current_vis is not None and len(df.current_vis) == 1, "Vis-derived intent did not compile")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exported = df.exported
    _assert(exported == [], "exported should be empty without an attached widget")
    _assert(
        any("No widget attached" in str(warning.message) for warning in caught),
        "exported did not warn about missing widget",
    )

    df.clear_intent()
    _assert(df.intent == [], "clear_intent did not clear the dataframe intent")

    return {
        "status": "ok",
        "dataframe_class": f"{type(df).__module__}.{type(df).__name__}",
        "series_class": f"{type(df['category']).__module__}.{type(df['category']).__name__}",
        "default_recommendation_keys": sorted(default_recs.keys()),
        "intent_recommendation_keys": sorted(intent_recs.keys()),
        "current_vis_mark": current_vis.mark,
        "current_vis_export_keys": sorted(vegalite.keys()),
        "exported_without_widget": exported,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_smoke()
    except Exception as exc:  # pragma: no cover - command-line failure path
        print(f"intent_recommendation_smoke failed: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
