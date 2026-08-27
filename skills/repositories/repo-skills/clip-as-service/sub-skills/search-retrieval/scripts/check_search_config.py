#!/usr/bin/env python3
"""Statically validate a CLIP-as-service search Flow YAML.

The checker confirms the Flow contains a CLIP encoder and an AnnLite indexer,
warns about obvious `n_dim` mismatches, and inspects sharded polling rules
without starting a server or downloading models.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MODEL_DIMS = {
    "ViT-B-32::openai": 512,
    "ViT-B-32::laion2b_e16": 512,
    "ViT-B-32::laion400m_e31": 512,
    "ViT-B-32::laion400m_e32": 512,
    "ViT-B-32::laion2b-s34b-b79k": 512,
    "ViT-B-16::openai": 512,
    "ViT-B-16::laion400m_e31": 512,
    "ViT-B-16::laion400m_e32": 512,
    "ViT-B-16-plus-240::laion400m_e31": 640,
    "ViT-B-16-plus-240::laion400m_e32": 640,
    "RN50::openai": 1024,
    "RN50::yfcc15m": 1024,
    "RN50::cc12m": 1024,
    "RN101::openai": 512,
    "RN101::yfcc15m": 512,
    "ViT-L-14::openai": 768,
    "ViT-L-14::laion400m_e31": 768,
    "ViT-L-14::laion400m_e32": 768,
    "ViT-L-14::laion2b-s32b-b82k": 768,
    "ViT-L-14-336::openai": 768,
    "ViT-H-14::laion2b-s32b-b79k": 1024,
    "ViT-g-14::laion2b-s12b-b42k": 1024,
    "M-CLIP/LABSE-Vit-L-14": 768,
    "M-CLIP/XLM-Roberta-Large-Vit-B-32": 512,
    "M-CLIP/XLM-Roberta-Large-Vit-B-16Plus": 640,
    "M-CLIP/XLM-Roberta-Large-Vit-L-14": 768,
}

ENCODER_MODULES = {
    "clip_server.executors.clip_torch",
    "clip_server.executors.clip_onnx",
    "clip_server.executors.clip_tensorrt",
}


def load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("PyYAML is required: pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def inspect_flow(data: dict, model_name: str | None = None) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    executors = data.get("executors")
    if not isinstance(executors, list) or not executors:
        errors.append("executors must be a non-empty list")
        executors = []

    runtime_modules: list[str] = []
    indexer_found = False
    workspace = None
    n_dim = None
    limit = None
    polling = None

    for i, executor in enumerate(executors):
        if not isinstance(executor, dict):
            errors.append(f"executor[{i}] must be a mapping")
            continue
        uses = executor.get("uses") or {}
        metas = uses.get("metas") if isinstance(uses, dict) else {}
        py_modules = metas.get("py_modules") if isinstance(metas, dict) else None
        if isinstance(py_modules, list):
            runtime_modules.extend(str(item) for item in py_modules)
        if uses.get("jtype") == "AnnLiteIndexer":
            indexer_found = True
            uses_with = uses.get("with") or {}
            if isinstance(uses_with, dict):
                n_dim = uses_with.get("n_dim", n_dim)
                limit = uses_with.get("limit", limit)
            workspace = executor.get("workspace", workspace)
            polling = executor.get("polling", polling)

    if not any(module in ENCODER_MODULES for module in runtime_modules):
        errors.append("no recognized CLIP encoder module found in py_modules")
    if not indexer_found:
        errors.append("no AnnLiteIndexer executor found")

    flow_with = data.get("with") or {}
    if isinstance(flow_with, dict):
        details["port"] = flow_with.get("port")
        details["protocol"] = flow_with.get("protocol", "grpc")
    details["workspace"] = workspace
    details["n_dim"] = n_dim
    details["limit"] = limit
    details["polling"] = polling
    details["runtime_modules"] = runtime_modules

    if model_name and n_dim is not None:
        expected = MODEL_DIMS.get(model_name)
        if expected is None:
            warnings.append(f"unknown model_name {model_name!r}; cannot confirm n_dim")
        elif expected != n_dim:
            errors.append(f"n_dim {n_dim} does not match model {model_name!r} output dimension {expected}")

    if not workspace:
        warnings.append("workspace is missing; persistent indexes need a storage path")

    if polling:
        if not isinstance(polling, dict):
            warnings.append("polling should be a mapping of endpoint to strategy")
        else:
            if polling.get("/index") not in {"ANY", None}:
                warnings.append("/index polling should usually be ANY for sharded indexing")
            if polling.get("/search") not in {"ALL", None}:
                warnings.append("/search polling should usually be ALL for sharded retrieval")

    if model_name and model_name in MODEL_DIMS:
        details["expected_n_dim"] = MODEL_DIMS[model_name]

    return errors, warnings, details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Statically validate a CLIP-as-service search Flow YAML.")
    parser.add_argument("yaml_path", type=Path)
    parser.add_argument("--model-name", help="Optional model name used to sanity-check n_dim.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_yaml(args.yaml_path)
        errors, warnings, details = inspect_flow(data, args.model_name)
    except Exception as exc:  # noqa: BLE001
        errors, warnings, details = [f"{type(exc).__name__}: {exc}"], [], {}

    report = {"path": str(args.yaml_path), "ok": not errors, "errors": errors, "warnings": warnings, "details": details}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
