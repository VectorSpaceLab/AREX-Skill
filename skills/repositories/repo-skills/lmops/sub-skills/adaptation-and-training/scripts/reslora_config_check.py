#!/usr/bin/env python3
"""Validate a proposed ResLoRA configuration.

The script checks the flag combinations and expands target-module aliases into
concrete module names for the selected model family. It does not import the
repository's ResLoRA package.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Tuple

BUILTIN_TARGETS: Dict[str, Dict[str, List[str]]] = {
    "llama": {
        "q": ["q_proj"],
        "k": ["k_proj"],
        "v": ["v_proj"],
        "o": ["o_proj"],
        "f": ["up_proj", "down_proj"],
        "g": ["gate_proj"],
    },
    "mistral": {
        "q": ["q_proj"],
        "k": ["k_proj"],
        "v": ["v_proj"],
        "o": ["o_proj"],
        "f": ["up_proj", "down_proj"],
        "g": ["gate_proj"],
    },
    "roberta": {
        "q": ["query"],
        "k": ["key"],
        "v": ["value"],
        "o": ["out"],
    },
    "unet": {
        "q": ["to_q"],
        "k": ["to_k"],
        "v": ["to_v"],
        "o": ["to_out"],
    },
}

PLACEHOLDER_MARKERS = ("<", ">", "todo", "replace", "path/to", "???", "unset")


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]
    warnings: List[str]
    family: str
    aliases: List[str]
    expanded_modules: List[str]
    suggested_config: Dict[str, Any]


def _split_aliases(raw: str) -> List[str]:
    tokens = []
    for chunk in raw.replace(",", ".").replace("+", ".").replace(" ", ".").split("."):
        item = chunk.strip().lower()
        if item:
            tokens.append(item)
    deduped: List[str] = []
    for token in tokens:
        if token not in deduped:
            deduped.append(token)
    return deduped


def _load_mapping(model_name: str, module_map_json: str | None) -> Dict[str, List[str]]:
    if module_map_json:
        loaded = json.loads(module_map_json)
        if not isinstance(loaded, dict):
            raise ValueError("module map JSON must be an object")
        mapping: Dict[str, List[str]] = {}
        for key, value in loaded.items():
            if not isinstance(key, str) or not isinstance(value, list):
                raise ValueError("module map entries must map strings to lists")
            mapping[key.lower()] = [str(item) for item in value]
        return mapping
    if model_name.lower() not in BUILTIN_TARGETS:
        raise ValueError(
            f"unknown model family: {model_name}. Supply --module-map-json for a custom family."
        )
    return BUILTIN_TARGETS[model_name.lower()]


def _expand_targets(mapping: Dict[str, List[str]], aliases: Iterable[str]) -> Tuple[List[str], List[str]]:
    expanded: List[str] = []
    unknown: List[str] = []
    for alias in aliases:
        if alias not in mapping:
            unknown.append(alias)
            continue
        for module_name in mapping[alias]:
            if module_name not in expanded:
                expanded.append(module_name)
    return expanded, unknown


def _build_result(args: argparse.Namespace) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    family = args.model_name.lower()
    mapping = _load_mapping(family, args.module_map_json)
    aliases = _split_aliases(args.target_modules)
    if not aliases:
        errors.append("no target aliases were supplied")

    expanded_modules, unknown = _expand_targets(mapping, aliases)
    if unknown:
        message = f"unknown target alias(es) for family {family}: {', '.join(unknown)}"
        if args.allow_unknown_targets:
            warnings.append(message)
        else:
            errors.append(message)

    if not expanded_modules:
        errors.append("no concrete target modules remain after expansion")

    if args.rank <= 0:
        errors.append("rank must be positive")
    if args.lora_alpha <= 0:
        errors.append("lora_alpha must be positive")
    if args.lora_num <= 0:
        errors.append("lora_num must be positive")
    if not 0.0 <= args.lora_dropout <= 1.0:
        errors.append("lora_dropout must be between 0 and 1")

    if args.res_flag not in (0, 1, 2, 3):
        errors.append("res_flag must be one of 0, 1, 2, 3")
    if args.merge_flag not in (0, 3, 4):
        errors.append("merge_flag must be one of 0, 3, 4")

    if args.merge_flag != 0 and args.res_flag == 0:
        errors.append("merge_flag requires a residual mode")
    if args.merge_flag != 0 and args.res_flag not in (1, 3):
        errors.append("merge-aware behavior only matches res_flag 1 or 3")
    if args.res_flag in (2, 3) and args.pre_num <= 0:
        errors.append("pre_num must be positive when res_flag is 2 or 3")
    if args.res_flag not in (2, 3) and args.pre_num > 0:
        warnings.append("pre_num will be ignored unless res_flag is 2 or 3")
    if args.res_flag == 0 and args.pre_num > 0:
        warnings.append("pre_num has no effect in res_flag 0")
    if args.merge_flag == 4 and args.merge_4_len <= 0:
        errors.append("merge_4_len must be positive when merge_flag is 4")

    if args.method.lower() != "reslora":
        warnings.append("this checker only validates the reslora method surface")

    suggested_config = {
        "rank": args.rank,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "target_modules": args.target_modules,
        "res_flag": args.res_flag,
        "merge_flag": args.merge_flag,
        "pre_num": args.pre_num,
        "merge_4_len": args.merge_4_len,
        "family": family,
        "expanded_modules": expanded_modules,
    }

    return ValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        family=family,
        aliases=aliases,
        expanded_modules=expanded_modules,
        suggested_config=suggested_config,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-name", type=str, default="llama", help="Model family or custom family name.")
    parser.add_argument("--module-map-json", type=str, default=None, help="Optional JSON object mapping aliases to concrete module-name lists.")
    parser.add_argument("--target-modules", type=str, required=True, help="Alias string such as q.v or q,k,v.")
    parser.add_argument("--res-flag", type=int, default=0)
    parser.add_argument("--merge-flag", type=int, default=0)
    parser.add_argument("--pre-num", type=int, default=0)
    parser.add_argument("--merge-4-len", type=int, default=100)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-num", type=int, default=1)
    parser.add_argument("--method", type=str, default="reslora")
    parser.add_argument("--allow-unknown-targets", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as errors.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = _build_result(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print("# ResLoRA config check")
        print(f"- family: {result.family}")
        print(f"- aliases: {', '.join(result.aliases) if result.aliases else 'none'}")
        print(f"- expanded modules: {', '.join(result.expanded_modules) if result.expanded_modules else 'none'}")
        print(f"- ok: {result.ok}")
        if result.warnings:
            print("- warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        if result.errors:
            print("- errors:")
            for error in result.errors:
                print(f"  - {error}")
        print("- suggested config:")
        print(json.dumps(result.suggested_config, indent=2))

    if result.errors:
        return 2
    if args.strict_warnings and result.warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
