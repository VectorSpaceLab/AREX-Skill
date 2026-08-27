#!/usr/bin/env python3
"""Check an installed Snorkel environment without relying on a source checkout."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict


def _dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _import_status(module: str) -> Dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _check_spacy_model() -> Dict[str, Any]:
    status = _import_status("spacy")
    if not status["ok"]:
        return status
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
        doc = nlp("Jane Doe wrote a rule.")
        return {"ok": True, "tokens": len(doc), "first_token_pos": doc[0].pos_}
    except Exception as exc:  # pragma: no cover - optional dependency gate
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _check_spark() -> Dict[str, Any]:
    java = subprocess.run(
        ["java", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    java_line = (java.stderr or java.stdout).splitlines()[0] if (java.stderr or java.stdout) else "unavailable"
    pyspark = _import_status("pyspark")
    if not pyspark["ok"]:
        return {"ok": False, "java": java_line, "pyspark": pyspark}
    try:
        os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
        from pyspark import SparkContext

        sc = SparkContext.getOrCreate()
        spark_version = sc.version
        sc.stop()
        return {"ok": True, "java": java_line, "spark_version": spark_version}
    except Exception as exc:  # pragma: no cover - optional backend gate
        return {"ok": False, "java": java_line, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an installed Snorkel package and optional local backends.")
    parser.add_argument("--check-spacy-model", action="store_true", help="Load en_core_web_sm with spaCy.")
    parser.add_argument("--check-spark", action="store_true", help="Start a tiny local SparkContext.")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "distributions": {
            name: _dist_version(name)
            for name in ["snorkel", "torch", "pandas", "numpy", "scipy", "scikit-learn", "tensorboard"]
        },
        "imports": {
            module: _import_status(module)
            for module in [
                "snorkel",
                "snorkel.labeling",
                "snorkel.classification",
                "snorkel.slicing",
                "snorkel.preprocess",
                "snorkel.map",
                "snorkel.augmentation",
                "snorkel.analysis",
                "snorkel.synthetic",
            ]
        },
        "optional_imports": {
            module: _import_status(module)
            for module in ["dask.dataframe", "distributed", "spacy", "pyspark"]
        },
    }
    if args.check_spacy_model:
        report["spacy_model"] = _check_spacy_model()
    if args.check_spark:
        report["spark"] = _check_spark()

    print(json.dumps(report, indent=2, sort_keys=True))
    required_ok = all(item["ok"] for item in report["imports"].values())
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
