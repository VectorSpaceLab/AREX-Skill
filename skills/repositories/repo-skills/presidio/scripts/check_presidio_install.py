#!/usr/bin/env python3
"""Check a Presidio installation without relying on any source checkout.

The check imports the public packages, optionally verifies the default spaCy
model, optionally probes Tesseract OCR, and can run a tiny analyzer/anonymizer
smoke. It does not download models, start services, or require credentials.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Iterable

DISTRIBUTIONS = {
    "presidio": "presidio",
    "presidio_analyzer": "presidio_analyzer",
    "presidio_anonymizer": "presidio_anonymizer",
    "presidio_structured": "presidio_structured",
    "presidio-image-redactor": "presidio_image_redactor",
    "presidio-cli": "presidio_cli",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check installed Presidio packages, model/OCR prerequisites, and a tiny smoke path."
    )
    parser.add_argument(
        "--skip-model-check",
        action="store_true",
        help="Do not require the default en_core_web_lg spaCy model to be importable.",
    )
    parser.add_argument(
        "--skip-tesseract-check",
        action="store_true",
        help="Do not check for the tesseract executable/pytesseract bridge.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a tiny analyzer/anonymizer smoke using the default analyzer model.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable report.",
    )
    return parser


def check_distributions() -> dict:
    results = {}
    for dist, module in DISTRIBUTIONS.items():
        entry = {"module": module}
        try:
            entry["version"] = version(dist)
            imported = importlib.import_module(module)
            entry["imported"] = True
            entry["public_file_present"] = bool(getattr(imported, "__file__", None))
        except PackageNotFoundError as exc:
            entry.update({"imported": False, "error": f"distribution not found: {exc}"})
        except Exception as exc:  # pragma: no cover - environment dependent
            entry.update({"imported": False, "error": str(exc)})
        results[dist] = entry
    return results


def check_model() -> dict:
    try:
        importlib.import_module("en_core_web_lg")
        return {"status": "present", "model": "en_core_web_lg"}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "status": "missing",
            "model": "en_core_web_lg",
            "error": str(exc),
            "recovery": "Run: python -m spacy download en_core_web_lg, or use NoOpNlpEngine for pattern-only workflows.",
        }


def check_tesseract() -> dict:
    exe = shutil.which("tesseract")
    if not exe:
        return {
            "status": "missing",
            "error": "tesseract executable not found on PATH",
            "recovery": "Install the Tesseract OCR system binary before using the default image redactor OCR path.",
        }
    try:
        import pytesseract

        return {"status": "present", "executable": exe, "version": str(pytesseract.get_tesseract_version())}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"status": "bridge-error", "executable": exe, "error": str(exc)}


def run_smoke() -> dict:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine

    text = "John Smith drivers license is AC432223"
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=text, language="en")
    anonymized = AnonymizerEngine().anonymize(text=text, analyzer_results=results)
    entities = [result.entity_type for result in results]
    if "PERSON" not in entities:
        raise AssertionError(f"Expected PERSON in analyzer output, got {entities}")
    return {"status": "passed", "entities": entities, "anonymized_text": anonymized.text}


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    report = {"distributions": check_distributions()}
    if not args.skip_model_check:
        report["model"] = check_model()
    if not args.skip_tesseract_check:
        report["tesseract"] = check_tesseract()
    if args.smoke:
        try:
            report["smoke"] = run_smoke()
        except Exception as exc:  # pragma: no cover - environment dependent
            report["smoke"] = {"status": "failed", "error": str(exc)}

    failed = []
    for name, entry in report["distributions"].items():
        if not entry.get("imported"):
            failed.append(f"{name}: {entry.get('error')}")
    if report.get("model", {}).get("status") == "missing":
        failed.append("default spaCy model en_core_web_lg is missing")
    if report.get("tesseract", {}).get("status") not in {None, "present"}:
        failed.append("Tesseract OCR prerequisite is not ready")
    if report.get("smoke", {}).get("status") == "failed":
        failed.append("default analyzer/anonymizer smoke failed")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("Presidio installation check")
        for name, entry in report["distributions"].items():
            status = "ok" if entry.get("imported") else "failed"
            print(f"- {name}: {status} {entry.get('version', '')}")
        if "model" in report:
            print(f"- en_core_web_lg model: {report['model']['status']}")
        if "tesseract" in report:
            print(f"- Tesseract OCR: {report['tesseract']['status']}")
        if "smoke" in report:
            print(f"- analyzer/anonymizer smoke: {report['smoke']['status']}")
        if failed:
            print("\nFailures:", file=sys.stderr)
            for item in failed:
                print(f"- {item}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
