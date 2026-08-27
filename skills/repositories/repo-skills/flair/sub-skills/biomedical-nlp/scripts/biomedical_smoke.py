#!/usr/bin/env python3
"""Safe biomedical NLP smoke checks for pip-installed Flair.

Default mode performs a dry run that requires no Flair import, no model download,
and no dictionary download. Use --dry-run to make that mode explicit. Add
--run-local-linker to execute a tiny in-memory exact-match EntityMentionLinker
workflow with the installed public Flair package.

Examples:
  python scripts/biomedical_smoke.py --dry-run --json
  python scripts/biomedical_smoke.py --run-local-linker --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
import traceback
from typing import Any


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def dry_run() -> dict[str, Any]:
    return {
        "ok": True,
        "mode": "dry-run",
        "python": sys.version.split()[0],
        "flair_available": package_available("flair"),
        "torch_available": package_available("torch"),
        "scispacy_available_optional_unverified": package_available("scispacy"),
        "pyab3p_available_optional_unverified": package_available("pyab3p"),
        "flair_device_env": os.environ.get("FLAIR_DEVICE", "<unset; Flair chooses at import time>"),
        "flair_cache_root_env": os.environ.get("FLAIR_CACHE_ROOT", "<unset; Flair defaults to user cache>"),
        "downloads_attempted": False,
        "notes": [
            "Default mode does not import Flair and does not download models or dictionaries.",
            "CPU baseline: set FLAIR_DEVICE=cpu before importing Flair for deterministic CPU behavior.",
            "SciSpaCy and pyab3p are optional and unverified unless separately installed and probed.",
        ],
    }


def _candidate(concept_id: str, concept_name: str, synonyms: list[str]):
    from flair.data import EntityCandidate

    return EntityCandidate(
        concept_id=concept_id,
        concept_name=concept_name,
        database_name="DEMO",
        synonyms=synonyms,
    )


def _build_exact_linker(*, entity_type: str, label_type: str, dataset_name: str, candidates: list[Any]):
    from flair.datasets.entity_linking import InMemoryEntityLinkingDictionary
    from flair.models import EntityMentionLinker
    from flair.models.entity_mention_linking import BioSynEntityPreprocessor

    dictionary = InMemoryEntityLinkingDictionary(candidates=candidates, dataset_name=dataset_name)
    return EntityMentionLinker.build(
        "exact-string-match",
        dictionary=dictionary,
        dataset_name=dataset_name,
        entity_type=entity_type,
        hybrid_search=False,
        label_type=label_type,
        preprocessor=BioSynEntityPreprocessor(),  # no pyab3p dependency
    )


def run_local_linker() -> dict[str, Any]:
    """Run tiny type-specific exact-match EntityMentionLinker workflows with no external data."""
    os.environ.setdefault("FLAIR_DEVICE", "cpu")

    # Flair logs an informational line during linker prediction. Disable logging
    # in this smoke path so --json remains machine-readable.
    logging.disable(logging.CRITICAL)

    from flair.data import Sentence

    text = "TP53 interacts with breast cancer"
    sentence = Sentence(text)

    # Manually add two NER mentions so this smoke does not load a pretrained NER model.
    tokens = [token.text for token in sentence]
    if tokens[:1] != ["TP53"] or tokens[-2:] != ["breast", "cancer"]:
        raise AssertionError(f"Unexpected tokenization for smoke text: {tokens}")

    sentence[0:1].add_label("ner", "Gene")
    sentence[len(sentence) - 2 : len(sentence)].add_label("ner", "Disease")

    gene_linker = _build_exact_linker(
        entity_type="gene",
        label_type="gene-link",
        dataset_name="DEMO-GENE",
        candidates=[_candidate("7157", "TP53", ["tumor protein p53", "TRP53"])],
    )
    disease_linker = _build_exact_linker(
        entity_type="disease",
        label_type="disease-link",
        dataset_name="DEMO-DISEASE",
        candidates=[_candidate("MESH:D001943", "Breast Neoplasms", ["breast cancer"])],
    )

    # Explicit layer/type filters make the NER-vs-linking boundary visible.
    gene_linker.predict(
        sentence,
        entity_label_types={"ner": {"Gene"}},
        pred_label_type="gene-link",
        top_k=1,
    )
    disease_linker.predict(
        sentence,
        entity_label_types={"ner": {"Disease"}},
        pred_label_type="disease-link",
        top_k=1,
    )

    ner_labels = [
        {
            "text": label.data_point.text,
            "value": label.value,
            "start": label.data_point.start_position,
            "end": label.data_point.end_position,
        }
        for label in sentence.get_labels("ner")
    ]
    link_layers = {
        layer: [
            {
                "text": label.data_point.text,
                "value": label.value,
                "name": label.metadata.get("name"),
                "score": label.score,
            }
            for label in sentence.get_labels(layer)
        ]
        for layer in ["gene-link", "disease-link"]
    }
    combined_links = link_layers["gene-link"] + link_layers["disease-link"]

    expected_by_layer = {
        "gene-link": {"7157"},
        "disease-link": {"MESH:D001943"},
    }
    for layer, expected_values in expected_by_layer.items():
        found_values = {label["value"] for label in link_layers[layer]}
        if found_values != expected_values:
            raise AssertionError(
                f"Expected {layer} IDs {sorted(expected_values)}, found {sorted(found_values)}: {link_layers[layer]}"
            )

    import flair

    return {
        "ok": True,
        "mode": "local-linker",
        "flair_version": getattr(flair, "__version__", "unknown"),
        "flair_device": str(getattr(flair, "device", "unknown")),
        "downloads_attempted": False,
        "workflow": "manual NER spans + two in-memory exact-string-match EntityMentionLinker instances",
        "ner_layer": ner_labels,
        "link_layers": link_layers,
        "link_layer": combined_links,
        "optional_scispacy_available_unverified": package_available("scispacy"),
        "optional_pyab3p_available_unverified": package_available("pyab3p"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe Flair biomedical NLP smoke checks.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform only environment/package checks. This is the default and does not import Flair.",
    )
    mode.add_argument(
        "--run-local-linker",
        action="store_true",
        help="Import Flair and run a tiny in-memory exact-match linker. No model or dictionary downloads are used.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = run_local_linker() if args.run_local_linker else dry_run()
    except ModuleNotFoundError as exc:
        result = {
            "ok": False,
            "mode": "local-linker" if args.run_local_linker else "dry-run",
            "downloads_attempted": False,
            "error": f"{type(exc).__name__}: {exc}",
            "hint": "Install the public flair package in the active Python environment, then rerun this smoke script.",
        }
    except Exception as exc:  # noqa: BLE001 - smoke script reports failures clearly.
        result = {
            "ok": False,
            "mode": "local-linker" if args.run_local_linker else "dry-run",
            "downloads_attempted": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=8),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
        if result.get("ok") and not args.run_local_linker:
            print("\nTip: add --run-local-linker to execute the no-download in-memory linker smoke.")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
