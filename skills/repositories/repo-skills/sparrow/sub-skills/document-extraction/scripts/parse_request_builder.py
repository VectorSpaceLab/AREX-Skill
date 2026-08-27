#!/usr/bin/env python3
"""Build a Sparrow Parse extraction request plan without running a VLM backend.

The script validates schema/hints JSON, prepares the prompt shape used by Sparrow
Parse, and emits backend config plus VLLMExtractor.run_inference kwargs. It is
safe by default: no model is loaded and no document is read except an optional
hints JSON file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_QUERY = '{"invoice_number":"str","total":0.0}'
DEFAULT_MODEL_BY_BACKEND = {
    "mlx": "mlx-community/Qwen3.6-35B-A3B-8bit",
    "ollama": "mistral-small3.2:24b-instruct-2506-q8_0",
    "vllm": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    "mistral": "mistral-ocr-latest",
    "huggingface": "owner/space-name",
    "local_gpu": "custom-model-placeholder",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a Sparrow Parse request plan without invoking a model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="JSON example schema, '*' for generic/page-type extraction, or text when --instruction/--validation is set.",
    )
    parser.add_argument(
        "--file-path",
        default=None,
        help="Document path to place in input_data. The file is not opened by this builder.",
    )
    parser.add_argument(
        "--backend",
        choices=["mlx", "ollama", "vllm", "mistral", "huggingface", "local_gpu"],
        default="mlx",
        help="InferenceFactory backend method.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name for mlx/ollama/vllm/mistral, HF space for huggingface, or placeholder for local_gpu.",
    )
    parser.add_argument(
        "--hf-token-env",
        default="HF_TOKEN",
        help="Environment variable name used by Hugging Face backend; secret value is never printed.",
    )
    parser.add_argument(
        "--mistral-token-env",
        default="MISTRAL_API_KEY",
        help="Environment variable name expected by Mistral backend; secret value is never printed.",
    )
    parser.add_argument(
        "--hints-file-path",
        default=None,
        help="Optional JSON hints file. This builder validates and embeds its JSON content in the prompt preview.",
    )
    parser.add_argument(
        "--page-type",
        action="append",
        default=None,
        help="Candidate page type. Repeat for multiple labels. Use with --query '*'.",
    )
    parser.add_argument("--tables-only", action="store_true", help="Set tables_only for table crop extraction.")
    parser.add_argument("--validation-off", action="store_true", help="Skip pipeline schema validation.")
    parser.add_argument("--apply-annotation", action="store_true", help="Request bbox/value/confidence annotation where supported.")
    parser.add_argument("--crop-size", type=int, default=None, help="Pixels to crop from each image border.")
    parser.add_argument("--markdown", action="store_true", help="Plan the markdown-first extraction flow.")
    parser.add_argument("--instruction", action="store_true", help="Treat query as a short document instruction, not JSON schema.")
    parser.add_argument("--validation", action="store_true", help="Treat query as a comma-separated field-presence validation list.")
    parser.add_argument("--debug", action="store_true", help="Set debug=True in the run plan.")
    parser.add_argument("--debug-dir", default=None, help="Directory Sparrow Parse should use for retained debug page/crop images.")
    parser.add_argument("--output", default="-", help="Output JSON file path, or '-' for stdout.")
    return parser.parse_args()


def json_loads_or_die(value: str, label: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(json.dumps({"ok": False, "error": f"Invalid {label}: {exc.msg}", "position": exc.pos}, indent=2))


def read_hints(path_value: str | None, warnings: list[str]) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if path.suffix.lower() != ".json":
        warnings.append("Hints path does not end in .json; Sparrow pipeline would ignore it.")
        return ""
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        warnings.append("Hints file is missing; Sparrow pipeline would silently ignore it.")
        return ""
    except json.JSONDecodeError as exc:
        warnings.append(f"Hints file is invalid JSON at position {exc.pos}; Sparrow pipeline would silently ignore it.")
        return ""
    except OSError as exc:
        warnings.append(f"Could not read hints file ({exc}); Sparrow pipeline would silently ignore it.")
        return ""
    return json.dumps(content, ensure_ascii=False)


def prepare_query(args: argparse.Namespace, hints_content: str, warnings: list[str]) -> dict[str, Any]:
    query = args.query
    query_all_data = query == "*"

    if args.instruction and args.validation:
        raise SystemExit(json.dumps({"ok": False, "error": "Use only one of --instruction or --validation."}, indent=2))
    if args.markdown and (args.instruction or args.validation):
        warnings.append("--markdown uses a markdown-first extraction flow; --instruction/--validation are not part of the normal markdown extraction path.")

    if query_all_data:
        if args.page_type:
            page_types = ", ".join(str(item) for item in args.page_type)
            return {
                "mode": "page_type",
                "text_input": f"detect page type based on this list of types - {page_types}. return response in JSON format",
                "query_schema": None,
                "generic_query": False,
                "schema_validated_by_builder": False,
            }
        return {
            "mode": "wildcard_all_data",
            "text_input": "retrieve document data. return response in JSON format",
            "query_schema": None,
            "generic_query": True,
            "schema_validated_by_builder": False,
        }

    if args.page_type:
        warnings.append("--page-type only changes the prepared prompt when --query '*' is used; with a schema query it mainly forces validation off in the pipeline.")

    if args.instruction:
        return {
            "mode": "instruction",
            "text_input": f"{query}. response must be short, with values to answer the question, no need to provide other values. return response in JSON format",
            "query_schema": None,
            "generic_query": False,
            "schema_validated_by_builder": False,
        }

    if args.validation:
        return {
            "mode": "field_validation",
            "text_input": f"validate if listed fields - {query} are present in the document. format response with field name and boolean value. return response in JSON format",
            "query_schema": None,
            "generic_query": False,
            "schema_validated_by_builder": False,
        }

    # Markdown flow still needs the schema for its second-stage extraction.
    schema_obj = json_loads_or_die(query, "schema query")
    hints_section = f"\n\nAdditional Hints:\n{hints_content}" if hints_content else ""

    if args.markdown:
        return {
            "mode": "markdown_first",
            "text_input": "\n<|grounding|>Convert the document to markdown.",
            "query_schema": schema_obj,
            "generic_query": False,
            "schema_validated_by_builder": True,
            "markdown_second_stage_schema_query": query,
            "markdown_second_stage_hints_included": bool(hints_content),
        }

    prompt = (
        "retrieve data based on provided JSON schema. return response in JSON format, "
        "by strictly following this JSON schema: "
        + query
        + ". If a field is not visible or cannot be found in the document, return null. "
        "Do not guess, infer, or generate values for missing fields."
        + hints_section
    )
    return {
        "mode": "schema_extraction",
        "text_input": prompt,
        "query_schema": schema_obj,
        "generic_query": False,
        "schema_validated_by_builder": True,
    }


def backend_config(args: argparse.Namespace, warnings: list[str]) -> dict[str, Any]:
    model = args.model or DEFAULT_MODEL_BY_BACKEND[args.backend]
    if args.backend == "huggingface":
        if not os.getenv(args.hf_token_env):
            warnings.append(f"Environment variable {args.hf_token_env} is not set; Hugging Face backend will fail unless a token is supplied.")
        return {
            "method": "huggingface",
            "hf_space": model,
            "hf_token_env": args.hf_token_env,
            "hf_token_present": bool(os.getenv(args.hf_token_env)),
        }
    if args.backend == "local_gpu":
        warnings.append("local_gpu is a placeholder in the default InferenceFactory; supply a model manually or choose vllm/ollama.")
        return {"method": "local_gpu", "device": "cuda", "model_placeholder": model}
    if args.backend == "mistral" and not os.getenv(args.mistral_token_env):
        warnings.append(f"Environment variable {args.mistral_token_env} is not set; Mistral backend will fail without it.")
    if args.backend == "mlx" and sys.platform != "darwin":
        warnings.append("MLX backend is Apple Silicon/macOS oriented; this platform is not darwin.")
    return {"method": args.backend, "model_name": model}


def main() -> int:
    args = parse_args()
    warnings: list[str] = []

    if args.crop_size is not None and args.crop_size < 0:
        raise SystemExit(json.dumps({"ok": False, "error": "--crop-size must be non-negative."}, indent=2))

    hints_content = read_hints(args.hints_file_path, warnings)
    prepared = prepare_query(args, hints_content, warnings)
    config = backend_config(args, warnings)

    effective_validation_off = any([
        args.validation_off,
        prepared["mode"] in {"wildcard_all_data", "page_type", "instruction", "field_validation", "markdown_first"},
        args.apply_annotation,
        bool(args.page_type),
    ])

    pipeline_options = [args.backend, args.model or DEFAULT_MODEL_BY_BACKEND[args.backend]]
    for enabled, name in [
        (args.tables_only, "tables_only"),
        (args.validation_off, "validation_off"),
        (args.apply_annotation, "apply_annotation"),
    ]:
        if enabled:
            pipeline_options.append(name)

    if args.apply_annotation and args.backend in {"ollama", "vllm"}:
        warnings.append(f"{args.backend} backend disables annotations in implementation; apply_annotation will not produce bboxes there.")
    if args.tables_only and args.markdown:
        warnings.append("tables_only and markdown-first are separate flows; use one primary extraction strategy per run.")

    plan = {
        "ok": True,
        "safe_no_model_invocation": True,
        "query_mode": prepared["mode"],
        "backend_config": config,
        "pipeline_options": pipeline_options,
        "input_data": [{"file_path": args.file_path, "text_input": prepared["text_input"]}],
        "run_inference_kwargs": {
            "tables_only": args.tables_only,
            "generic_query": prepared["generic_query"],
            "crop_size": args.crop_size,
            "apply_annotation": args.apply_annotation,
            "ocr_callback": None,
            "debug_dir": args.debug_dir,
            "debug": args.debug,
            "mode": None,
        },
        "query_schema": prepared.get("query_schema"),
        "schema_validated_by_builder": prepared.get("schema_validated_by_builder", False),
        "hints_included": bool(hints_content),
        "effective_pipeline_validation_off": effective_validation_off,
        "warnings": warnings,
        "next_steps": [
            "Review the prepared text_input before running a backend.",
            "Run parse_input_smoke.py to check no-model package wiring in the target environment.",
            "Only then instantiate InferenceFactory and VLLMExtractor with the selected backend.",
        ],
    }
    if "markdown_second_stage_schema_query" in prepared:
        plan["markdown_second_stage"] = {
            "schema_query": prepared["markdown_second_stage_schema_query"],
            "hints_included": prepared["markdown_second_stage_hints_included"],
            "note": "Engine markdown flow converts the document to markdown first, then asks an instructor backend to extract this schema from markdown.",
        }

    output = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
