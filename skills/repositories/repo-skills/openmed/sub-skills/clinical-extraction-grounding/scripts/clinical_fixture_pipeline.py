#!/usr/bin/env python3
"""Offline synthetic clinical extraction and grounding smoke helper.

The helper uses a fixture loader and a synthetic note so it can run without
network access or model downloads. Each note line is treated as one sentence
window to keep the example deterministic and dependency-free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from openmed import analyze_text, ground
from openmed.clinical import (
    assert_context,
    deduplicate_problem_list,
    extract_lab_results,
    normalize_temporal,
    reconcile_medications,
    route_analysis,
)
from openmed.clinical.sections import classify_document, detect_sections
from openmed.clinical.exporters import build_reverse_index, to_codeable_concept
from openmed.clinical.grounding import VocabLoader, VocabSource
from openmed.clinical.relations_lite import extract_relation_candidates
from openmed.ner import available_domains, get_default_labels

SYNTHETIC_NOTE = (
    "Synthetic outpatient follow-up.\n"
    "History of Present Illness: The patient reports type 2 diabetes.\n"
    "Medications: metformin 500 mg oral daily continued.\n"
    "Assessment: No evidence of pneumonia. Hemoglobin A1c 8.1 % today.\n"
    "Family History: father has asthma.\n"
    "Plan: Follow-up in 3 days."
)

FIXTURE_PREDICTIONS: tuple[dict[str, Any], ...] = (
    {"surface": "type 2 diabetes", "label": "CONDITION", "score": 0.99},
    {"surface": "metformin", "label": "MEDICATION", "score": 0.99},
    {"surface": "500 mg", "label": "DOSAGE", "score": 0.97},
    {"surface": "oral", "label": "ROUTE", "score": 0.96},
    {"surface": "pneumonia", "label": "CONDITION", "score": 0.98},
    {"surface": "Hemoglobin A1c", "label": "LAB_TEST", "score": 0.99},
    {"surface": "8.1", "label": "LAB_VALUE", "score": 0.95},
    {"surface": "asthma", "label": "CONDITION", "score": 0.98},
)

GROUNDING_FIXTURES: dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]] = {
    "icd10cm": (
        ("E11.9", "Type 2 diabetes mellitus", ("type 2 diabetes", "T2DM")),
        ("J18.9", "Pneumonia", ("pneumonia",)),
        ("J45.909", "Asthma", ("asthma",)),
    ),
    "rxnorm": (
        ("6809", "Metformin", ("metformin",)),
    ),
    "loinc": (
        (
            "4548-4",
            "Hemoglobin A1c/Hemoglobin.total in Blood",
            ("Hemoglobin A1c", "A1c"),
        ),
    ),
}

ENTITY_SYSTEMS = {
    "CONDITION": ("icd10cm",),
    "MEDICATION": ("rxnorm",),
    "LAB_TEST": ("loinc",),
}

MODEL_NAME = "disease_detection_superclinical"
REFERENCE_TIME = "2026-06-15"


class FixtureNERLoader:
    """Deterministic token-classification stand-in for a local smoke run."""

    config = None

    def __init__(self, predictions: tuple[dict[str, Any], ...]) -> None:
        self._predictions = predictions

    def create_pipeline(self, model_name: str, **kwargs: Any):
        del model_name, kwargs
        predictions = self._predictions

        def pipeline(text: Any, **call_kwargs: Any):
            del call_kwargs
            segments = [text] if not isinstance(text, list) else list(text)
            outputs: list[list[dict[str, Any]]] = []
            for segment in segments:
                spans: list[dict[str, Any]] = []
                for prediction in predictions:
                    surface = prediction["surface"]
                    start = str(segment).find(surface)
                    if start < 0:
                        continue
                    spans.append(
                        {
                            "entity_group": prediction["label"],
                            "score": float(prediction["score"]),
                            "start": start,
                            "end": start + len(surface),
                            "word": surface,
                        }
                    )
                spans.sort(key=lambda item: item["start"])
                outputs.append(spans)
            return outputs[0] if not isinstance(text, list) else outputs

        return pipeline

    def get_max_sequence_length(self, model_name: str, tokenizer: Any = None) -> int:
        del model_name, tokenizer
        return 256


@contextmanager
def offline_env():
    """Keep the smoke helper from touching remote model or hub paths."""

    keys = ("OPENMED_OFFLINE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ[key] = "1"
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _write_tsv(path: Path, rows: tuple[tuple[str, str, tuple[str, ...]], ...]) -> Path:
    lines = ["code\tpreferred_term\tsynonyms"]
    for code, preferred_term, synonyms in rows:
        joined = "|".join(synonyms)
        lines.append(f"{code}\t{preferred_term}\t{joined}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_sentence_windows(text: str) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        start = cursor
        end = cursor + len(line)
        cursor = end
        if not line.strip():
            continue
        windows.append({"text": line, "start": start, "end": end})
    if cursor < len(text):
        tail = text[cursor:]
        if tail.strip():
            windows.append({"text": tail, "start": cursor, "end": len(text)})
    return windows


def _section_for_span(sections: tuple[dict[str, Any], ...], start: int, end: int) -> str | None:
    for section in sections:
        section_start = int(section["start"])
        section_end = int(section["end"])
        if section_start <= start and end <= section_end:
            return str(section["label"])
    return None


def _build_vocab_loader(root: Path) -> VocabLoader:
    registry: dict[str, VocabSource] = {}
    for system, rows in GROUNDING_FIXTURES.items():
        fixture = _write_tsv(root / f"{system}.tsv", rows)
        registry[system] = VocabSource(
            system=system,
            path=fixture,
            sha256=_sha256(fixture),
            version="synthetic-1",
        )
    return VocabLoader(cache_dir=root / "cache", local_only=True, registry=registry)


def _ground_targets(
    contextualized_entities: list[dict[str, Any]],
    loader: VocabLoader,
) -> tuple[list[dict[str, Any]], list[Any]]:
    records: list[dict[str, Any]] = []
    grounded_spans: list[Any] = []
    for entity in contextualized_entities:
        systems = ENTITY_SYSTEMS.get(str(entity.get("label")))
        if systems is None:
            continue
        grounded = ground(entity, systems=systems, loader=loader, offline=True)
        if not grounded:
            continue
        selected = grounded[0]
        grounded_spans.append(selected)
        records.append(
            {
                "entity": entity,
                "audit": selected.to_audit_dict(),
                "codeable_concept": to_codeable_concept(selected),
            }
        )
    return records, grounded_spans


def _build_problem_list(
    contextualized_entities: list[dict[str, Any]],
    grounded_spans: list[Any],
) -> list[dict[str, Any]]:
    by_text = {span.text: span for span in grounded_spans}
    mentions: list[dict[str, Any]] = []
    for entity in contextualized_entities:
        if str(entity.get("label")) != "CONDITION":
            continue
        grounded = by_text.get(str(entity.get("text")))
        if grounded is None or not grounded.candidates:
            continue
        mentions.append(
            {
                "text": entity["text"],
                "system": grounded.candidates[0].system,
                "code": grounded.candidates[0].code,
                "offset": (int(entity["start"]), int(entity["end"])),
                "negation": entity["negation"],
                "temporality": entity["temporality"],
                "certainty": entity["uncertainty"],
                "experiencer": entity["experiencer"],
            }
        )
    return [asdict(problem) for problem in deduplicate_problem_list(mentions)]


def _build_medication_summary(
    contextualized_entities: list[dict[str, Any]],
    grounded_spans: list[Any],
) -> list[dict[str, Any]]:
    by_text = {span.text: span for span in grounded_spans}
    mentions: list[dict[str, Any]] = []
    for entity in contextualized_entities:
        if str(entity.get("label")) != "MEDICATION":
            continue
        grounded = by_text.get(str(entity.get("text")))
        if grounded is None:
            continue
        mentions.append(
            {
                "text": entity["text"],
                "ingredient": grounded.display or entity["text"],
                "system": grounded.candidates[0].system,
                "code": grounded.candidates[0].code,
                "dose": "500 mg",
                "route": "oral",
                "status": "continued",
                "effective_time": REFERENCE_TIME,
                "offset": (int(entity["start"]), int(entity["end"])),
                "section": entity.get("section"),
            }
        )
    return [record.to_dict() for record in reconcile_medications(mentions, document_id="synthetic-note-1")]


def _build_relations(
    note: str,
    contextualized_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        candidate.to_dict()
        for candidate in extract_relation_candidates(note, contextualized_entities)
    ]


def _build_lab_results(
    note: str,
    contextualized_entities: list[dict[str, Any]],
    sections: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    return [
        lab_result.to_dict()
        for lab_result in extract_lab_results(note, contextualized_entities, sections=sections)
    ]


def _build_timelines(note: str) -> list[dict[str, Any]]:
    phrase = "in 3 days"
    start = note.index(phrase)
    end = start + len(phrase)
    return [
        record.to_dict()
        for record in normalize_temporal(note, [(start, end)], reference_time=REFERENCE_TIME)
    ]


def build_report() -> dict[str, Any]:
    """Run the deterministic smoke path and return JSON-ready output."""

    with offline_env(), tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        loader = _build_vocab_loader(root)
        sentence_windows = _line_sentence_windows(SYNTHETIC_NOTE)
        sections = detect_sections(SYNTHETIC_NOTE)
        section_payloads = tuple(dict(section) for section in sections)
        classification = classify_document(SYNTHETIC_NOTE)

        analysis = analyze_text(
            SYNTHETIC_NOTE,
            model_name=MODEL_NAME,
            loader=FixtureNERLoader(FIXTURE_PREDICTIONS),
            sentence_detection=False,
            confidence_threshold=0.4,
            group_entities=False,
            metadata={"synthetic": True, "fixture_loader": True},
        )
        contextualized_entities = assert_context(
            SYNTHETIC_NOTE,
            analysis.to_dict()["entities"],
            sentences=sentence_windows,
            sections=section_payloads,
        )
        for entity in contextualized_entities:
            entity["section"] = _section_for_span(
                section_payloads,
                int(entity["start"]),
                int(entity["end"]),
            )

        analysis_payload = analysis.to_dict()
        analysis_payload["entities"] = contextualized_entities
        metadata = analysis_payload.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["synthetic"] = True
            metadata["sentence_windows"] = sentence_windows
            metadata["sections"] = list(section_payloads)
            metadata["fixture_loader"] = True

        routed = route_analysis(
            SYNTHETIC_NOTE,
            analysis_payload,
            sections=section_payloads,
            language="en",
        )

        grounding_records, grounded_spans = _ground_targets(
            contextualized_entities,
            loader,
        )
        grounding_reverse_index = {
            f"{system}|{code}": [list(offset) for offset in offsets]
            for (system, code), offsets in build_reverse_index(grounded_spans).items()
        }

        report = {
            "note": SYNTHETIC_NOTE,
            "model_selection": {
                "model_name": MODEL_NAME,
                "family_hint": "clinical disease detector",
                "confidence_threshold": 0.4,
                "sentence_detection": False,
            },
            "classification": classification,
            "sentence_windows": sentence_windows,
            "sections": list(section_payloads),
            "analysis": routed.to_dict(),
            "grounding": grounding_records,
            "grounding_reverse_index": grounding_reverse_index,
            "problem_list": _build_problem_list(contextualized_entities, grounded_spans),
            "medication_reconciliation": _build_medication_summary(
                contextualized_entities,
                grounded_spans,
            ),
            "relations": _build_relations(SYNTHETIC_NOTE, contextualized_entities),
            "lab_results": _build_lab_results(SYNTHETIC_NOTE, contextualized_entities, section_payloads),
            "timelines": _build_timelines(SYNTHETIC_NOTE),
            "zero_shot_preview": {
                "domains": available_domains(),
                "label_defaults": {
                    domain: get_default_labels(domain)[:5]
                    for domain in ("biomedical", "disease", "pharmaceutical", "oncology")
                    if domain in available_domains()
                },
            },
        }
        return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a synthetic OpenMed clinical extraction, context, and grounding fixture pipeline."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit a compact JSON payload instead of pretty-printed JSON.",
    )
    args = parser.parse_args()

    report = build_report()
    if args.compact:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
