#!/usr/bin/env python3
"""Build safe Sparrow CLI/curl request templates without sending them."""
from __future__ import annotations

import argparse
import json
import shlex
from typing import Any


def q(value: str) -> str:
    return shlex.quote(value)


def split_csv(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        out.extend(part.strip() for part in value.split(",") if part.strip())
    return out


def validate_json_query(query: str) -> dict[str, Any]:
    if query == "*":
        return {"kind": "wildcard", "validJson": False, "notes": ["Wildcard all-data/page-type query bypasses normal schema validation."]}
    try:
        parsed = json.loads(query)
        return {"kind": type(parsed).__name__, "validJson": True, "parsed": parsed, "notes": []}
    except json.JSONDecodeError as exc:
        return {"kind": "text", "validJson": False, "error": str(exc), "notes": ["Use --instruction for free-text instruction processing, or fix the JSON schema."]}


def add_options(parts: list[str], options: list[str]) -> None:
    for opt in options:
        parts.extend(["--options", q(opt)])


def build_extraction(args: argparse.Namespace) -> dict[str, Any]:
    options = [args.backend, args.model] + split_csv(args.option)
    validation = validate_json_query(args.query)

    cli_parts = ["./sparrow.sh", q(args.query), "--pipeline", q(args.pipeline)]
    add_options(cli_parts, options)
    if args.file_path:
        cli_parts.extend(["--file-path", q(args.file_path)])
    if args.hints_file_path:
        cli_parts.extend(["--hints-file-path", q(args.hints_file_path)])
    if args.crop_size is not None:
        cli_parts.extend(["--crop-size", str(args.crop_size)])
    for page_type in split_csv(args.page_type):
        cli_parts.extend(["--page-type", q(page_type)])
    for flag in ["instruction", "validation", "markdown", "ocr", "table", "debug"]:
        if getattr(args, flag):
            cli_parts.append(f"--{flag.replace('_', '-')}")
    if args.table_template:
        cli_parts.extend(["--table-template", q(args.table_template)])
    if args.debug_dir:
        cli_parts.extend(["--debug-dir", q(args.debug_dir)])

    curl_parts = [
        "curl", "-X", "POST", q(f"{args.base_url.rstrip('/')}/api/v1/sparrow-llm/inference"),
        "-H", q("Content-Type: multipart/form-data"),
        "-F", q(f"query={args.query}"),
        "-F", q(f"pipeline={args.pipeline}"),
        "-F", q("options=" + ",".join(options)),
    ]
    if args.file_path:
        curl_parts.extend(["-F", q(f"file=@{args.file_path}")])
    if args.hints_file_path:
        curl_parts.extend(["-F", q(f"hints_file=@{args.hints_file_path}")])
    if args.crop_size is not None:
        curl_parts.extend(["-F", q(f"crop_size={args.crop_size}")])
    for name in ["instruction", "validation", "markdown", "ocr", "table", "debug"]:
        if getattr(args, name):
            curl_parts.extend(["-F", q(f"{name}=true")])
    if args.table_template:
        curl_parts.extend(["-F", q(f"table_template={args.table_template}")])
    pts = split_csv(args.page_type)
    if pts:
        curl_parts.extend(["-F", q("page_type=" + ",".join(pts))])
    if args.sparrow_key:
        curl_parts.extend(["-F", q(f"sparrow_key={args.sparrow_key}")])

    return {
        "surface": "extraction",
        "queryValidation": validation,
        "options": options,
        "cli": " ".join(cli_parts),
        "curl": " ".join(curl_parts),
        "warnings": warnings_for_backend(args.backend),
    }


def build_instruction(args: argparse.Namespace) -> dict[str, Any]:
    options = [args.backend, args.model]
    cli = " ".join(["./sparrow.sh", q(args.query), "--pipeline", q(args.pipeline), "--instruction", "--options", q(args.backend), "--options", q(args.model)])
    curl = " ".join([
        "curl", "-X", "POST", q(f"{args.base_url.rstrip('/')}/api/v1/sparrow-llm/instruction-inference"),
        "-H", q("Content-Type: application/x-www-form-urlencoded"),
        "-d", q(f"query={args.query}"),
        "-d", q(f"pipeline={args.pipeline}"),
        "-d", q("options=" + ",".join(options)),
    ])
    return {"surface": "instruction", "options": options, "cli": cli, "curl": curl, "warnings": warnings_for_backend(args.backend)}


def build_ocr(args: argparse.Namespace) -> dict[str, Any]:
    endpoint = f"{args.base_url.rstrip('/')}/api/v1/sparrow-ocr/inference"
    parts = ["curl", "-X", "POST", q(endpoint), "-H", q("Content-Type: multipart/form-data")]
    if args.file_path:
        parts.extend(["-F", q(f"file=@{args.file_path}")])
    if args.image_url:
        parts.extend(["-F", q(f"image_url={args.image_url}")])
    for flag in ["include_bbox", "enhance_tables", "debug"]:
        if getattr(args, flag):
            parts.extend(["-F", q(f"{flag}=true")])
    warnings: list[str] = []
    if not args.file_path and not args.image_url:
        warnings.append("No file or image_url supplied; service returns an informational response instead of OCR output.")
    if args.file_path and args.image_url:
        warnings.append("Provide either file or image_url for clarity; endpoint prioritizes upload branch when file is present.")
    return {"surface": "ocr", "curl": " ".join(parts), "warnings": warnings}


def build_agent(args: argparse.Namespace) -> dict[str, Any]:
    endpoint = f"{args.base_url.rstrip('/')}/api/v1/sparrow-agents/execute/{args.mode}{'/async' if args.async_mode else ''}"
    warnings: list[str] = []
    if args.mode == "data":
        payload = {"agent_name": args.agent_name, "input_data": json.loads(args.input_json or "{}")}
        curl = " ".join(["curl", "-X", "POST", q(endpoint), "-H", q("Content-Type: application/json"), "-d", q(json.dumps(payload))])
    else:
        params = args.extraction_params or '{"sparrow_key":"12345"}'
        try:
            json.loads(params)
        except json.JSONDecodeError as exc:
            warnings.append(f"extraction_params is not valid JSON: {exc}")
        curl_parts = ["curl", "-X", "POST", q(endpoint), "-H", q("Content-Type: multipart/form-data"), "-F", q(f"agent_name={args.agent_name}"), "-F", q(f"extraction_params={params}")]
        if args.file_path:
            curl_parts.extend(["-F", q(f"file=@{args.file_path}")])
        else:
            warnings.append("File agents require a file upload.")
        curl = " ".join(curl_parts)
    if args.async_mode:
        warnings.append("Async agent requests require Redis and a Celery worker for the selected queue.")
    return {"surface": "agent", "curl": curl, "warnings": warnings}


def warnings_for_backend(backend: str) -> list[str]:
    backend = backend.lower()
    if backend == "mlx":
        return ["MLX requires Apple Silicon macOS and an MLX-compatible model."]
    if backend == "vllm":
        return ["vLLM requires a compatible GPU/runtime and model availability; a CPU import is not enough."]
    if backend == "ollama":
        return ["Ollama requires a running daemon and a pulled model with the exact name."]
    if backend in {"mistral", "huggingface"}:
        return ["Cloud/remote backends require credentials or reachable endpoints; keep tokens out of commands saved in files."]
    return []


def print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"Surface: {result['surface']}")
    for key in ["cli", "curl"]:
        if key in result:
            print(f"\n{key.upper()}:\n{result[key]}")
    if "queryValidation" in result:
        print("\nQuery validation:")
        print(json.dumps(result["queryValidation"], indent=2))
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")


