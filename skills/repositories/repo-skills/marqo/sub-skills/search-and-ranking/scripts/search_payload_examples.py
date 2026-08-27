#!/usr/bin/env python3
"""Print safe, offline Marqo search payload examples as JSON.

The script imports only the Python standard library. It never opens sockets,
never imports marqo, and never mutates a service. Examples use placeholder
fields and reserved example.invalid URLs.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable, Dict, List

Payload = Dict[str, Any]

EXAMPLE_VECTOR = [0.12, -0.08, 0.33, 0.5]


def tensor_payload() -> Payload:
    return {
        "q": {
            "red waterproof backpack": 1.0,
            "rain cover": 0.5,
            "child backpack": -0.25,
        },
        "searchMethod": "TENSOR",
        "limit": 10,
        "offset": 0,
        "searchableAttributes": ["title", "description", "image"],
        "filter": "category:backpack AND price:[0 TO 100] AND inStock:true",
        "attributesToRetrieve": ["_id", "title", "price", "image", "rating"],
        "showHighlights": True,
        "scoreModifiers": {
            "add_to_score": [{"field_name": "rating", "weight": 0.05}],
        },
    }


def lexical_payload() -> Payload:
    return {
        "q": "red waterproof backpack",
        "searchMethod": "LEXICAL",
        "limit": 10,
        "searchableAttributes": ["title", "description"],
        "language": "en",
        "filter": "category:backpack AND price:[0 TO 100]",
        "attributesToRetrieve": ["_id", "title", "price", "brand"],
        "showHighlights": True,
    }


def hybrid_payload() -> Payload:
    return {
        "q": "red waterproof hiking backpack",
        "searchMethod": "HYBRID",
        "limit": 10,
        "offset": 0,
        "filter": "category:backpack AND price:[0 TO 100] AND inStock:true",
        "attributesToRetrieve": ["_id", "title", "price", "brand", "rating"],
        "showHighlights": True,
        "hybridParameters": {
            "retrievalMethod": "disjunction",
            "rankingMethod": "rrf",
            "alpha": 0.6,
            "rrfK": 60,
            "searchableAttributesTensor": ["title", "description", "image"],
            "searchableAttributesLexical": ["title", "description"],
            "rerankDepthTensor": 50,
            "rerankDepthLexical": 50,
            "weakAndParameters": {
                "stopwordLimit": 0.6,
                "adjustTarget": 0.2,
                "allowDropAll": False,
            },
        },
        "facets": {
            "fields": {
                "brand": {"type": "string", "maxResults": 10},
                "price": {
                    "type": "number",
                    "ranges": [
                        {"to": 50, "name": "budget"},
                        {"from": 50, "to": 100, "name": "mid"},
                        {"from": 100, "name": "premium"},
                    ],
                },
            },
            "maxResults": 10,
            "order": "desc",
        },
        "trackTotalHits": True,
    }


def multimodal_payload() -> Payload:
    return {
        "q": {
            "red hiking backpack": 1.0,
            "https://example.invalid/images/red-backpack.jpg": 0.8,
        },
        "searchMethod": "TENSOR",
        "limit": 10,
        "mediaDownloadHeaders": {"User-Agent": "marqo-search-example"},
        "filter": "category:backpack",
        "attributesToRetrieve": ["_id", "title", "image", "price"],
    }


def custom_vector_payload() -> Payload:
    return {
        "q": {
            "customVector": {
                "content": "red hiking backpack",
                "vector": EXAMPLE_VECTOR,
            }
        },
        "searchMethod": "HYBRID",
        "limit": 5,
        "hybridParameters": {
            "retrievalMethod": "disjunction",
            "rankingMethod": "rrf",
            "alpha": 0.5,
        },
        "filter": "category:backpack",
    }


def filter_payload() -> Payload:
    return {
        "q": "waterproof backpack",
        "searchMethod": "HYBRID",
        "limit": 10,
        "filter": "(category:backpack OR category:luggage) AND price:[0 TO 100] AND NOT brand:(blocked brand)",
        "hybridParameters": {
            "retrievalMethod": "disjunction",
            "rankingMethod": "rrf",
        },
    }


def recommend_payload() -> Payload:
    return {
        "recommend_request": {
            "documents": {
                "doc-red-backpack": 1.0,
                "doc-hiking-pack": 0.5,
                "doc-child-pack": -0.2,
            },
            "tensorFields": ["title", "image"],
            "interpolationMethod": "slerp",
            "excludeInputDocuments": True,
            "filter": "category:backpack",
            "limit": 10,
        },
        "equivalent_search_shape_after_interpolation": {
            "q": None,
            "searchMethod": "TENSOR",
            "limit": 10,
            "context": {
                "tensor": [{"vector": EXAMPLE_VECTOR, "weight": 1.0}],
            },
            "filter": "(category:backpack) AND NOT (_id:(doc-red-backpack) OR _id:(doc-hiking-pack) OR _id:(doc-child-pack))",
        },
    }


def ecommerce_payloads() -> Payload:
    return {
        "request": "Find red waterproof backpacks under $100, prefer recent popular listings, and de-duplicate variants.",
        "tensor": {
            "q": "red waterproof hiking backpack",
            "searchMethod": "TENSOR",
            "limit": 10,
            "filter": "category:backpack AND price:[0 TO 100]",
            "scoreModifiers": {
                "add_to_score": [{"field_name": "popularity", "weight": 0.02}],
            },
        },
        "lexical": {
            "q": "red waterproof backpack",
            "searchMethod": "LEXICAL",
            "limit": 10,
            "searchableAttributes": ["title", "description"],
            "filter": "category:backpack AND price:[0 TO 100]",
        },
        "hybrid": {
            "q": "red waterproof hiking backpack",
            "searchMethod": "HYBRID",
            "limit": 10,
            "filter": "category:backpack AND price:[0 TO 100]",
            "hybridParameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
                "alpha": 0.6,
                "rrfK": 60,
                "searchableAttributesTensor": ["title", "description", "image"],
                "searchableAttributesLexical": ["title", "description"],
            },
            "recencyParameters": {
                "recencyField": "updated_at",
                "scale": "14d",
                "decayFunction": "exponential",
                "decayTo": 0.5,
                "applyInRankingPhase": "all",
            },
            "collapseFields": [
                {
                    "name": "variant_group",
                    "sortBy": {
                        "fields": [{"fieldName": "popularity", "order": "desc"}],
                    },
                }
            ],
        },
    }


def recover_filter_payload() -> Payload:
    return {
        "invalid": {
            "q": "red backpack",
            "searchMethod": "HYBRID",
            "filter": "category IN (backpack, luggage)",
            "hybridParameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
            },
        },
        "repaired": {
            "q": "red backpack",
            "searchMethod": "HYBRID",
            "filter": "category:backpack OR category:luggage",
            "hybridParameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
            },
        },
        "repair_note": "Use IN only for _id on semi-structured indexes; use OR equality terms for ordinary fields.",
    }


def recover_params_payload() -> Payload:
    return {
        "invalid_lexical": {
            "q": {"red backpack": 1.0, "waterproof": 0.5},
            "searchMethod": "LEXICAL",
            "efSearch": 100,
            "approximate": True,
        },
        "repaired_as_tensor": {
            "q": {"red backpack": 1.0, "waterproof": 0.5},
            "searchMethod": "TENSOR",
            "efSearch": 100,
            "approximate": True,
        },
        "repaired_as_lexical": {
            "q": "red waterproof backpack",
            "searchMethod": "LEXICAL",
        },
        "invalid_hybrid_searchables": {
            "q": "red backpack",
            "searchMethod": "HYBRID",
            "searchableAttributes": ["title", "description"],
            "hybridParameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
            },
        },
        "repaired_hybrid_searchables": {
            "q": "red backpack",
            "searchMethod": "HYBRID",
            "hybridParameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
                "searchableAttributesTensor": ["title", "description"],
                "searchableAttributesLexical": ["title", "description"],
            },
        },
    }


PAYLOAD_BUILDERS: Dict[str, Callable[[], Payload]] = {
    "tensor": tensor_payload,
    "lexical": lexical_payload,
    "hybrid": hybrid_payload,
    "multimodal": multimodal_payload,
    "custom-vector": custom_vector_payload,
    "filter": filter_payload,
    "recommend": recommend_payload,
    "ecommerce": ecommerce_payloads,
    "recover-filter": recover_filter_payload,
    "recover-params": recover_params_payload,
}


def build_output(cases: List[str]) -> Payload:
    selected = cases or list(PAYLOAD_BUILDERS)
    return {
        "_meta": {
            "safe_by_default": True,
            "network_calls": False,
            "service_mutation": False,
            "description": "Offline Marqo search/recommend request payload examples.",
        },
        "payloads": {name: PAYLOAD_BUILDERS[name]() for name in selected},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe offline JSON payload examples for Marqo search and ranking.",
    )
    parser.add_argument(
        "--case",
        action="append",
        choices=sorted(PAYLOAD_BUILDERS),
        help="Only print one case. Repeat to print several cases. Default: all cases.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the available case names as JSON and exit.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list:
        data: Any = sorted(PAYLOAD_BUILDERS)
    else:
        data = build_output(args.case or [])

    if args.compact:
        print(json.dumps(data, separators=(",", ":")))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
