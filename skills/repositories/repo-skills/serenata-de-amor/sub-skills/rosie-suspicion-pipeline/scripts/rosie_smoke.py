#!/usr/bin/env python3
"""No-download smoke checks for the Rosie suspicion pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional


def add_repo_root(repo_root: Optional[str]) -> None:
    """Add local Rosie source roots without requiring installation."""
    if not repo_root:
        return

    root = Path(repo_root).expanduser().resolve()
    candidates = [root / "rosie", root]
    new_paths: List[str] = []
    for candidate in candidates:
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path and text not in new_paths:
                new_paths.append(text)
    sys.path[:0] = new_paths


def apply_legacy_compatibility_shims() -> None:
    """Patch narrow legacy aliases needed by old Rosie imports."""
    try:
        import numpy as np  # type: ignore

        for name, value in (("str", str), ("int", int), ("long", int)):
            if name not in np.__dict__:
                setattr(np, name, value)
    except Exception:
        pass

    try:
        import joblib  # type: ignore
        import sklearn.externals as sklearn_externals  # type: ignore

        setattr(sklearn_externals, "joblib", joblib)
        sys.modules.setdefault("sklearn.externals.joblib", joblib)
    except Exception:
        pass


def import_invalid_classifier():
    apply_legacy_compatibility_shims()
    from rosie.core.classifiers import InvalidCnpjCpfClassifier  # type: ignore

    return InvalidCnpjCpfClassifier


def run_invalid_cnpj_cpf_smoke() -> None:
    import pandas as pd  # type: ignore

    InvalidCnpjCpfClassifier = import_invalid_classifier()
    dataframe = pd.DataFrame(
        [
            {"recipient_id": "22472225000183", "document_type": "bill_of_sale"},
            {"recipient_id": "22472225000180", "document_type": "bill_of_sale"},
            {"recipient_id": "57725723501", "document_type": "simple_receipt"},
            {"recipient_id": "11111111111", "document_type": "simple_receipt"},
            {"recipient_id": "22472225000180", "document_type": "expense_made_abroad"},
            {"recipient_id": "22472225000180", "document_type": "unknown"},
        ]
    )
    expected = [False, True, False, True, False, True]

    classifier = InvalidCnpjCpfClassifier()
    classifier.fit(dataframe)
    classifier.transform(dataframe)
    result = [bool(value) for value in classifier.predict(dataframe)]

    if result != expected:
        raise AssertionError(
            "invalid-cnpj-cpf smoke failed: "
            f"expected {expected}, got {result}"
        )

    print(
        "PASS invalid-cnpj-cpf smoke: "
        "valid IDs, invalid IDs, abroad documents, and Federal 'unknown' "
        "document type behaved as expected."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe Rosie smoke checks. No datasets are downloaded and no "
            "services are started."
        )
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "Optional local Serenata de Amor repository root. When provided, "
            "the script adds local Rosie source roots before importing."
        ),
    )
    parser.add_argument(
        "--smoke",
        choices=("invalid-cnpj-cpf",),
        default="invalid-cnpj-cpf",
        help="Smoke check to run. Default: invalid-cnpj-cpf.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    add_repo_root(args.repo_root)

    try:
        if args.smoke == "invalid-cnpj-cpf":
            run_invalid_cnpj_cpf_smoke()
        else:
            parser.error(f"unsupported smoke: {args.smoke}")
    except Exception as exc:  # pragma: no cover - intended CLI failure path
        print(f"FAIL {args.smoke}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
