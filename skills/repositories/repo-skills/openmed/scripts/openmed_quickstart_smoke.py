#!/usr/bin/env python3
"""Synthetic OpenMed quickstart smoke without model downloads.

This script uses fixture loaders to exercise the same top-level APIs future
agents will normally call (`analyze_text` and `deidentify`) while avoiding
network access and real PHI.

Example:
    python openmed_quickstart_smoke.py --json
"""

from __future__ import annotations

import argparse
import json
from typing import Any

SYNTHETIC_NOTE = "History of asthma. Patient Alice Smith visited on 2026-01-15."


class ClinicalFixtureLoader:
    config = None

    def create_pipeline(self, model_name: str, **kwargs: Any):
        def pipeline(text: str, **call_kwargs: Any):
            start = text.index("asthma")
            return [
                {
                    "entity_group": "CONDITION",
                    "score": 0.99,
                    "start": start,
                    "end": start + len("asthma"),
                    "word": "asthma",
                }
            ]

        return pipeline

    def get_max_sequence_length(self, model_name: str, tokenizer: Any = None) -> int:
        return 128


class PIIFixtureLoader:
    config = None

    def create_pipeline(self, model_name: str, **kwargs: Any):
        def predict_one(text: str) -> list[dict[str, Any]]:
            start = text.index("Alice Smith")
            return [
                {
                    "entity_group": "NAME",
                    "score": 0.99,
                    "start": start,
                    "end": start + len("Alice Smith"),
                    "word": "Alice Smith",
                }
            ]

        def pipeline(text: str | list[str], **call_kwargs: Any):
            if isinstance(text, list):
                return [predict_one(item) for item in text]
            return predict_one(text)

        return pipeline

    def get_max_sequence_length(self, model_name: str, tokenizer: Any = None) -> int:
        return 128


def run_smoke(note: str) -> dict[str, Any]:
    from openmed import analyze_text, deidentify

    clinical = analyze_text(
        note,
        model_name="fixture-clinical-ner",
        loader=ClinicalFixtureLoader(),
        sentence_detection=False,
    )
    deid = deidentify(note, method="mask", loader=PIIFixtureLoader())
    return {
        "ok": True,
        "note_is_synthetic": True,
        "clinical_entities": [
            {"text": entity.text, "label": entity.label, "start": entity.start, "end": entity.end}
            for entity in clinical.entities
        ],
        "deidentified_text": deid.deidentified_text,
        "pii_count": len(deid.pii_entities),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic OpenMed API smoke check with fixture loaders.")
    parser.add_argument("--text", default=SYNTHETIC_NOTE, help="Synthetic text to analyze; do not pass real PHI.")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload.")
    args = parser.parse_args()

    payload = run_smoke(args.text)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OpenMed quickstart smoke: ok")
        print("Clinical entities:", payload["clinical_entities"])
        print("Deidentified text:", payload["deidentified_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
