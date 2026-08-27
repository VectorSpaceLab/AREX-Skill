#!/usr/bin/env python3
"""Static preflight for AIMET GenAILab YAML configs.

This checker intentionally avoids importing GenAILab, transformers, torch, or
qai_hub modules, so it does not download models/datasets or allocate GPUs. It
validates the parts of GenAILab's YAML contract that can be checked from the
file alone and prints the runtime command that a user may run after approving
credentials and compute cost.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Any

TOP_LEVEL_KEYS = {
    "model",
    "metrics",
    "precision",
    "recipe",
    "dataset",
    "export",
    "eval_in_onnx",
    "run_group",
    "profiler",
}
MODEL_REQUIRED = {"model_id", "sequence_length", "context_length"}
TERMINAL_RECIPES = {"Calibration", "RemoveQuantization", "Skip"}
KNOWN_RECIPES = {"Calibration", "SeqMSE", "AdaScale", "SpinQuant", "RemoveQuantization", "Skip"}
KNOWN_DATASETS = {
    "Wikitext",
    "TinyMMLU",
    "MMLU",
    "MMMLU",
    "MMLUPro",
    "MMMU",
    "C4",
    "AOKVQA",
    "Interleaved",
}
KNOWN_METRICS = {
    "PPL",
    "TinyMMLU",
    "MMLU",
    "MMLU1000",
    "MMMLU",
    "MMLUKLDivergence",
    "MMLUReverseKLDivergence",
    "MMLUFlips",
    "MMLUJSDivergence",
    "MMMU",
    "MMMUKLDivergence",
    "MMMUReverseKLDivergence",
    "MMMUFlips",
    "MMMUJSDivergence",
    "Interactive",
    "Prompts",
    "MultimodalPrompts",
    "TrickyPrompts",
    "AutogradedPrompts",
    "AutogradedMultimodalPrompts",
}
KNOWN_ADAPTATIONS = {"SHA", "SHA_Conv", "FastExportable", "AttentionMaskScale", "AIHM"}
QTYPE_ALIASES = {"int4", "int8", "int16", "float16", "float32", 4, 8, 16}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Path to a GenAILab YAML config file")
    parser.add_argument(
        "--framework",
        choices=("torch", "onnx", "both"),
        default="torch",
        help="Framework intended for the follow-up run (default: torch)",
    )
    parser.add_argument(
        "--repo-dir",
        default=".",
        help="AIMET repository root used to form printed commands (default: current directory)",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print a safe GenAILab command template after validation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable validation details as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> list[Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        raise RuntimeError("PyYAML is required for this preflight: python -m pip install pyyaml") from exc

    with path.open("r", encoding="utf-8") as handle:
        try:
            docs = list(yaml.safe_load_all(handle))
        except Exception as exc:
            raise ValueError(f"YAML parse failed: {exc}") from exc
    return docs


def scalar_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and len(value) == 1 and "name" not in value:
        return next(iter(value.keys()))
    if isinstance(value, dict):
        name = value.get("name")
        return str(name) if name is not None else None
    return None


def iter_steps(recipe: Any) -> list[tuple[str, Any]]:
    """Return (component, step) pairs for known recipe syntaxes."""
    if recipe is None:
        return []
    if isinstance(recipe, list):
        return [("backbone", item) for item in recipe]
    if isinstance(recipe, str):
        return [("backbone", recipe)]
    if isinstance(recipe, dict):
        if "name" in recipe:
            return [("backbone", recipe)]
        steps: list[tuple[str, Any]] = []
        for component in ("pre_sim", "backbone", "visual"):
            value = recipe.get(component)
            if value is None:
                continue
            if isinstance(value, list):
                steps.extend((component, item) for item in value)
            else:
                steps.append((component, value))
        return steps
    return []


def dataset_name_from_step(step: Any) -> str | None:
    if not isinstance(step, dict):
        return None
    dataset = step.get("dataset")
    if isinstance(dataset, str):
        return dataset
    if isinstance(dataset, dict):
        name = dataset.get("name")
        return str(name) if name is not None else None
    return None


def validate_precision(value: Any, path: str, errors: list[str], warnings: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, (str, int)):
        if value not in QTYPE_ALIASES:
            warnings.append(f"{path}: unusual qtype {value!r}; GenAILab may reject it")
        return
    if not isinstance(value, dict):
        errors.append(f"{path}: expected scalar or mapping, got {type(value).__name__}")
        return
    for key, item in value.items():
        sub = f"{path}.{key}"
        if key in {"qtype", "granularity", "block_size"}:
            if key == "qtype" and item not in QTYPE_ALIASES:
                warnings.append(f"{sub}: unusual qtype {item!r}")
        else:
            validate_precision(item, sub, errors, warnings)


def validate_document(doc: Any, index: int, repo_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {"document": index, "errors": errors, "warnings": warnings}

    if doc is None:
        errors.append("empty YAML document")
        return summary
    if not isinstance(doc, dict):
        errors.append(f"top-level document must be a mapping, got {type(doc).__name__}")
        return summary

    extra = sorted(set(doc) - TOP_LEVEL_KEYS)
    if extra:
        errors.append(f"unrecognized top-level keys: {', '.join(extra)}")

    model = doc.get("model")
    if not isinstance(model, dict):
        errors.append("missing or invalid required mapping: model")
        model = {}
    else:
        missing_model = sorted(MODEL_REQUIRED - set(model))
        if missing_model:
            errors.append(f"model missing required keys: {', '.join(missing_model)}")

    model_id = model.get("model_id") if isinstance(model, dict) else None
    summary["model_id"] = model_id
    if isinstance(model_id, str):
        if os.path.exists(model_id) or os.path.exists(repo_dir / model_id):
            summary["model_access"] = "local-path"
        else:
            summary["model_access"] = "huggingface-or-remote"
            warnings.append(
                "model.model_id is not a local path; Hugging Face access/cache may be required"
            )
    elif model_id is not None:
        errors.append("model.model_id must be a string")

    seq = model.get("sequence_length") if isinstance(model, dict) else None
    ctx = model.get("context_length") if isinstance(model, dict) else None
    if not isinstance(seq, (int, list)):
        errors.append("model.sequence_length must be an int or list[int]")
    elif isinstance(seq, list) and not all(isinstance(item, int) for item in seq):
        errors.append("model.sequence_length list entries must be ints")
    if not isinstance(ctx, int):
        errors.append("model.context_length must be an int")
    if isinstance(seq, int) and isinstance(ctx, int) and seq > ctx:
        warnings.append("model.sequence_length is greater than context_length")

    adaptations = model.get("adaptations", []) if isinstance(model, dict) else []
    adaptation_names: list[str] = []
    if adaptations is None:
        adaptation_names = []
    elif not isinstance(adaptations, list):
        errors.append("model.adaptations must be a list when present")
    else:
        for item in adaptations:
            name = scalar_name(item)
            if not name:
                errors.append(f"model.adaptations contains invalid entry {item!r}")
                continue
            adaptation_names.append(name)
            if name not in KNOWN_ADAPTATIONS:
                warnings.append(f"unknown adaptation {name!r}; verify it is registered in this checkout")
    summary["adaptations"] = adaptation_names

    metrics = doc.get("metrics")
    metric_names: list[str] = []
    if not isinstance(metrics, list) or not metrics:
        errors.append("metrics must be a non-empty list")
    else:
        for item in metrics:
            name = scalar_name(item)
            if not name:
                errors.append(f"metrics contains invalid entry {item!r}")
                continue
            metric_names.append(name)
            if name not in KNOWN_METRICS:
                warnings.append(f"unknown metric {name!r}; verify it is registered in this checkout")
    summary["metrics"] = metric_names

    validate_precision(doc.get("precision"), "precision", errors, warnings)

    recipe = doc.get("recipe")
    steps = iter_steps(recipe)
    step_names: list[str] = []
    if recipe is None:
        step_names.append("RemoveQuantization(default)")
    elif not steps:
        errors.append("recipe must be a dict, list, string, or component mapping")
    else:
        chain_last: dict[str, str] = {}
        for component, step in steps:
            name = scalar_name(step)
            if not name:
                errors.append(f"recipe.{component} contains invalid step {step!r}")
                continue
            step_names.append(f"{component}:{name}")
            chain_last[component] = name
            if name not in KNOWN_RECIPES:
                warnings.append(f"unknown recipe {name!r}; verify it is registered in this checkout")
            dataset_name = dataset_name_from_step(step)
            if dataset_name and dataset_name not in KNOWN_DATASETS:
                warnings.append(f"unknown dataset {dataset_name!r}; verify it is registered in this checkout")
        for component, last in sorted(chain_last.items()):
            if component != "pre_sim" and last not in TERMINAL_RECIPES:
                warnings.append(
                    f"recipe.{component} does not end in a terminal recipe; GenAILab will auto-append Calibration"
                )
    summary["recipe_steps"] = step_names

    if bool(doc.get("eval_in_onnx")):
        summary["exports"] = True
        warnings.append("eval_in_onnx forces export and may trigger secondary ONNX evaluation")
    else:
        summary["exports"] = bool(doc.get("export"))

    if any(name in {"MMLU", "MMLU1000", "MMMLU", "MMMU", "AOKVQA", "PPL"} for name in metric_names):
        warnings.append("selected metrics can download datasets or require benchmark assets")

    return summary


def print_human(summaries: list[dict[str, Any]], strict: bool) -> None:
    total_errors = sum(len(item["errors"]) for item in summaries)
    total_warnings = sum(len(item["warnings"]) for item in summaries)
    print(f"GenAILab config preflight: {len(summaries)} document(s), {total_errors} error(s), {total_warnings} warning(s)")
    for item in summaries:
        print(f"\nDocument {item['document']}:")
        print(f"  model_id: {item.get('model_id')}")
        print(f"  model_access: {item.get('model_access', 'unknown')}")
        print(f"  metrics: {', '.join(item.get('metrics', [])) or '(none)'}")
        print(f"  recipe: {', '.join(item.get('recipe_steps', [])) or '(none)'}")
        print(f"  exports: {item.get('exports', False)}")
        for err in item["errors"]:
            print(f"  ERROR: {err}")
        for warn in item["warnings"]:
            print(f"  WARNING: {warn}")
    if strict and total_warnings:
        print("\nStrict mode: warnings are treated as failures.")


def main() -> int:
    args = parse_args()
    config = Path(args.config).expanduser().resolve()
    repo_dir = Path(args.repo_dir).expanduser().resolve()

    if not config.is_file() or config.stat().st_size == 0:
        print(f"ERROR: config file does not exist or is empty: {config}", file=sys.stderr)
        return 1

    try:
        docs = load_yaml(config)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    summaries = [validate_document(doc, i + 1, repo_dir) for i, doc in enumerate(docs)]
    total_errors = sum(len(item["errors"]) for item in summaries)
    total_warnings = sum(len(item["warnings"]) for item in summaries)

    if args.json:
        print(json.dumps({"config": str(config), "framework": args.framework, "documents": summaries}, indent=2))
    else:
        print_human(summaries, args.strict)

    if args.print_command:
        cmd = [
            "python",
            "-m",
            "GenAILab",
            "--framework",
            args.framework,
            "--config",
            str(config),
            "--export-dir",
            "GenAILab/artifacts/exports",
            "--results-dir",
            "GenAILab/artifacts/results",
        ]
        print("\nLocal command template:")
        print("  " + " ".join(shlex.quote(part) for part in cmd))
        print("Credential checks before long runs: HF token for gated/remote models, dataset access, CUDA capacity, and optional gh/AWS/AI Hub auth.")

    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
