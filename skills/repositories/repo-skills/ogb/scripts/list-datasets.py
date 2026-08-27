#!/usr/bin/env python3
"""Print the installed OGB dataset catalog from packaged metadata."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import ogb


def family_table(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, index_col=0, keep_default_na=False)
    rows = []
    for name in df.columns:
        rows.append(
            {
                "dataset": name,
                "task": df.loc["task type", name] if "task type" in df.index else "",
                "metric": df.loc["eval metric", name] if "eval metric" in df.index else "",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(ogb.__file__).resolve().parent
    families = [
        ("graphproppred", root / "graphproppred" / "master.csv"),
        ("nodeproppred", root / "nodeproppred" / "master.csv"),
        ("linkproppred", root / "linkproppred" / "master.csv"),
    ]

    for family, csv_path in families:
        print(f"[{family}]")
        table = family_table(csv_path)
        for _, row in table.iterrows():
            print(f"- {row['dataset']}: {row['task']} ({row['metric']})")
        print()

    print("[lsc]")
    print("- PCQM4M / PCQM4Mv2")
    print("- MAG240M")
    print("- WikiKG90M / WikiKG90Mv2")


if __name__ == "__main__":
    main()
