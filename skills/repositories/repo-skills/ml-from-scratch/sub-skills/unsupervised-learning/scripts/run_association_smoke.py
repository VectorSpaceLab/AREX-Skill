#!/usr/bin/env python3
"""Deterministic in-memory Apriori/FPGrowth smoke checks with string normalization."""

from __future__ import annotations

import argparse
import json
import os
from numbers import Integral
from typing import Any, Iterable

os.environ.setdefault("MPLBACKEND", "Agg")

from mlfromscratch.unsupervised_learning import Apriori, FPGrowth


def default_transactions() -> list[list[str]]:
    return [
        ["milk", "bread", "eggs"],
        ["milk", "bread"],
        ["milk", "eggs"],
        ["bread", "eggs"],
        ["milk", "bread", "eggs"],
    ]


def normalize_transactions(transactions: Iterable[Iterable[str]]) -> tuple[list[list[int]], dict[int, str]]:
    """Map string items to stable integer IDs for Apriori's singleton logic."""
    normalized_strings = [sorted({str(item) for item in tx}) for tx in transactions]
    items = sorted({item for tx in normalized_strings for item in tx})
    item_to_id = {item: i + 1 for i, item in enumerate(items)}
    id_to_item = {i: item for item, i in item_to_id.items()}
    encoded = [[item_to_id[item] for item in tx] for tx in normalized_strings]
    return encoded, id_to_item


def decode_itemset(itemset: Any, id_to_item: dict[int, str]) -> Any:
    if isinstance(itemset, Integral):
        return id_to_item[int(itemset)]
    return [id_to_item[int(item)] for item in itemset]


def sort_key(itemset: Any) -> tuple[int, str]:
    if isinstance(itemset, str):
        return (1, itemset)
    return (len(itemset), ",".join(str(x) for x in itemset))


def run(args: argparse.Namespace) -> dict[str, Any]:
    transactions = default_transactions()
    encoded, id_to_item = normalize_transactions(transactions)

    apriori = Apriori(min_sup=args.apriori_min_support, min_conf=args.apriori_min_confidence)
    itemsets = [decode_itemset(itemset, id_to_item) for itemset in apriori.find_frequent_itemsets(encoded)]
    rules = []
    for rule in apriori.generate_rules(encoded):
        rules.append(
            {
                "antecedent": decode_itemset(rule.antecedent, id_to_item),
                "consequent": decode_itemset(rule.concequent, id_to_item),
                "support": round(float(rule.support), 4),
                "confidence": round(float(rule.confidence), 4),
            }
        )

    fp_growth = FPGrowth(min_sup=args.fp_min_support_count)
    fp_itemsets = fp_growth.find_frequent_itemsets(transactions)

    return {
        "transactions": transactions,
        "apriori_itemsets": sorted(itemsets, key=sort_key),
        "apriori_rules": sorted(rules, key=lambda r: (str(r["antecedent"]), str(r["consequent"]))),
        "fp_growth_itemsets": sorted(fp_itemsets, key=sort_key),
        "notes": [
            "String transactions were normalized to integer IDs for Apriori and decoded for output.",
            "FPGrowth min_sup is used as a raw support count in this implementation.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Apriori and FPGrowth on tiny in-memory transactions and print itemsets/rules as JSON."
    )
    parser.add_argument("--apriori-min-support", type=float, default=0.4, help="Apriori fractional support threshold.")
    parser.add_argument("--apriori-min-confidence", type=float, default=0.6, help="Apriori confidence threshold.")
    parser.add_argument("--fp-min-support-count", type=int, default=3, help="FPGrowth raw support-count threshold.")
    args = parser.parse_args()
    if not 0 < args.apriori_min_support <= 1:
        parser.error("--apriori-min-support must be in (0, 1]")
    if not 0 < args.apriori_min_confidence <= 1:
        parser.error("--apriori-min-confidence must be in (0, 1]")
    if args.fp_min_support_count < 1:
        parser.error("--fp-min-support-count must be positive")
    return args


def main() -> int:
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
