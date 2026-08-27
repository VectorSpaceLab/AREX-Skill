#!/usr/bin/env python3
"""Safe Chonkie CLI/API interface smoke checks.

This script is intentionally non-invasive:
- runs only `chonkie ... --help` subprocess checks for the CLI;
- imports and inspects the FastAPI app/schema without starting a server;
- inspects Chonkie Cloud class signatures without constructing clients or using
  credentials.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable


EXPECTED_ROUTES = {
    "/",
    "/health",
    "/v1/chunk/token",
    "/v1/chunk/sentence",
    "/v1/chunk/recursive",
    "/v1/chunk/semantic",
    "/v1/chunk/code",
    "/v1/refine/overlap",
    "/v1/refine/embeddings",
    "/v1/pipelines",
    "/v1/pipelines/{pipeline_id}",
    "/v1/pipelines/{pipeline_id}/execute",
}

CLI_CHECKS: list[tuple[list[str], list[str]]] = [
    (["--help"], ["chunk", "pipeline", "serve"]),
    (["chunk", "--help"], ["--chunker", "--chunk-size", "--chunk-overlap", "--threshold", "--chunker-params", "--handshaker"]),
    (["pipeline", "--help"], ["--fetcher", "--d", "--ext", "--chef", "--chunker", "--refiner", "--handshaker"]),
    (["serve", "--help"], ["--host", "--port", "--reload", "--log-level"]),
]


@dataclass
class SmokeResult:
    passed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def ok(self, message: str) -> None:
        self.passed.append(message)

    def skip(self, message: str) -> None:
        self.skipped.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)


def _prefix_from_command(command: str | None) -> list[str] | None:
    if command:
        return shlex.split(command)
    found = shutil.which("chonkie")
    if found:
        return [found]
    return None


def run_cli_checks(result: SmokeResult, *, skip_cli: bool, cli_command: str | None, timeout: float) -> None:
    if skip_cli:
        result.skip("CLI checks skipped by --skip-cli")
        return

    prefix = _prefix_from_command(cli_command)
    if prefix is None:
        result.fail("chonkie console command not found; rerun with --skip-cli to check Python API imports only")
        return

    cli_details: dict[str, Any] = {}
    for args, expected_terms in CLI_CHECKS:
        label = " ".join([*prefix, *args])
        try:
            proc = subprocess.run(
                [*prefix, *args],
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            result.fail(f"CLI help timed out: {label}")
            continue
        except OSError as exc:
            result.fail(f"CLI help failed to execute {label!r}: {exc}")
            continue

        combined = f"{proc.stdout}\n{proc.stderr}"
        cli_details[label] = {
            "returncode": proc.returncode,
            "stdout_preview": proc.stdout[:500],
            "stderr_preview": proc.stderr[:500],
        }
        if proc.returncode != 0:
            result.fail(f"CLI help returned {proc.returncode}: {label}")
            continue
        missing = [term for term in expected_terms if term not in combined]
        if missing:
            result.fail(f"CLI help missing expected terms for {label}: {missing}")
        else:
            result.ok(f"CLI help ok: {' '.join(args)}")

    result.details["cli"] = cli_details


def _model_fields(model_cls: type[Any]) -> set[str]:
    fields = getattr(model_cls, "model_fields", None)
    if fields is not None:
        return set(fields)
    fields = getattr(model_cls, "__fields__", None)
    if fields is not None:
        return set(fields)
    return set()


def _dump_model(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    raise TypeError(f"Cannot dump Pydantic model {type(obj)!r}")


def assert_fields(result: SmokeResult, cls: type[Any], required: Iterable[str]) -> None:
    fields = _model_fields(cls)
    missing = [name for name in required if name not in fields]
    if missing:
        result.fail(f"{cls.__name__} missing fields: {missing}")
    else:
        result.ok(f"schema fields ok: {cls.__name__}")


def run_api_schema_checks(result: SmokeResult) -> None:
    # Keep imports quiet and host-controlled. This must be set before importing
    # chonkie.api.main because that module configures logging at import time.
    os.environ.setdefault("CHONKIE_LOG", "unconfigured")

    try:
        api_main = importlib.import_module("chonkie.api.main")
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report import failures
        result.fail(f"failed to import chonkie.api.main: {type(exc).__name__}: {exc}")
        return

    app = getattr(api_main, "app", None)
    if app is None:
        result.fail("chonkie.api.main does not expose app")
        return

    result.ok(f"FastAPI app imported: {getattr(app, 'title', '<unknown title>')}")

    routes = sorted({getattr(route, "path", "") for route in getattr(app, "routes", []) if getattr(route, "path", "")})
    openapi_paths: set[str] = set()
    try:
        openapi = app.openapi()
        openapi_paths = set(openapi.get("paths", {}))
        result.ok(f"OpenAPI schema generated with {len(openapi_paths)} paths")
        result.details["openapi_path_count"] = len(openapi_paths)
    except Exception as exc:  # noqa: BLE001
        result.fail(f"OpenAPI generation failed: {type(exc).__name__}: {exc}")

    advertised_paths = set(routes) | openapi_paths
    missing_routes = sorted(EXPECTED_ROUTES.difference(advertised_paths))
    if missing_routes:
        result.fail(f"FastAPI app/OpenAPI schema missing expected routes: {missing_routes}")
    else:
        result.ok(f"FastAPI app/OpenAPI schema contains {len(EXPECTED_ROUTES)} expected paths")

    try:
        schemas = importlib.import_module("chonkie.api.schemas")
    except Exception as exc:  # noqa: BLE001
        result.fail(f"failed to import chonkie.api.schemas: {type(exc).__name__}: {exc}")
        return

    schema_expectations = {
        "TokenChunkerRequest": ["text", "tokenizer", "chunk_size", "chunk_overlap"],
        "SentenceChunkerRequest": ["text", "tokenizer", "chunk_size", "chunk_overlap", "min_sentences_per_chunk"],
        "RecursiveChunkerRequest": ["text", "tokenizer", "chunk_size", "recipe", "lang", "min_characters_per_chunk"],
        "SemanticChunkerRequest": ["text", "embedding_model", "threshold", "chunk_size", "similarity_window"],
        "CodeChunkerRequest": ["text", "tokenizer", "chunk_size", "language", "include_nodes"],
        "PipelineStepRequest": ["type", "chunker", "refinery", "config"],
        "PipelineCreateRequest": ["name", "description", "steps"],
        "PipelineExecuteRequest": ["text"],
        "OverlapRefineryRequest": ["chunks", "tokenizer", "context_size", "mode", "method", "merge"],
        "EmbeddingsRefineryRequest": ["chunks", "embedding_model"],
    }
    for name, required in schema_expectations.items():
        cls = getattr(schemas, name, None)
        if cls is None:
            result.fail(f"schema class missing: {name}")
            continue
        assert_fields(result, cls, required)

    try:
        token_req = schemas.TokenChunkerRequest(text="hello world", chunk_size=8, chunk_overlap=0)
        rec_req = schemas.RecursiveChunkerRequest(text=["# A\n\nBody."], chunk_size=64, recipe="markdown")
        step = schemas.PipelineStepRequest(type="chunk", chunker="token", config={"chunk_size": 8})
        pipe_req = schemas.PipelineCreateRequest(name="smoke-token", steps=[step])
        result.details["schema_samples"] = {
            "token": _dump_model(token_req),
            "recursive": _dump_model(rec_req),
            "pipeline": _dump_model(pipe_req),
        }
        result.ok("Pydantic schema instantiation ok")
    except Exception as exc:  # noqa: BLE001
        result.fail(f"Pydantic schema instantiation failed: {type(exc).__name__}: {exc}")

    result.details["routes"] = routes


def run_cloud_signature_checks(result: SmokeResult) -> None:
    try:
        cloud = importlib.import_module("chonkie.cloud")
    except Exception as exc:  # noqa: BLE001
        result.warn(f"could not import chonkie.cloud for signature inspection: {type(exc).__name__}: {exc}")
        return

    names = [
        "Pipeline",
        "PipelineStep",
        "FileManager",
        "TokenChunker",
        "SentenceChunker",
        "RecursiveChunker",
        "SemanticChunker",
        "CodeChunker",
        "LateChunker",
        "NeuralChunker",
        "SlumberChunker",
        "OverlapRefinery",
        "EmbeddingsRefinery",
    ]
    signatures: dict[str, str] = {}
    for name in names:
        obj = getattr(cloud, name, None)
        if obj is None:
            result.fail(f"cloud export missing: {name}")
            continue
        target = getattr(obj, "__init__", obj)
        try:
            signatures[name] = str(inspect.signature(target))
        except (TypeError, ValueError):
            signatures[name] = "<signature unavailable>"
    if "Pipeline" in signatures and "slug" in signatures["Pipeline"]:
        result.ok("cloud exports/signatures inspected without constructing credentialed clients")
    else:
        result.fail("cloud Pipeline signature did not expose expected slug parameter")
    result.details["cloud_signatures"] = signatures


def emit_text(result: SmokeResult) -> None:
    print("Chonkie interfaces smoke")
    for message in result.passed:
        print(f"PASS: {message}")
    for message in result.skipped:
        print(f"SKIP: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    for message in result.errors:
        print(f"FAIL: {message}")
    print(f"Summary: {len(result.passed)} passed, {len(result.skipped)} skipped, {len(result.warnings)} warnings, {len(result.errors)} errors")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe Chonkie CLI/FastAPI/cloud signature smoke checks.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip chonkie CLI subprocess help checks.")
    parser.add_argument("--cli-command", help="Command prefix for the Chonkie CLI, e.g. 'python -m chonkie.cli' or '/path/to/chonkie'. Defaults to PATH lookup for 'chonkie'.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Timeout in seconds for each CLI help subprocess. Default: 15.")
    parser.add_argument("--json", action="store_true", help="Emit JSON diagnostics instead of human-readable text.")
    args = parser.parse_args(argv)

    result = SmokeResult()
    run_cli_checks(result, skip_cli=args.skip_cli, cli_command=args.cli_command, timeout=args.timeout)
    run_api_schema_checks(result)
    run_cloud_signature_checks(result)

    if args.json:
        print(json.dumps({
            "passed": result.passed,
            "skipped": result.skipped,
            "warnings": result.warnings,
            "errors": result.errors,
            "details": result.details,
        }, indent=2, sort_keys=True, default=str))
    else:
        emit_text(result)

    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
