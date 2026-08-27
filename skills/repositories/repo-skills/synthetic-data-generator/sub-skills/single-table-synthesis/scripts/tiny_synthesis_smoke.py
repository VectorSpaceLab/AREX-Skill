#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def make_data(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "customer_id": np.arange(rows),
            "age": rng.integers(18, 70, rows),
            "income": rng.normal(50000, 8000, rows).round(2),
            "segment": rng.choice(["basic", "plus", "premium"], rows),
            "education": rng.choice(["HS", "BS", "MS"], rows),
        }
    )


def run_gaussian_copula(df: pd.DataFrame, samples: int) -> pd.DataFrame:
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.data_loader import DataLoader
    from sdgx.data_models.metadata import Metadata
    from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel

    metadata = Metadata.from_dataframe(df)
    loader = DataLoader(DataFrameConnector(df))
    model = GaussianCopulaSynthesizerModel(metadata=metadata)
    model.fit(metadata, loader)
    return model.sample(samples)


def run_ctgan(df: pd.DataFrame, samples: int, device: str) -> pd.DataFrame:
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
    from sdgx.synthesizer import Synthesizer

    synthesizer = Synthesizer(
        model=CTGANSynthesizerModel(epochs=1, batch_size=10, device=device),
        data_connector=DataFrameConnector(df),
    )
    synthesizer.fit()
    return synthesizer.sample(samples)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny SDGX synthesis smoke test with no external data.")
    parser.add_argument("--model", choices=["gaussian-copula", "ctgan"], default="gaussian-copula")
    parser.add_argument("--rows", type=int, default=60)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu", help="CTGAN device; use cpu for portable checks.")
    parser.add_argument("--output", help="Optional CSV path for sampled rows.")
    args = parser.parse_args()

    if args.rows < 20:
        raise SystemExit("Use at least 20 rows for a meaningful smoke fixture")
    df = make_data(args.rows, args.seed)
    if args.model == "gaussian-copula":
        sampled = run_gaussian_copula(df, args.samples)
    else:
        sampled = run_ctgan(df, args.samples, args.device)

    assert len(sampled) == args.samples, (len(sampled), args.samples)
    assert sampled.columns.tolist() == df.columns.tolist(), sampled.columns.tolist()
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        sampled.to_csv(out, index=False)
    print(json.dumps({"model": args.model, "rows": len(df), "samples": len(sampled), "columns": sampled.columns.tolist()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
