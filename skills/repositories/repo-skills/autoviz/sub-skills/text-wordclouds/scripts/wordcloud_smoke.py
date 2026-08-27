#!/usr/bin/env python3
"""Run a safe AutoViz text and wordcloud smoke test.

Usage:
  python wordcloud_smoke.py --outdir wordcloud-smoke-output
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from autoviz.AutoViz_NLP import clean_steps, clean_text, draw_wordcloud_from_dataframe


def build_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "text": [
                "quick brown fox jumps over data",
                "automated visualization finds patterns",
                "data quality and word clouds",
                "nlp text columns are useful for summaries",
            ]
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default="wordcloud-smoke-output", help="Directory for the generated image")
    args = parser.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    df = build_dataframe()
    wc = draw_wordcloud_from_dataframe(df, "text")
    outpath = outdir / "wordcloud.png"
    wc.to_file(str(outpath))
    sample = clean_text(clean_steps("AutoViz cleans URLs https://example.com and emojis 😊"))
    print(f"Wordcloud saved to {outpath}")
    print(f"Sample cleaned text: {sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
