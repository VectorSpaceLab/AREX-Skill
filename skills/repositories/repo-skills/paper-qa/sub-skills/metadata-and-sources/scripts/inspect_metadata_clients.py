#!/usr/bin/env python3
"""Inspect PaperQA metadata client availability without making network calls.

This script imports provider classes, prints the default/all client composition,
shows verified query-shape guidance, and can optionally validate requested field
names against PaperQA's DocDetails model. It never calls provider APIs.
"""

from __future__ import annotations

import argparse
import inspect
import json
from collections.abc import Iterable
from typing import Any


def _class_names(values: Iterable[Any]) -> list[str]:
    return [getattr(value, "__name__", value.__class__.__name__) for value in values]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fields",
        nargs="*",
        default=[],
        help="Optional DocDetails fields to validate for metadata query planning.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    args = parser.parse_args()

    try:
        from paperqa.clients import ALL_CLIENTS, DEFAULT_CLIENTS, DocMetadataClient
        from paperqa.clients.client_models import DOIQuery, TitleAuthorQuery
        from paperqa.clients.crossref import CROSSREF_API_MAPPING, CrossrefProvider
        from paperqa.clients.journal_quality import JournalQualityPostProcessor
        from paperqa.clients.openalex import OpenAlexProvider
        from paperqa.clients.retractions import RetractionDataPostProcessor
        from paperqa.clients.semantic_scholar import (
            SEMANTIC_SCHOLAR_API_MAPPING,
            SemanticScholarProvider,
        )
        from paperqa.clients.unpaywall import UnpaywallProvider
        from paperqa.types import DocDetails
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(f"ERROR: could not import PaperQA metadata clients: {exc}")
        return 2

    doc_fields = set(DocDetails.model_fields)
    requested_fields = list(args.fields)
    unknown_fields = sorted(set(requested_fields) - doc_fields)

    provider_classes = [
        CrossrefProvider,
        SemanticScholarProvider,
        OpenAlexProvider,
        UnpaywallProvider,
    ]
    post_processors = [JournalQualityPostProcessor, RetractionDataPostProcessor]

    report = {
        "network_calls_made": False,
        "DocMetadataClient_signature": str(inspect.signature(DocMetadataClient)),
        "DocMetadataClient_query_signature": str(
            inspect.signature(DocMetadataClient.query)
        ),
        "DocMetadataClient_bulk_query_signature": str(
            inspect.signature(DocMetadataClient.bulk_query)
        ),
        "upgrade_doc_to_doc_details_signature": str(
            inspect.signature(DocMetadataClient.upgrade_doc_to_doc_details)
        ),
        "DEFAULT_CLIENTS": _class_names(DEFAULT_CLIENTS),
        "ALL_CLIENTS": _class_names(ALL_CLIENTS),
        "providers": _class_names(provider_classes),
        "post_processors": _class_names(post_processors),
        "query_models": {
            "DOIQuery": str(inspect.signature(DOIQuery)),
            "TitleAuthorQuery": str(inspect.signature(TitleAuthorQuery)),
        },
        "requested_fields": requested_fields,
        "unknown_requested_fields": unknown_fields,
        "known_docdetails_fields": sorted(doc_fields),
        "provider_field_maps": {
            "CrossrefProvider": sorted(CROSSREF_API_MAPPING),
            "SemanticScholarProvider": sorted(SEMANTIC_SCHOLAR_API_MAPPING),
            "OpenAlexProvider": "passes requested field names as OpenAlex select fields",
            "UnpaywallProvider": "does not use PaperQA fields optimization in provider methods",
        },
        "composition_guidance": {
            "flat": "DocMetadataClient(metadata_clients=[ProviderA, ProviderB, Processor]) merges provider results within one task, then post-processes.",
            "nested": "DocMetadataClient(metadata_clients=[[ProviderA], [ProviderB]]) tries ordered tasks and can stop early once requested fields are hydrated.",
        },
        "safe_next_step": "Use references/metadata-clients.md before making live provider calls.",
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PaperQA metadata client inspection (no network)")
        print("=" * 52)
        print(f"DocMetadataClient: {report['DocMetadataClient_signature']}")
        print(f"query: {report['DocMetadataClient_query_signature']}")
        print(f"bulk_query: {report['DocMetadataClient_bulk_query_signature']}")
        print(f"upgrade_doc_to_doc_details: {report['upgrade_doc_to_doc_details_signature']}")
        print()
        print("DEFAULT_CLIENTS:", ", ".join(report["DEFAULT_CLIENTS"]))
        print("ALL_CLIENTS:", ", ".join(report["ALL_CLIENTS"]))
        print("Providers:", ", ".join(report["providers"]))
        print("Post-processors:", ", ".join(report["post_processors"]))
        print()
        if requested_fields:
            print("Requested fields:", ", ".join(requested_fields))
            if unknown_fields:
                print("Unknown DocDetails fields:", ", ".join(unknown_fields))
            else:
                print("All requested fields are DocDetails fields.")
            print()
        print("Provider field-map keys:")
        for provider, mapping in report["provider_field_maps"].items():
            if isinstance(mapping, list):
                print(f"- {provider}: {', '.join(mapping)}")
            else:
                print(f"- {provider}: {mapping}")
        print()
        print("Composition guidance:")
        print("- Flat:", report["composition_guidance"]["flat"])
        print("- Nested:", report["composition_guidance"]["nested"])
        print()
        print(report["safe_next_step"])

    return 1 if unknown_fields else 0


if __name__ == "__main__":
    raise SystemExit(main())
