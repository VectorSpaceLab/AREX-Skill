#!/usr/bin/env python3
"""Run a deterministic, offline MOABB analysis/plot/timeline smoke check.

The output directory must already exist. The script writes only the named
fixture artifacts below and never downloads data or reads the source checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create deterministic synthetic MOABB analysis figures and "
            "FakeDataset timeline SVGs in an existing directory."
        )
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Existing directory for smoke outputs; it is not created.",
    )
    return parser


def _save(fig, path: Path) -> None:
    """Save a figure without a timestamp and close it."""
    import matplotlib.pyplot as plt

    try:
        fig.savefig(path, bbox_inches="tight", metadata={"Date": None})
    finally:
        plt.close(fig)


def _fixture():
    import pandas as pd

    rows = []
    # Four complete subject pairs per dataset make the paired statistics path
    # deterministic while retaining enough rows to catch accidental unpaired
    # pivots. The score is treated as multiclass accuracy in this fixture.
    for dataset, base in (("DsetAlpha", 0.60), ("DsetBeta", 0.55)):
        for subject in range(1, 5):
            for pipeline, delta, slope in (
                ("Reference", 0.00, 0.01),
                ("Candidate", 0.08, 0.015),
            ):
                rows.append(
                    {
                        "dataset": dataset,
                        "pipeline": pipeline,
                        "subject": subject,
                        "session": "0",
                        "score": base + delta + subject * slope,
                        "samples_test": 60,
                        "n_classes": 3,
                        "time": 0.1,
                        "samples": 120,
                        "channels": 3,
                        "n_sessions": 1,
                    }
                )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    output_dir = args.output_dir
    if not output_dir.exists():
        parser.error(f"output directory does not exist: {output_dir}")
    if not output_dir.is_dir():
        parser.error(f"output path is not a directory: {output_dir}")

    # Select Agg before importing MOABB plotting/timeline modules.
    import matplotlib

    matplotlib.use("Agg")

    try:
        from moabb.analysis.chance_level import chance_by_chance
        from moabb.analysis.meta_analysis import (
            compute_dataset_statistics,
            find_significant_differences,
        )
        from moabb.analysis.plotting import (
            distribution_plot,
            paired_plot,
            score_plot,
            summary_plot,
        )
        from moabb.analysis.timeline import (
            class_balance_svg,
            session_structure_svg,
            stimulus_timeline_svg,
        )
        from moabb.datasets.fake import FakeDataset

        df = _fixture()
        levels = chance_by_chance(df, alpha=[0.05, 0.01])
        stats = compute_dataset_statistics(df)
        p_values, effects = find_significant_differences(stats)

        score_fig, _ = score_plot(df, chance_level=levels)
        _save(score_fig, output_dir / "score.svg")
        distribution_fig, _ = distribution_plot(df, chance_level=levels)
        _save(distribution_fig, output_dir / "distribution.svg")
        paired_fig = paired_plot(
            df, "Reference", "Candidate", chance_level=levels
        )
        _save(paired_fig, output_dir / "paired.svg")
        summary_fig = summary_plot(p_values, effects, simplify=False)
        _save(summary_fig, output_dir / "summary.svg")

        dataset = FakeDataset(
            event_list=("left_hand", "right_hand"),
            n_sessions=2,
            n_runs=1,
            n_subjects=2,
            n_events=12,
            duration=30,
            seed=7,
        )
        (output_dir / "timeline.svg").write_text(
            stimulus_timeline_svg(dataset, show_annotations=False), encoding="utf-8"
        )
        balance = class_balance_svg(dataset)
        if balance is not None:
            (output_dir / "class-balance.svg").write_text(balance, encoding="utf-8")
        structure = session_structure_svg(dataset)
        if structure is not None:
            (output_dir / "session-structure.svg").write_text(
                structure, encoding="utf-8"
            )

        stats.to_csv(output_dir / "stats.csv", index=False)
        manifest = {
            "rows": int(len(df)),
            "datasets": sorted(df["dataset"].unique().tolist()),
            "pipelines": sorted(df["pipeline"].unique().tolist()),
            "metric_fixture": "multiclass accuracy",
            "n_classes": 3,
            "plotly_available": importlib.util.find_spec("plotly") is not None,
            "core_outputs": sorted(
                p.name
                for p in output_dir.iterdir()
                if p.is_file()
                and p.suffix in {".svg", ".csv"}
                and p.name in {
                    "score.svg",
                    "distribution.svg",
                    "paired.svg",
                    "summary.svg",
                    "timeline.svg",
                    "class-balance.svg",
                    "session-structure.svg",
                    "stats.csv",
                }
            ),
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception as exc:  # pragma: no cover - CLI error surface
        parser.error(f"offline smoke check failed: {type(exc).__name__}: {exc}")

    print(f"wrote deterministic analysis smoke outputs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
