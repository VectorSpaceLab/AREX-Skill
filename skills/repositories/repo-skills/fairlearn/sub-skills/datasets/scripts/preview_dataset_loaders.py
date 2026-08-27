#!/usr/bin/env python3
"""Preview Fairlearn dataset loader signatures; optionally run one download."""

from __future__ import annotations

import argparse
import inspect
from pathlib import Path

from fairlearn import datasets


LOADERS = {
    "adult": datasets.fetch_adult,
    "acs-income": datasets.fetch_acs_income,
    "bank-marketing": datasets.fetch_bank_marketing,
    "boston": datasets.fetch_boston,
    "credit-card": datasets.fetch_credit_card,
    "diabetes-hospital": datasets.fetch_diabetes_hospital,
}

NOTES = {
    "adult": "48,842 rows; income >50K binary target; common sensitive columns include sex and race.",
    "acs-income": "Large ACSIncome loader; 10 columns AGEP,COW,SCHL,MAR,OCCP,POBP,RELP,WKHP,SEX,RAC1P; supports states=.",
    "bank-marketing": "45,211 rows; term-deposit subscription binary target.",
    "boston": "506 rows; known fairness issues; warn=True raises DataFairnessWarning by default.",
    "credit-card": "30,000 rows; default-of-credit-card-clients binary target.",
    "diabetes-hospital": "101,766 rows; readmission within 30 days binary target; mixed dtypes.",
}


def preview() -> None:
    for name, func in LOADERS.items():
        print(f"{name}: {func.__name__}{inspect.signature(func)}")
        print(f"  {NOTES[name]}")


def download_one(name: str, data_home: Path | None, states: list[str] | None):
    func = LOADERS[name]
    kwargs = {"as_frame": True, "return_X_y": False}
    if data_home is not None:
        kwargs["data_home"] = str(data_home)
    if name == "acs-income" and states:
        kwargs["states"] = states
    if name == "boston":
        kwargs["warn"] = True
    dataset = func(**kwargs)
    print(f"Downloaded {name}: data shape={getattr(dataset.data, 'shape', None)} target shape={getattr(dataset.target, 'shape', None)}")
    print("Feature names:", list(dataset.feature_names)[:12], "..." if len(dataset.feature_names) > 12 else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", choices=sorted(LOADERS), help="Optionally download and preview one loader.")
    parser.add_argument("--data-home", type=Path, help="Cache/download directory for --download.")
    parser.add_argument("--states", nargs="*", help="State abbreviations for --download acs-income.")
    args = parser.parse_args()
    preview()
    if args.download:
        download_one(args.download, args.data_home, args.states)
    else:
        print("No download requested. Add --download <loader> to fetch one dataset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
