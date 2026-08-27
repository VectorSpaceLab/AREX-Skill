#!/usr/bin/env python3
"""Offline Lux configuration/custom-action smoke test.

The script uses only an in-memory dataframe. It verifies that Lux can register a
validator-gated custom action, that the action appears only when its validator
passes, and that lux.debug_info(return_string=True) returns expected diagnostics.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable


def _build_frame(pd, enabled: bool):
    return pd.DataFrame(
        {
            "group": ["A", "A", "B", "B", "C", "C"],
            "x": [1, 2, 3, 4, 5, 6],
            "y": [2, 3, 5, 7, 11, 13],
            "enabled": [enabled] * 6,
        }
    )


def _assert_contains_all(text: str, tokens: Iterable[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"debug_info output is missing tokens: {missing}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run an offline Lux smoke test for lux.config, custom actions, "
            "display conditions, and debug_info."
        )
    )
    parser.add_argument(
        "--action-name",
        default="LuxSkillEnabledMetrics",
        help="temporary custom action name to register during the smoke test",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress success details; failures still raise assertions",
    )
    args = parser.parse_args(argv)

    import lux
    import pandas as pd
    from lux.vis.VisList import VisList

    action_name = args.action_name
    lux.config.set_executor_type("Pandas")
    lux.config.render_widget = False

    if action_name in lux.config.actions:
        lux.config.remove_action(action_name)

    def enabled_metrics_by_group(ldf):
        intent = [lux.Clause("?", data_type="quantitative"), lux.Clause("group")]
        collection = VisList(intent, ldf)
        for vis in collection:
            vis.score = 1.0
        collection.sort()
        return {
            "action": action_name,
            "description": "Quantitative columns grouped by category when enabled is true.",
            "collection": collection.showK(),
        }

    def only_enabled_frames(ldf) -> bool:
        try:
            return "enabled" in ldf.columns and bool(ldf["enabled"].all())
        except Exception:
            return False

    try:
        lux.config.register_action(action_name, enabled_metrics_by_group, only_enabled_frames)

        failing = _build_frame(pd, enabled=False)
        failing.maintain_recs()
        if action_name in failing.recommendation:
            raise AssertionError("custom action appeared even though its validator failed")

        passing = _build_frame(pd, enabled=True)
        passing.maintain_recs()
        if action_name not in passing.recommendation:
            raise AssertionError("custom action did not appear when its validator passed")
        if len(passing.recommendation[action_name]) == 0:
            raise AssertionError("custom action produced an empty recommendation collection")

        debug_text = lux.debug_info(return_string=True)
        if not isinstance(debug_text, str):
            raise AssertionError("lux.debug_info(return_string=True) did not return a string")
        _assert_contains_all(
            debug_text,
            [
                "Package Versions",
                "python",
                "lux",
                "pandas",
                "luxwidget",
                "matplotlib",
                "altair",
                "Widget Setup",
            ],
        )
    finally:
        if action_name in lux.config.actions:
            lux.config.remove_action(action_name)

    if not args.quiet:
        print("Lux configuration/custom-action smoke passed")
        print(f"- validator skipped action for disabled dataframe: {action_name}")
        print(f"- validator allowed action for enabled dataframe: {len(passing.recommendation[action_name])} charts")
        print("- debug_info returned package and widget diagnostics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
