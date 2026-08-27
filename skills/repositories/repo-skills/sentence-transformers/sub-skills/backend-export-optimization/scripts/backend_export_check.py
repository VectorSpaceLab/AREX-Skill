#!/usr/bin/env python3
"""Inspect Sentence Transformers backend/export support without exporting by default."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from typing import Any


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def collect_availability() -> dict[str, Any]:
    availability: dict[str, Any] = {
        "sentence_transformers": module_available("sentence_transformers"),
        "torch": module_available("torch"),
        "onnxruntime": module_available("onnxruntime"),
        "optimum": module_available("optimum"),
        "optimum.onnxruntime": module_available("optimum.onnxruntime"),
        "optimum.intel": module_available("optimum.intel"),
        "openvino": module_available("openvino"),
        "datasets": module_available("datasets"),
    }
    if availability["onnxruntime"]:
        import onnxruntime as ort

        availability["onnxruntime_providers"] = ort.get_available_providers()
    return availability


def collect_signatures() -> dict[str, str]:
    from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder
    from sentence_transformers.backend import (
        export_dynamic_quantized_onnx_model,
        export_optimized_onnx_model,
        export_static_quantized_openvino_model,
    )

    objects = {
        "SentenceTransformer.__init__": SentenceTransformer.__init__,
        "CrossEncoder.__init__": CrossEncoder.__init__,
        "SparseEncoder.__init__": SparseEncoder.__init__,
        "export_optimized_onnx_model": export_optimized_onnx_model,
        "export_dynamic_quantized_onnx_model": export_dynamic_quantized_onnx_model,
        "export_static_quantized_openvino_model": export_static_quantized_openvino_model,
    }
    return {name: str(inspect.signature(obj)) for name, obj in objects.items()}


def validate_backend_requirements(backend: str) -> list[str]:
    availability = collect_availability()
    problems: list[str] = []
    if not availability["sentence_transformers"]:
        problems.append("sentence_transformers is not importable")
    if backend == "onnx":
        if not availability["optimum.onnxruntime"]:
            problems.append("optimum.onnxruntime is not importable; install sentence-transformers[onnx] or [onnx-gpu]")
        if not availability["onnxruntime"]:
            problems.append("onnxruntime is not importable; install sentence-transformers[onnx] or [onnx-gpu]")
    elif backend == "openvino":
        if not availability["optimum.intel"]:
            problems.append("optimum.intel is not importable; install sentence-transformers[openvino]")
        if not availability["openvino"]:
            problems.append("openvino is not importable; install sentence-transformers[openvino]")
    return problems


def maybe_load_model(args: argparse.Namespace) -> dict[str, Any]:
    if not args.model:
        return {"model_load": "skipped; pass --model and --backend to load a model"}
    if not args.backend:
        raise SystemExit("--backend is required when --model is provided")

    problems = validate_backend_requirements(args.backend)
    if problems:
        return {"model_load": "skipped", "problems": problems}

    from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder

    model_classes = {
        "sentence-transformer": SentenceTransformer,
        "cross-encoder": CrossEncoder,
        "sparse-encoder": SparseEncoder,
    }
    model_kwargs: dict[str, Any] = {}
    if args.file_name:
        model_kwargs["file_name"] = args.file_name
    if args.no_export:
        model_kwargs["export"] = False
    if args.provider:
        model_kwargs["provider"] = args.provider

    cls = model_classes[args.model_type]
    model = cls(args.model, backend=args.backend, model_kwargs=model_kwargs or None)
    return {
        "model_load": "ok",
        "model_type": args.model_type,
        "backend": args.backend,
        "class": type(model).__name__,
        "transformers_model_class": type(getattr(model, "transformers_model", None)).__name__,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Sentence Transformers backend export APIs and optional dependencies. "
            "By default this performs import/signature checks only and does not export models."
        )
    )
    parser.add_argument("--check", choices=["all", "onnx", "openvino"], default="all", help="Dependency group to validate.")
    parser.add_argument("--signatures", action="store_true", help="Print public backend/export API signatures.")
    parser.add_argument("--model", help="Optional model name or local directory to load. May download/export depending on backend.")
    parser.add_argument("--backend", choices=["torch", "onnx", "openvino"], help="Backend to use when --model is provided.")
    parser.add_argument(
        "--model-type",
        choices=["sentence-transformer", "cross-encoder", "sparse-encoder"],
        default="sentence-transformer",
        help="Model wrapper class to instantiate when --model is provided.",
    )
    parser.add_argument("--file-name", help="Backend artifact file name, for example onnx/model_O3.onnx.")
    parser.add_argument("--provider", help="ONNX Runtime provider, for example CPUExecutionProvider.")
    parser.add_argument("--no-export", action="store_true", help="Set model_kwargs={'export': False} when loading a backend model.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result: dict[str, Any] = {"availability": collect_availability()}

    checks = ["onnx", "openvino"] if args.check == "all" else [args.check]
    result["requirement_problems"] = {backend: validate_backend_requirements(backend) for backend in checks}

    if args.signatures:
        if not result["availability"]["sentence_transformers"]:
            result["signatures"] = "skipped; sentence_transformers is not importable"
        else:
            result["signatures"] = collect_signatures()

    result.update(maybe_load_model(args))

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Backend export environment check")
        print("Availability:")
        for key, value in result["availability"].items():
            print(f"  {key}: {value}")
        print("Requirement problems:")
        for backend, problems in result["requirement_problems"].items():
            print(f"  {backend}: {problems or 'none'}")
        if "signatures" in result:
            print("Signatures:")
            if isinstance(result["signatures"], dict):
                for key, value in result["signatures"].items():
                    print(f"  {key}{value}")
            else:
                print(f"  {result['signatures']}")
        print(f"Model load: {result.get('model_load')}")
        if result.get("problems"):
            print("Model load problems:")
            for problem in result["problems"]:
                print(f"  - {problem}")
    has_problems = any(result["requirement_problems"].values()) if args.check != "all" else False
    return 1 if has_problems else 0


if __name__ == "__main__":
    sys.exit(main())
