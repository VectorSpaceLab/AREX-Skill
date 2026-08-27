#!/usr/bin/env python3
"""Probe the non-model prerequisites of the legacy KNN label workflow.

This script avoids pyfasttext and the large fastText model file. It focuses on
feature-shape validation, positional base-info alignment, and label-file sanity.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from label_file_check import parse_label_file


def coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "##" in value:
            return [part.strip() for part in value.split("##") if part.strip()]
        value = value.strip()
        return [value] if value else []
    return [str(value).strip()]


def normalize_item(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise TypeError("item must be a JSON object")
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("item.title is required")
    return {
        "title": title.strip(),
        "openTypeList": coerce_list(data.get("openTypeList")),
        "baseInfoKeyList": coerce_list(data.get("baseInfoKeyList")),
        "baseInfoValueList": coerce_list(data.get("baseInfoValueList")),
        "label": data.get("label"),
    }


def load_json_payload(source: str) -> Any:
    path = Path(source)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = source
    return json.loads(text)


def load_item(source: str) -> Dict[str, Any]:
    payload = load_json_payload(source)
    return normalize_item(payload)


def load_training_items(source: Optional[str]) -> List[Dict[str, Any]]:
    if source is None:
        return build_demo_training_items()
    path = Path(source)
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
    else:
        text = source.strip()

    if not text:
        return []
    if text.startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("training set JSON must be an array")
        return [normalize_item(item) for item in payload]

    items: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(normalize_item(json.loads(line)))
    return items


def build_demo_items() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    item_a = normalize_item(
        {
            "title": "苹果",
            "openTypeList": "水果##植物",
            "baseInfoKeyList": "中文名##别名##科",
            "baseInfoValueList": "苹果##频果##蔷薇科",
        }
    )
    item_b = normalize_item(
        {
            "title": "小麦",
            "openTypeList": "植物##谷物",
            "baseInfoKeyList": "中文名##科##别名",
            "baseInfoValueList": "小麦##禾本科##麦子",
        }
    )
    return item_a, item_b


def build_demo_training_items() -> List[Dict[str, Any]]:
    return [
        normalize_item(
            {
                "title": "苹果",
                "openTypeList": "水果##植物",
                "baseInfoKeyList": "中文名##别名##科",
                "baseInfoValueList": "苹果##频果##蔷薇科",
            }
        ),
        normalize_item(
            {
                "title": "梨",
                "openTypeList": "水果##植物",
                "baseInfoKeyList": "中文名##别名##科",
                "baseInfoValueList": "梨##白梨##蔷薇科",
            }
        ),
        normalize_item(
            {
                "title": "小麦",
                "openTypeList": "植物##谷物",
                "baseInfoKeyList": "中文名##科",
                "baseInfoValueList": "小麦##禾本科",
            }
        ),
    ]


def unique_tokens_for_training(items: List[Dict[str, Any]], field: str) -> Dict[str, float]:
    doc_freq: Counter = Counter()
    for item in items:
        tokens = set(coerce_list(item.get(field)))
        for token in tokens:
            doc_freq[token] += 1
    total = float(len(items)) if items else 1.0
    return {token: math.log(total / freq) for token, freq in doc_freq.items() if freq > 0}


def positional_map(keys: List[str], values: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for idx, key in enumerate(keys):
        if idx < len(values):
            mapping[key] = values[idx]
    return mapping


def summarize_pair(
    item_a: Dict[str, Any],
    item_b: Dict[str, Any],
    training_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    training_items = training_items or []
    open_type_idf = unique_tokens_for_training(training_items, "openTypeList") if training_items else {}
    base_info_key_idf = unique_tokens_for_training(training_items, "baseInfoKeyList") if training_items else {}

    open_a = item_a["openTypeList"][:10]
    open_b = item_b["openTypeList"][:10]
    key_a = item_a["baseInfoKeyList"]
    key_b = item_b["baseInfoKeyList"]
    val_a = item_a["baseInfoValueList"]
    val_b = item_b["baseInfoValueList"]

    shared_open_types = sorted(set(open_a) & set(open_b))
    shared_keys = sorted(set(key_a) & set(key_b))
    pos_a = positional_map(key_a, val_a)
    pos_b = positional_map(key_b, val_b)

    equal_key_value_pairs = [key for key in shared_keys if pos_a.get(key) == pos_b.get(key)]
    shared_key_weight = sum(base_info_key_idf.get(key, 1.0) for key in shared_keys)
    equal_key_value_weight = sum(base_info_key_idf.get(key, 1.0) for key in equal_key_value_pairs)

    return {
        "title_pair": [item_a["title"], item_b["title"]],
        "legacy_notes": [
            "title and openTypeList similarity use fastText in the source classifier",
            "baseInfoKeyList and baseInfoValueList are compared without fastText",
            "baseInfoValueList is aligned by key position in the legacy source",
        ],
        "non_model_prerequisites": {
            "required_fields": ["title", "openTypeList", "baseInfoKeyList", "baseInfoValueList"],
            "positional_alignment_required": True,
            "model_free_feature_groups": ["baseInfoKeyList", "baseInfoValueList"],
        },
        "shape": {
            "openType_prefix_lengths": [len(open_a), len(open_b)],
            "baseInfo_key_lengths": [len(key_a), len(key_b)],
            "baseInfo_value_lengths": [len(val_a), len(val_b)],
            "truncated_openType_pair_count": len(open_a) * len(open_b),
            "shared_open_types": shared_open_types,
            "shared_baseInfo_keys": shared_keys,
            "equal_key_value_pairs": equal_key_value_pairs,
            "mismatched_baseInfo_lengths": len(key_a) != len(val_a) or len(key_b) != len(val_b),
        },
        "weights": {
            "shared_baseInfo_key_weight": shared_key_weight,
            "equal_baseInfo_value_weight": equal_key_value_weight,
            "openType_idf": open_type_idf,
            "baseInfoKey_idf": base_info_key_idf,
        },
        "fasttext_required_for": ["title_similarity", "openTypeList_similarity"],
    }


def build_report(
    item_a: Dict[str, Any],
    item_b: Dict[str, Any],
    training_items: Optional[List[Dict[str, Any]]] = None,
    label_file: Optional[str] = None,
) -> Dict[str, Any]:
    report = summarize_pair(item_a, item_b, training_items=training_items)
    if label_file:
        label_result = parse_label_file(Path(label_file))
        label_result["path"] = str(Path(label_file))
        report["label_file_check"] = label_result
    else:
        report["label_file_check"] = None
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the legacy KNN feature prerequisites without downloading the fastText model.",
    )
    parser.add_argument("--demo", action="store_true", help="Use a tiny built-in fixture.")
    parser.add_argument("--item-a", help="JSON file or inline JSON for the first item.")
    parser.add_argument("--item-b", help="JSON file or inline JSON for the second item.")
    parser.add_argument(
        "--training-set",
        help="JSON array, JSONL file, or inline JSON used to derive IDF weights for non-model features.",
    )
    parser.add_argument("--label-file", help="Optional whitespace-delimited label file to validate.")
    args = parser.parse_args(argv)

    if (args.item_a is None) ^ (args.item_b is None):
        parser.error("--item-a and --item-b must be provided together")

    if args.demo or (args.item_a is None and args.item_b is None):
        item_a, item_b = build_demo_items()
        training_items = build_demo_training_items()
    else:
        item_a = load_item(args.item_a)
        item_b = load_item(args.item_b)
        training_items = load_training_items(args.training_set)

    report = build_report(item_a, item_b, training_items=training_items, label_file=args.label_file)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))

    label_check = report.get("label_file_check")
    if label_check is not None and not label_check.get("ok", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
