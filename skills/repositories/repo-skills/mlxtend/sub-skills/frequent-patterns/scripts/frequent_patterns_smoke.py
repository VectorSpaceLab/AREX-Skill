#!/usr/bin/env python
"""Deterministic smoke test for mlxtend frequent-pattern mining.

The script imports the installed mlxtend package, builds a tiny transaction
list, encodes it with TransactionEncoder, mines itemsets, and prints association
rules. It uses only installed package APIs and the tiny in-script dataset.
"""

from __future__ import annotations

import argparse
from typing import Callable, Iterable

import pandas as pd

from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth, fpmax, hmine
from mlxtend.preprocessing import TransactionEncoder


TRANSACTIONS = [
    ["Milk", "Bread", "Eggs"],
    ["Milk", "Bread"],
    ["Milk", "Eggs"],
    ["Bread", "Eggs"],
    ["Milk", "Bread", "Eggs"],
    ["Bread", "Butter"],
    ["Milk", "Bread", "Butter"],
    ["Milk", "Bread", "Eggs"],
]

MetricName = str

ALGORITHMS: dict[str, Callable[..., pd.DataFrame]] = {
    "apriori": apriori,
    "fpgrowth": fpgrowth,
    "fpmax": fpmax,
    "hmine": hmine,
}

METRICS: tuple[MetricName, ...] = (
    "support",
    "confidence",
    "lift",
    "representativity",
    "leverage",
    "conviction",
    "zhangs_metric",
    "jaccard",
    "certainty",
    "kulczynski",
)


def encode_transactions(transactions: list[list[str]]) -> pd.DataFrame:
    """Encode transactions as a boolean one-hot pandas DataFrame."""
    encoder = TransactionEncoder()
    encoded = encoder.fit_transform(transactions)
    return pd.DataFrame(encoded, columns=encoder.columns_)


def itemset_label(value: Iterable[object]) -> str:
    """Stable human-readable label for frozenset/set/list itemsets."""
    return "{" + ", ".join(str(item) for item in sorted(value)) + "}"


def sort_itemsets(df: pd.DataFrame) -> pd.DataFrame:
    """Sort itemset rows deterministically for smoke-test output."""
    if df.empty:
        return df.copy()
    out = df.copy()
    out["_length"] = out["itemsets"].map(len)
    out["_key"] = out["itemsets"].map(lambda x: tuple(str(i) for i in sorted(x)))
    out = out.sort_values(["_length", "_key", "support"]).drop(
        columns=["_length", "_key"]
    )
    return out.reset_index(drop=True)


def display_itemsets(df: pd.DataFrame) -> str:
    out = sort_itemsets(df)
    if out.empty:
        return "<no itemsets>"
    out = out.copy()
    out["itemsets"] = out["itemsets"].map(itemset_label)
    return out.to_string(index=False)


def sort_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Sort rule rows deterministically for smoke-test output."""
    if df.empty:
        return df.copy()
    out = df.copy()
    out["_antecedents"] = out["antecedents"].map(
        lambda x: tuple(str(i) for i in sorted(x))
    )
    out["_consequents"] = out["consequents"].map(
        lambda x: tuple(str(i) for i in sorted(x))
    )
    out = out.sort_values(["_antecedents", "_consequents"]).drop(
        columns=["_antecedents", "_consequents"]
    )
    return out.reset_index(drop=True)


def display_rules(df: pd.DataFrame) -> str:
    if df.empty:
        return "<no rules>"
    out = sort_rules(df).copy()
    out["antecedents"] = out["antecedents"].map(itemset_label)
    out["consequents"] = out["consequents"].map(itemset_label)
    columns = [
        column
        for column in [
            "antecedents",
            "consequents",
            "support",
            "confidence",
            "lift",
            "leverage",
            "conviction",
        ]
        if column in out.columns
    ]
    return out[columns].round(4).to_string(index=False)


def mine_itemsets(name: str, df: pd.DataFrame, min_support: float) -> pd.DataFrame:
    """Run one configured frequent-pattern miner."""
    func = ALGORITHMS[name]
    return func(df, min_support=min_support, use_colnames=True)


def rules_for_itemsets(
    name: str,
    itemsets: pd.DataFrame,
    n_transactions: int,
    metric: str,
    min_threshold: float,
    min_support: float,
) -> pd.DataFrame:
    """Generate rules, using support-only mode for fpmax maximal itemsets."""
    if itemsets.empty:
        return pd.DataFrame()

    if name == "fpmax":
        # fpmax omits non-maximal subset supports, so full confidence/lift rules
        # are usually not available. support_only exercises the rule API safely.
        return association_rules(
            itemsets,
            num_itemsets=n_transactions,
            support_only=True,
            min_threshold=min_support,
        )

    return association_rules(
        itemsets,
        num_itemsets=n_transactions,
        metric=metric,
        min_threshold=min_threshold,
    )


def run_algorithm(
    name: str,
    df: pd.DataFrame,
    min_support: float,
    metric: str,
    min_threshold: float,
) -> None:
    print(f"\n=== {name} ===")
    itemsets = mine_itemsets(name, df, min_support)
    print("Itemsets:")
    print(display_itemsets(itemsets))

    rules = rules_for_itemsets(
        name=name,
        itemsets=itemsets,
        n_transactions=len(df),
        metric=metric,
        min_threshold=min_threshold,
        min_support=min_support,
    )
    if name == "fpmax":
        print("Rules (support_only=True because fpmax returns maximal itemsets):")
    else:
        print(f"Rules (metric={metric!r}, min_threshold={min_threshold}):")
    print(display_rules(rules))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test mlxtend frequent-pattern itemset and rule APIs."
    )
    parser.add_argument(
        "--algorithm",
        choices=("apriori", "fpgrowth", "fpmax", "hmine", "all"),
        default="all",
        help="Frequent-pattern miner to run.",
    )
    parser.add_argument(
        "--min-support",
        type=float,
        default=0.375,
        help="Minimum itemset support fraction in (0, 1].",
    )
    parser.add_argument(
        "--metric",
        choices=METRICS,
        default="confidence",
        help="Association-rule metric for non-fpmax algorithms.",
    )
    parser.add_argument(
        "--min-threshold",
        type=float,
        default=0.6,
        help="Minimum rule metric threshold for non-fpmax algorithms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = encode_transactions(TRANSACTIONS)

    print("Encoded one-hot dataframe")
    print(f"shape={df.shape}, columns={list(df.columns)}")
    print(df.astype(int).to_string(index=False))

    names = list(ALGORITHMS) if args.algorithm == "all" else [args.algorithm]
    for name in names:
        run_algorithm(
            name=name,
            df=df,
            min_support=args.min_support,
            metric=args.metric,
            min_threshold=args.min_threshold,
        )


if __name__ == "__main__":
    main()