def add_common_model(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--backend", default="ollama", help="Backend method such as mlx, vllm, ollama, huggingface, or mistral.")
    parser.add_argument("--model", default="model-name", help="Model name, HF Space, or backend identifier.")
    parser.add_argument("--base-url", default="http://localhost:8002", help="Base URL for the relevant Sparrow service.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Sparrow command/curl templates without sending requests.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extraction", help="Build Sparrow LLM extraction API and CLI templates.")
    add_common_model(p)
    p.add_argument("--query", required=True)
    p.add_argument("--pipeline", default="sparrow-parse")
    p.add_argument("--file-path")
    p.add_argument("--hints-file-path")
    p.add_argument("--crop-size", type=int)
    p.add_argument("--option", action="append", help="Additional backend option; may be repeated or comma-separated.")
    p.add_argument("--page-type", action="append", help="Page type; may be repeated or comma-separated.")
    p.add_argument("--table-template")
    p.add_argument("--debug-dir")
    p.add_argument("--sparrow-key")
    for flag in ["instruction", "validation", "markdown", "ocr", "table", "debug"]:
        p.add_argument(f"--{flag.replace('_', '-')}", action="store_true")
    p.set_defaults(func=build_extraction)

    p = sub.add_parser("instruction", help="Build instruction-inference templates.")
    add_common_model(p)
    p.add_argument("--query", required=True)
    p.add_argument("--pipeline", default="sparrow-instructor")
    p.set_defaults(func=build_instruction)

    p = sub.add_parser("ocr", help="Build OCR service curl template.")
    p.add_argument("--base-url", default="http://localhost:8004")
    p.add_argument("--file-path")
    p.add_argument("--image-url")
    p.add_argument("--include-bbox", action="store_true")
    p.add_argument("--enhance-tables", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.set_defaults(func=build_ocr)

    p = sub.add_parser("agent", help="Build Sparrow Agents curl template.")
    p.add_argument("--base-url", default="http://localhost:8003")
    p.add_argument("--mode", choices=["data", "file"], default="data")
    p.add_argument("--async-mode", action="store_true")
    p.add_argument("--agent-name", default="trading")
    p.add_argument("--input-json", help="JSON input_data for data agents.")
    p.add_argument("--file-path")
    p.add_argument("--extraction-params")
    p.set_defaults(func=build_agent)

    args = parser.parse_args()
    result = args.func(args)
    print_result(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
