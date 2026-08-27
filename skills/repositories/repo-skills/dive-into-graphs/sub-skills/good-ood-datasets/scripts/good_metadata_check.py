#!/usr/bin/env python3
"""Tiny DIG GOOD metadata smoke check.

Imports dataset classes and prints their supported domain metadata. No downloads.
"""
import argparse
import inspect
import json

from dig.oodgraph import GOODArxiv, GOODCBAS, GOODCMNIST, GOODHIV, GOODMotif, GOODPCBA, GOODZINC, GOODCora

DATASETS = {
    "GOODHIV": {"domains": ["scaffold", "size"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODPCBA": {"domains": ["scaffold", "size"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODZINC": {"domains": ["scaffold", "size"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODCMNIST": {"domains": ["color"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODMotif": {"domains": ["basis", "size"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODCora": {"domains": ["word", "degree"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODArxiv": {"domains": ["time", "degree"], "shifts": ["no_shift", "covariate", "concept"]},
    "GOODCBAS": {"domains": ["color"], "shifts": ["no_shift", "covariate", "concept"]},
}


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG GOOD metadata check.")
    parser.parse_args()
    classes = [GOODHIV, GOODPCBA, GOODZINC, GOODCMNIST, GOODMotif, GOODCora, GOODArxiv, GOODCBAS]
    print(json.dumps({
        "loaded_classes": [cls.__name__ for cls in classes],
        "load_signature": str(inspect.signature(GOODHIV.load)),
        "datasets": DATASETS,
    }, indent=2, sort_keys=True))
    print("good_metadata_check: ok")


if __name__ == "__main__":
    main()
