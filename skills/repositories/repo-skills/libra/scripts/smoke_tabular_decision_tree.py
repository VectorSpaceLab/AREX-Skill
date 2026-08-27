#!/usr/bin/env python3
"""Synthetic CPU smoke test for Libra tabular decision trees."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import sys

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
for candidate in (SCRIPT_DIR, REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from libra_compat import apply


def build_fixture(csv_path: Path) -> None:
    rng = np.random.default_rng(7)
    rows = []
    for idx in range(24):
        label = 'NEAR_OCEAN' if idx % 2 == 0 else 'INLAND'
        rows.append(
            {
                'feature_a': int(rng.integers(0, 10)),
                'feature_b': float(rng.normal()),
                'ocean_proximity': label,
            }
        )
    pd.DataFrame(rows).to_csv(csv_path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run a tiny synthetic Libra tabular smoke test.')
    parser.add_argument('--instruction', default='predict ocean proximity', help='Instruction to route to the target column.')
    parser.add_argument('--rows', type=int, default=24, help='Synthetic row count to generate.')
    args = parser.parse_args()

    apply()

    from libra import client
    apply()

    client.required_installations = lambda self: None

    with tempfile.TemporaryDirectory(prefix='libra-tabular-smoke-') as tmpdir:
        csv_path = Path(tmpdir) / 'smoke.csv'
        build_fixture(csv_path)
        c = client(str(csv_path))
        c.decision_tree_query(args.instruction, test_size=0.25)
        model = c.models['decision_tree']
        print('model-key:', 'decision_tree')
        print('target:', model['target'])
        print('accuracy:', model['accuracy_score'])
        print('keys:', ','.join(sorted(model.keys())))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
