#!/usr/bin/env python3
"""Inspect Libra's tabular client surface."""
from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
REPO_ROOT = SCRIPT_DIR.parents[5]
for candidate in (ROOT / 'scripts', REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from libra_compat import apply

TABULAR_METHODS = [
    'neural_network_query',
    'regression_query_ann',
    'classification_query_ann',
    'svm_query',
    'nearest_neighbor_query',
    'decision_tree_query',
    'kmeans_clustering_query',
    'content_recommender_query',
    'xgboost_query',
    'tune',
    'predict',
    'analyze',
    'plots',
    'info',
    'model',
    'accuracy',
    'losses',
    'target',
    'operators',
    'dashboard',
]


def collect_rows():
    apply()
    from libra import client
    apply()

    rows = []
    for name in TABULAR_METHODS:
        attr = getattr(client, name)
        try:
            signature = str(inspect.signature(attr))
        except (TypeError, ValueError):
            signature = '<no signature>'
        rows.append({'name': name, 'signature': signature})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect the Libra tabular modeling surface.')
    parser.add_argument('--json', action='store_true', help='Emit JSON instead of text.')
    parser.add_argument('--methods-only', action='store_true', help='Print only method names.')
    args = parser.parse_args()

    rows = collect_rows()
    if args.methods_only:
        for row in rows:
            print(row['name'])
        return 0

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print('Tabular Libra methods:')
        for row in rows:
            print(f"- {row['name']}{row['signature']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
