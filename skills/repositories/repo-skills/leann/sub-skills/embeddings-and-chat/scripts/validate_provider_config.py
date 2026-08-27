#!/usr/bin/env python3
"""Offline, secret-safe validation for LEANN LLM and embedding config JSON.

The validator performs schema and environment-presence checks only. It never
imports LEANN/provider packages, contacts a service, downloads a model, or emits
credential values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


LLM_TYPES = ("openai", "ollama", "hf", "anthropic")
EMBEDDING_MODES = ("sentence-transformers", "mlx", "openai")

OPENAI_KEY_ENV = ("OPENAI_API_KEY",)
OPENAI_URL_ENV = (
    "LEANN_OPENAI_BASE_URL",
    "OPENAI_BASE_URL",
    "LOCAL_OPENAI_BASE_URL",
)
ANTHROPIC_KEY_ENV = ("ANTHROPIC_API_KEY",)
ANTHROPIC_URL_ENV = (
    "LEANN_ANTHROPIC_BASE_URL",
    "ANTHROPIC_BASE_URL",
    "LOCAL_ANTHROPIC_BASE_URL",
)
OLLAMA_HOST_ENV = (
    "LEANN_LOCAL_LLM_HOST",
    "LEANN_OLLAMA_HOST",
    "OLLAMA_HOST",
    "LOCAL_LLM_ENDPOINT",
)
HF_ENV = ("LEANN_LLM_DEVICE",)
SENTENCE_TRANSFORMERS_ENV = (
    "LEANN_EMBEDDING_DEVICE",
    "LEANN_CPU_THREADS",
    "LEANN_CUDA_BATCH_SIZE",
    "LEANN_MPS_BATCH_SIZE",
    "LEANN_CUDA_AUTO_BATCH",
)


@dataclass
class Result:
    kind: str
    provider: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    credential_source: str = "not-required"
    environment: dict[str, bool] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not self.errors


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_optional_string(config: dict[str, Any], key: str, result: Result) -> None:
    if key in config and config[key] is not None and not _nonempty_string(config[key]):
        result.errors.append(f"{key} must be a non-empty string or null")


def _check_url(config: dict[str, Any], key: str, result: Result) -> None:
    if key not in config or config[key] is None:
        return
    if not _nonempty_string(config[key]):
        result.errors.append(f"{key} must be a non-empty HTTP(S) URL or null")
        return
    parsed = urlsplit(config[key])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        result.errors.append(f"{key} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        result.errors.append(f"{key} must not embed credentials in the URL")


def _check_unknown_fields(
    config: dict[str, Any], allowed: set[str], result: Result, scope: str
) -> None:
    unknown_count = sum(1 for key in config if key not in allowed)
    if unknown_count:
        allowed_text = ", ".join(sorted(allowed))
        result.errors.append(
            f"{scope} has {unknown_count} unknown field(s); allowed fields: {allowed_text}"
        )


def _env_state(names: tuple[str, ...]) -> dict[str, bool]:
    return {name: bool(os.getenv(name)) for name in names}


def _credential_source(
    config: dict[str, Any], field_name: str, env_names: tuple[str, ...]
) -> str:
    if _nonempty_string(config.get(field_name)):
        return "config-field (value redacted)"
    for name in env_names:
        if os.getenv(name):
            return f"environment:{name} (value redacted)"
    return "missing"


def _require_model_if_present(config: dict[str, Any], result: Result) -> None:
    if "model" in config and not _nonempty_string(config["model"]):
        result.errors.append("model must be a non-empty string")


def validate_llm(config: dict[str, Any], require_credentials: bool) -> Result:
    raw_type = config.get("type", "openai")
    provider = raw_type if raw_type in LLM_TYPES else "invalid"
    result = Result(kind="llm", provider=provider)

    if provider == "invalid":
        result.errors.append(f"type must be one of: {', '.join(LLM_TYPES)}")
        return result

    common = {"type", "model"}
    _require_model_if_present(config, result)
    if "model" not in config:
        result.warnings.append("model is omitted; LEANN will use the provider default")

    if provider == "openai":
        _check_unknown_fields(config, common | {"api_key", "base_url"}, result, "openai config")
        _check_optional_string(config, "api_key", result)
        _check_url(config, "base_url", result)
        result.credential_source = _credential_source(config, "api_key", OPENAI_KEY_ENV)
        result.environment = _env_state(OPENAI_KEY_ENV + OPENAI_URL_ENV)
        if result.credential_source == "missing":
            message = (
                "no OpenAI credential is configured; current LEANN runtime initialization "
                "will fail until a nonempty value is supplied"
            )
            (result.errors if require_credentials else result.warnings).append(message)

    elif provider == "anthropic":
        _check_unknown_fields(
            config, common | {"api_key", "base_url"}, result, "anthropic config"
        )
        _check_optional_string(config, "api_key", result)
        _check_url(config, "base_url", result)
        result.credential_source = _credential_source(config, "api_key", ANTHROPIC_KEY_ENV)
        result.environment = _env_state(ANTHROPIC_KEY_ENV + ANTHROPIC_URL_ENV)
        if result.credential_source == "missing":
            message = "no Anthropic credential is configured"
            (result.errors if require_credentials else result.warnings).append(message)

    elif provider == "ollama":
        _check_unknown_fields(config, common | {"host"}, result, "ollama config")
        _check_url(config, "host", result)
        result.environment = _env_state(OLLAMA_HOST_ENV)

    elif provider == "hf":
        _check_unknown_fields(
            config, common | {"trust_remote_code"}, result, "Hugging Face config"
        )
        if "trust_remote_code" in config and not isinstance(config["trust_remote_code"], bool):
            result.errors.append("trust_remote_code must be a boolean")
        if config.get("trust_remote_code") is True:
            result.warnings.append(
                "trust_remote_code=true executes code from the model repository; use only after review"
            )
        result.environment = _env_state(HF_ENV)

    return result


def _check_template_options(options: dict[str, Any], result: Result) -> None:
    for key in ("build_prompt_template", "query_prompt_template", "prompt_template"):
        if key in options and not isinstance(options[key], str):
            result.errors.append(f"embedding_options.{key} must be a string")


def validate_embedding(config: dict[str, Any], require_credentials: bool) -> Result:
    raw_mode = config.get("embedding_mode", "sentence-transformers")
    mode = raw_mode if raw_mode in EMBEDDING_MODES else "invalid"
    result = Result(kind="embedding", provider=mode)

    top_allowed = {"embedding_mode", "embedding_model", "embedding_options", "dimensions"}
    _check_unknown_fields(config, top_allowed, result, "embedding config")

    if mode == "invalid":
        result.errors.append(f"embedding_mode must be one of: {', '.join(EMBEDDING_MODES)}")
        return result

    model = config.get("embedding_model")
    if model is not None and not _nonempty_string(model):
        result.errors.append("embedding_model must be a non-empty string")
    if mode != "sentence-transformers" and model is None:
        result.errors.append(f"embedding_model is required for embedding_mode={mode}")

    dimensions = config.get("dimensions")
    if dimensions is not None and (
        isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions < 1
    ):
        result.errors.append("dimensions must be a positive integer or null")

    options = config.get("embedding_options", {})
    if options is None:
        options = {}
    if not isinstance(options, dict):
        result.errors.append("embedding_options must be a JSON object or null")
        return result

    if mode == "sentence-transformers":
        _check_unknown_fields(
            options, {"batch_size"}, result, "sentence-transformers embedding_options"
        )
        if "batch_size" in options and (
            isinstance(options["batch_size"], bool)
            or not isinstance(options["batch_size"], int)
            or options["batch_size"] < 1
        ):
            result.errors.append("embedding_options.batch_size must be a positive integer")
        result.environment = _env_state(SENTENCE_TRANSFORMERS_ENV)

    elif mode == "mlx":
        _check_unknown_fields(options, set(), result, "MLX embedding_options")
        result.warnings.append(
            "MLX availability and model cache are not checked; this mode is intended for Apple silicon"
        )

    elif mode == "openai":
        allowed = {
            "api_key",
            "base_url",
            "build_prompt_template",
            "query_prompt_template",
            "prompt_template",
        }
        _check_unknown_fields(options, allowed, result, "OpenAI embedding_options")
        _check_optional_string(options, "api_key", result)
        _check_url(options, "base_url", result)
        _check_template_options(options, result)
        result.credential_source = _credential_source(options, "api_key", OPENAI_KEY_ENV)
        result.environment = _env_state(OPENAI_KEY_ENV + OPENAI_URL_ENV)
        if result.credential_source == "missing":
            message = (
                "no OpenAI embedding credential is configured; current LEANN runtime "
                "initialization will fail until a nonempty value is supplied"
            )
            (result.errors if require_credentials else result.warnings).append(message)

    if dimensions is not None:
        result.warnings.append(
            "declared dimensions are not an output transform; they must equal the model's actual width"
        )

    return result


def _load_config(path_text: str) -> dict[str, Any]:
    if path_text == "-":
        text = sys.stdin.read()
    else:
        text = Path(path_text).expanduser().read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def _detect_kind(config: dict[str, Any]) -> str:
    embedding_keys = {"embedding_mode", "embedding_model", "embedding_options", "dimensions"}
    return "embedding" if embedding_keys.intersection(config) else "llm"


def _render_text(result: Result) -> str:
    status = "VALID" if result.valid else "INVALID"
    lines = [f"{status}: {result.kind} configuration for {result.provider}"]
    lines.append(f"Credential source: {result.credential_source}")
    if result.environment:
        lines.append("Environment names (values never shown):")
        for name, present in result.environment.items():
            lines.append(f"  - {name}: {'set' if present else 'unset'}")
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {message}" for message in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"  - {message}" for message in result.errors)
    return "\n".join(lines)


def _render_json(result: Result) -> str:
    payload = {
        "valid": result.valid,
        "kind": result.kind,
        "provider": result.provider,
        "credential_source": result.credential_source,
        "environment": result.environment,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate LEANN LLM or embedding configuration JSON offline without "
            "printing secrets or contacting providers."
        )
    )
    parser.add_argument("config", help="JSON file path, or '-' to read JSON from stdin")
    parser.add_argument(
        "--kind",
        choices=("auto", "llm", "embedding"),
        default="auto",
        help="Configuration shape (default: infer from embedding_* keys)",
    )
    parser.add_argument(
        "--require-credentials",
        action="store_true",
        help="Fail when a provider that requires a key has neither an inline key nor its documented env key",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format; both formats redact credential values (default: text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = _load_config(args.config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        # JSON decoder messages contain line/column, not document contents.
        print(f"INVALID: could not load configuration: {exc}", file=sys.stderr)
        return 2

    kind = _detect_kind(config) if args.kind == "auto" else args.kind
    if kind == "llm":
        result = validate_llm(config, args.require_credentials)
    else:
        result = validate_embedding(config, args.require_credentials)

    print(_render_json(result) if args.format == "json" else _render_text(result))
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
