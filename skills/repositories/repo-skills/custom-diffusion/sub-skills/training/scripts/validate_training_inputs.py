#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

ALLOWED_FREEZE = {"crossattn_kv", "crossattn"}

def _split_plus(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split("+") if item.strip()]

def _load_concepts(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("concepts_list must be a JSON list")
    return data

def _validate_concept_list(concepts: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    for index, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            errors.append(f"concept[{index}] is not a JSON object")
            continue
        for field in ("instance_prompt", "class_prompt", "instance_data_dir", "class_data_dir"):
            value = concept.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"concept[{index}] missing non-empty {field}")
    return errors

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Custom Diffusion training inputs.")
    parser.add_argument("--base-dir", default=".", help="Base directory for resolving relative paths.")
    parser.add_argument("--concepts-list", default=None, help="Path to a concept-list JSON file.")
    parser.add_argument("--instance-data-dir", default=None, help="Instance image directory for single-concept runs.")
    parser.add_argument("--instance-prompt", default=None, help="Instance prompt for single-concept runs.")
    parser.add_argument("--class-data-dir", default=None, help="Class image directory for generated-prior runs.")
    parser.add_argument("--class-prompt", default=None, help="Class prompt for prior-preservation runs.")
    parser.add_argument("--with-prior-preservation", action="store_true", help="Require prior-preservation inputs.")
    parser.add_argument("--real-prior", action="store_true", help="Interpret prior-preservation inputs as a real-prior bundle.")
    parser.add_argument("--freeze-model", default="crossattn_kv", help="Freeze mode to validate.")
    parser.add_argument("--modifier-token", default=None, help="Plus-separated modifier token list.")
    parser.add_argument("--initializer-token", default="ktn+pll+ucd", help="Plus-separated initializer token list.")
    parser.add_argument("--resolution", type=int, default=512, help="Training resolution to record in the summary.")
    parser.add_argument("--sdxl", action="store_true", help="Record that the SDXL branch is being checked.")
    parser.add_argument("--check-instance-paths", action="store_true", help="Require instance_data_dir paths to exist.")
    parser.add_argument("--check-concept-paths", action="store_true", help="Require concept-list instance paths to exist.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    base_dir = Path(args.base_dir)
    errors: list[str] = []
    concepts: list[dict[str, object]] | None = None

    if args.freeze_model not in ALLOWED_FREEZE:
        errors.append(f"freeze_model must be one of {sorted(ALLOWED_FREEZE)}")

    modifier_tokens = _split_plus(args.modifier_token)
    initializer_tokens = _split_plus(args.initializer_token)
    if modifier_tokens and len(initializer_tokens) < len(modifier_tokens):
        errors.append("initializer_token must contain at least one entry for each modifier_token")
    if args.modifier_token is not None and any(not token for token in modifier_tokens):
        errors.append("modifier_token contains an empty entry")
    if args.initializer_token is not None and any(not token for token in initializer_tokens):
        errors.append("initializer_token contains an empty entry")

    if args.concepts_list is not None:
        concepts = _load_concepts(Path(args.concepts_list))
        if not concepts:
            errors.append("concepts_list must contain at least one concept")
        errors.extend(_validate_concept_list(concepts))
        if args.check_concept_paths:
            for index, concept in enumerate(concepts):
                for field in ("instance_data_dir", "class_data_dir"):
                    data_dir = Path(str(concept.get(field, "")))
                    if not data_dir.is_absolute():
                        data_dir = base_dir / data_dir
                    if not data_dir.exists():
                        errors.append(f"concept[{index}] {field} does not exist: {data_dir}")
    else:
        if not args.instance_data_dir:
            errors.append("instance_data_dir is required when concepts_list is not provided")
        if not args.instance_prompt:
            errors.append("instance_prompt is required when concepts_list is not provided")
        if args.with_prior_preservation:
            if not args.class_data_dir:
                errors.append("class_data_dir is required when prior preservation is enabled without concepts_list")
            if not args.class_prompt:
                errors.append("class_prompt is required when prior preservation is enabled without concepts_list")
        if args.check_instance_paths and args.instance_data_dir:
            instance_dir = Path(args.instance_data_dir)
            if not instance_dir.is_absolute():
                instance_dir = base_dir / instance_dir
            if not instance_dir.exists():
                errors.append(f"instance_data_dir does not exist: {instance_dir}")
        if args.check_instance_paths and args.with_prior_preservation and args.class_data_dir:
            class_dir = Path(args.class_data_dir)
            if not class_dir.is_absolute():
                class_dir = base_dir / class_dir
            if not class_dir.exists():
                errors.append(f"class_data_dir does not exist: {class_dir}")

    summary = {
        "mode": "sdxl" if args.sdxl else "standard",
        "resolution": args.resolution,
        "freeze_model": args.freeze_model,
        "concept_count": len(concepts) if concepts is not None else 1,
        "prior_preservation": args.with_prior_preservation,
        "real_prior": args.real_prior,
        "modifier_tokens": modifier_tokens,
    }

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    print(summary)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
