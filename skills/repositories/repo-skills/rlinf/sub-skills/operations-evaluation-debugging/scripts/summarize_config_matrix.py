#!/usr/bin/env python3
"""Read-only YAML matrix summarizer for RLinf config families.

The script counts task types, environment/model types, algorithms, rollout
backends, training backends, and likely benchmark families from one or more YAML
files/directories. It uses PyYAML when available and falls back to conservative
regular-expression extraction when PyYAML is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

try:  # graceful optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - depends on caller environment
    yaml = None  # type: ignore

YAML_SUFFIXES = {".yaml", ".yml"}
KNOWN_FAMILIES = [
    "libero",
    "robotwin",
    "behavior",
    "maniskill",
    "realworld",
    "polaris",
    "metaworld",
    "calvin",
    "robocasa365",
    "robocasa",
    "roboverse",
    "isaaclab",
    "frankasim",
    "genesis",
    "d4rl",
    "sft",
    "offline",
    "reasoning",
    "agent",
    "agentlightning",
    "searchr1",
    "wideseek",
    "auto_placement",
    "dynamic_scheduler",
]
KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z0-9_./-]+)\s*:\s*['\"]?([^#'\"\n][^#\n]*)")


def iter_yaml_files(root: Path, max_files: int) -> Iterable[Path]:
    root = root.expanduser()
    if root.is_file():
        if root.suffix.lower() in YAML_SUFFIXES:
            yield root
        return
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", "__pycache__"}]
        for filename in filenames:
            if Path(filename).suffix.lower() not in YAML_SUFFIXES:
                continue
            count += 1
            if count > max_files:
                return
            yield Path(dirpath) / filename


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(value, path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            path = f"{prefix}[{idx}]"
            out.update(flatten(value, path))
    else:
        out[prefix] = obj
    return out


def read_yaml_flat(path: Path) -> tuple[dict[str, Any], str | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            if data is None:
                data = {}
            return flatten(data), None
        except Exception as exc:
            # Fall through to regex extraction but keep the parse warning.
            fallback = regex_extract(text)
            return fallback, f"PyYAML parse failed: {exc}"
    return regex_extract(text), "PyYAML not installed; used conservative regex extraction"


def regex_extract(text: str) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for idx, line in enumerate(text.splitlines(), start=1):
        match = KEY_VALUE_RE.match(line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip().strip("'\"")
        if value in {"null", "None", "~", ""}:
            continue
        flat[f"line{idx}.{key}"] = value
    return flat


def normalize_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, str):
        cleaned = value.strip().strip("'\"")
        if not cleaned or cleaned.startswith("${"):
            return None
        return cleaned
    return None


def count_if(counter: Counter[str], value: Any) -> None:
    normalized = normalize_value(value)
    if normalized:
        counter[normalized] += 1


def detect_family(path: Path) -> str:
    lower_parts = [part.lower() for part in path.parts]
    stem = path.stem.lower()
    for family in KNOWN_FAMILIES:
        if family in lower_parts or stem.startswith(family + "_") or stem == family:
            return family
    first = re.split(r"[_-]", stem)[0]
    return first or "unknown"


def detect_training_backend(flat: dict[str, Any]) -> set[str]:
    joined = "\n".join(f"{k}: {v}" for k, v in flat.items()).lower()
    found: set[str] = set()
    if "megatron" in joined or "mbridge" in joined or "megatron_bridge" in joined:
        found.add("megatron")
    if "fsdp" in joined or "fully_sharded" in joined:
        found.add("fsdp")
    return found


def detect_rollout_backend(flat: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    for key, value in flat.items():
        key_lower = key.lower()
        normalized = normalize_value(value)
        if not normalized:
            continue
        value_lower = normalized.lower()
        if key_lower.endswith("rollout_backend") or key_lower.endswith("generation_backend"):
            found.add(value_lower)
        elif "sglang" in value_lower:
            found.add("sglang")
        elif "vllm" in value_lower:
            found.add("vllm")
    return found


def detect_default_presets(flat: dict[str, Any]) -> dict[str, set[str]]:
    """Extract Hydra defaults such as env/libero_spatial@env.eval."""
    presets: dict[str, set[str]] = {"env": set(), "model": set(), "algorithm": set()}
    for key, value in flat.items():
        if "defaults" not in key.lower():
            continue
        normalized = normalize_value(value)
        if not normalized or normalized.startswith("override "):
            continue
        match = re.match(r"^(env|model|algorithm)/([^@\s]+)", normalized)
        if match:
            kind, preset = match.groups()
            presets[kind].add(preset)
    return presets


def summarize(paths: list[str], max_files: int) -> dict[str, Any]:
    counters: dict[str, Counter[str]] = {
        "families": Counter(),
        "task_types": Counter(),
        "env_types": Counter(),
        "env_presets": Counter(),
        "model_types": Counter(),
        "model_presets": Counter(),
        "algorithm_presets": Counter(),
        "adv_types": Counter(),
        "loss_types": Counter(),
        "rollout_backends": Counter(),
        "training_backends": Counter(),
    }
    files: list[dict[str, Any]] = []
    warnings: list[str] = []
    per_family_files: dict[str, list[str]] = defaultdict(list)

    for input_path in paths:
        root = Path(input_path).expanduser()
        if not root.exists():
            warnings.append(f"missing path: {input_path}")
            continue
        for yaml_path in iter_yaml_files(root, max_files=max_files):
            try:
                flat, warning = read_yaml_flat(yaml_path)
            except OSError as exc:
                warnings.append(f"could not read {yaml_path}: {exc}")
                continue
            if warning:
                warnings.append(f"{yaml_path}: {warning}")

            family = detect_family(yaml_path)
            counters["families"][family] += 1
            per_family_files[family].append(str(yaml_path))

            default_presets = detect_default_presets(flat)
            for preset in default_presets["env"]:
                counters["env_presets"][preset] += 1
            for preset in default_presets["model"]:
                counters["model_presets"][preset] += 1
            for preset in default_presets["algorithm"]:
                counters["algorithm_presets"][preset] += 1

            file_record: dict[str, Any] = {
                "path": str(yaml_path),
                "family": family,
                "task_type": None,
                "env_types": [],
                "env_presets": sorted(default_presets["env"]),
                "model_types": [],
                "model_presets": sorted(default_presets["model"]),
                "algorithm_presets": sorted(default_presets["algorithm"]),
                "adv_type": None,
                "loss_type": None,
                "rollout_backends": sorted(detect_rollout_backend(flat)),
                "training_backends": sorted(detect_training_backend(flat)),
            }

            for key, value in flat.items():
                key_lower = key.lower()
                if key_lower.endswith("task_type"):
                    count_if(counters["task_types"], value)
                    file_record["task_type"] = file_record["task_type"] or normalize_value(value)
                elif key_lower.endswith("env_type"):
                    normalized = normalize_value(value)
                    if normalized:
                        counters["env_types"][normalized] += 1
                        file_record["env_types"].append(normalized)
                elif key_lower.endswith("model_type"):
                    normalized = normalize_value(value)
                    if normalized:
                        counters["model_types"][normalized] += 1
                        file_record["model_types"].append(normalized)
                elif key_lower.endswith("adv_type"):
                    count_if(counters["adv_types"], value)
                    file_record["adv_type"] = file_record["adv_type"] or normalize_value(value)
                elif key_lower.endswith("loss_type"):
                    count_if(counters["loss_types"], value)
                    file_record["loss_type"] = file_record["loss_type"] or normalize_value(value)

            for backend in file_record["rollout_backends"]:
                counters["rollout_backends"][backend] += 1
            for backend in file_record["training_backends"]:
                counters["training_backends"][backend] += 1

            file_record["env_types"] = sorted(set(file_record["env_types"]))
            file_record["model_types"] = sorted(set(file_record["model_types"]))
            files.append(file_record)

    return {
        "pyyaml_available": yaml is not None,
        "files_scanned": len(files),
        "counters": {name: dict(counter.most_common()) for name, counter in counters.items()},
        "files": files,
        "families": {family: sorted(paths) for family, paths in sorted(per_family_files.items())},
        "warnings": warnings,
    }


def print_counter(title: str, data: dict[str, int], limit: int) -> None:
    print(f"\n{title}:")
    if not data:
        print("  - <none>")
        return
    for idx, (key, value) in enumerate(data.items()):
        if idx >= limit:
            print(f"  - ... {len(data) - limit} more")
            break
        print(f"  - {key}: {value}")


def print_text(summary: dict[str, Any], limit: int, show_files: bool) -> None:
    print("RLinf config matrix summary")
    print(f"PyYAML available: {summary['pyyaml_available']}")
    print(f"Files scanned: {summary['files_scanned']}")
    for name, title in [
        ("families", "Families"),
        ("task_types", "Task types"),
        ("env_types", "Environment types"),
        ("env_presets", "Environment presets from defaults"),
        ("model_types", "Model types"),
        ("model_presets", "Model presets from defaults"),
        ("algorithm_presets", "Algorithm presets from defaults"),
        ("adv_types", "Advantage types"),
        ("loss_types", "Loss types"),
        ("training_backends", "Training backends"),
        ("rollout_backends", "Rollout backends"),
    ]:
        print_counter(title, summary["counters"].get(name, {}), limit)

    warnings = summary.get("warnings") or []
    if warnings:
        print("\nWarnings:")
        for warning in warnings[:limit]:
            print(f"  - {warning}")
        if len(warnings) > limit:
            print(f"  - ... {len(warnings) - limit} more")

    if show_files:
        print("\nFiles:")
        for record in summary["files"][:limit]:
            print(
                "  - {path} | family={family} task={task} env={env} env_preset={env_preset} model={model} model_preset={model_preset} algorithm_preset={algorithm_preset} train={train} rollout={rollout}".format(
                    path=record["path"],
                    family=record["family"],
                    task=record.get("task_type") or "?",
                    env=",".join(record.get("env_types") or []) or "?",
                    env_preset=",".join(record.get("env_presets") or []) or "?",
                    model=",".join(record.get("model_types") or []) or "?",
                    model_preset=",".join(record.get("model_presets") or []) or "?",
                    algorithm_preset=",".join(record.get("algorithm_presets") or []) or "?",
                    train=",".join(record.get("training_backends") or []) or "?",
                    rollout=",".join(record.get("rollout_backends") or []) or "?",
                )
            )
        if len(summary["files"]) > limit:
            print(f"  - ... {len(summary['files']) - limit} more")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize RLinf YAML config families and backend/env/model matrices."
    )
    parser.add_argument("paths", nargs="+", help="YAML files or directories to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument("--show-files", action="store_true", help="Print per-file extracted fields in text mode.")
    parser.add_argument("--limit", type=int, default=40, help="Maximum entries per text section (default: 40).")
    parser.add_argument("--max-files", type=int, default=3000, help="Maximum YAML files per input directory (default: 3000).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = summarize(args.paths, max_files=args.max_files)
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        print()
    else:
        print_text(summary, limit=args.limit, show_files=args.show_files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
