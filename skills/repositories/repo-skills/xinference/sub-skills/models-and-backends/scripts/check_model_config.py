#!/usr/bin/env python3
"""Validate a Xinference custom model JSON without downloading models.

The checker stays offline. It only reads JSON, validates the declared or
inferred model shape, and can print a register-command template.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Sequence
from urllib.parse import urlparse

MODEL_NAME_RE = re.compile(r"^[^+\/?%#&=\s]*$")

TYPE_ALIASES = {
    "llm": "LLM",
    "LLM": "LLM",
    "embedding": "embedding",
    "rerank": "rerank",
    "image": "image",
    "audio": "audio",
    "flexible": "flexible",
    "video": "video",
}

COMMON_TOP_LEVEL = {
    "version",
    "model_type",
    "model_name",
    "model_id",
    "model_revision",
    "model_hub",
    "model_uri",
    "cache_config",
    "virtualenv",
    "is_builtin",
}

LLM_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "context_length",
    "model_lang",
    "model_ability",
    "model_description",
    "model_family",
    "model_specs",
    "chat_template",
    "stop_token_ids",
    "stop",
    "architectures",
    "reasoning_start_tag",
    "reasoning_end_tag",
    "tool_parser",
}

EMBEDDING_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "dimensions",
    "max_tokens",
    "language",
    "model_specs",
}

RERANK_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "language",
    "type",
    "max_tokens",
    "model_specs",
}

IMAGE_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "model_family",
    "model_ability",
    "controlnet",
    "default_model_config",
    "default_generate_config",
    "gguf_model_id",
    "gguf_quantizations",
    "gguf_model_file_name_template",
    "lightning_model_id",
    "lightning_versions",
    "lightning_model_file_name_template",
}

AUDIO_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "model_family",
    "multilingual",
    "language",
    "model_ability",
    "default_model_config",
    "default_transcription_config",
    "engine",
}

FLEXIBLE_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "model_description",
    "launcher",
    "launcher_args",
}

VIDEO_TOP_LEVEL = COMMON_TOP_LEVEL | {
    "model_family",
    "model_ability",
    "default_model_config",
    "default_generate_config",
    "gguf_model_id",
    "gguf_quantizations",
    "gguf_model_file_name_template",
}

SPEC_FIELDS = {
    "model_format",
    "model_size_in_billions",
    "quantization",
    "model_id",
    "model_uri",
    "model_hub",
    "model_revision",
    "activated_size_in_billions",
    "multimodal_projectors",
    "model_file_name_template",
    "model_file_name_split_template",
    "quantization_parts",
    "draft_model_id",
    "draft_model_file_name_template",
    "draft_quantizations",
    "draft_model_revision",
    "quantizations",
}

SPEC_REQUIRED_COMMON = {"model_format", "quantization"}
SPEC_REQUIRED_LLM = SPEC_REQUIRED_COMMON | {"model_size_in_billions"}


@dataclass
class Issue:
    level: str
    path: str
    message: str


@dataclass
class ValidationResult:
    model_type: str
    errors: list[Issue]
    warnings: list[Issue]

    @property
    def ok(self) -> bool:
        return not self.errors


class ValidationError(Exception):
    pass


def normalize_model_type(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    return TYPE_ALIASES.get(value, TYPE_ALIASES.get(value.lower()))


def is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def add_issue(store: list[Issue], level: str, path: str, message: str) -> None:
    store.append(Issue(level=level, path=path, message=message))


def infer_model_type(payload: Mapping[str, Any]) -> str:
    if "model_type" in payload:
        explicit = normalize_model_type(payload.get("model_type"))
        if explicit:
            return explicit
        raise ValidationError(f"Unsupported model_type value: {payload.get('model_type')!r}")

    if "model_src" in payload:
        return "catalog"
    if "launcher" in payload:
        return "flexible"
    if "multilingual" in payload or "default_transcription_config" in payload:
        return "audio"
    if any(key in payload for key in ("controlnet", "lightning_model_id", "gguf_model_file_name_template", "default_generate_config")):
        if "model_family" in payload:
            return "image"
    if "dimensions" in payload:
        return "embedding"
    if "model_specs" in payload:
        llm_signals = {
            "model_lang",
            "model_ability",
            "context_length",
            "chat_template",
            "stop_token_ids",
            "stop",
            "reasoning_start_tag",
            "reasoning_end_tag",
            "architectures",
            "tool_parser",
        }
        if any(key in payload for key in llm_signals):
            return "LLM"
        if "type" in payload or "language" in payload:
            return "rerank"
    raise ValidationError("Could not infer model type; add \"model_type\" or use a more specific payload shape.")


def expected_top_level_fields(model_type: str) -> set[str]:
    return {
        "LLM": LLM_TOP_LEVEL,
        "embedding": EMBEDDING_TOP_LEVEL,
        "rerank": RERANK_TOP_LEVEL,
        "image": IMAGE_TOP_LEVEL,
        "audio": AUDIO_TOP_LEVEL,
        "flexible": FLEXIBLE_TOP_LEVEL,
        "video": VIDEO_TOP_LEVEL,
    }[model_type]


def validate_model_name(name: Any, path: str, errors: list[Issue]) -> None:
    if not isinstance(name, str) or not name:
        add_issue(errors, "error", path, "model_name must be a non-empty string")
        return
    if not MODEL_NAME_RE.match(name):
        add_issue(
            errors,
            "error",
            path,
            "model_name contains disallowed characters; use letters, digits, underscores, or dashes",
        )


def validate_model_uri(uri: Any, path: str, errors: list[Issue], warnings: list[Issue]) -> None:
    if uri in (None, ""):
        return
    if not isinstance(uri, str):
        add_issue(errors, path=path, level="error", message="model_uri must be a string")
        return

    parsed = urlparse(uri)
    scheme = parsed.scheme
    root = parsed.netloc + parsed.path
    if scheme in ("", "file") or len(scheme) == 1:
        if not root:
            add_issue(errors, "error", path, "model_uri file path is empty")
            return
        if not Path(root).is_absolute():
            add_issue(errors, "error", path, f"Model URI cannot be a relative path: {uri}")
            return
        if not Path(root).exists():
            add_issue(errors, "error", path, f"model_uri path does not exist: {uri}")
        return

    add_issue(warnings, "warning", path, f"model_uri uses remote scheme {scheme!r}; the checker does not fetch it")


def validate_size(value: Any, path: str, errors: list[Issue]) -> None:
    if isinstance(value, (int, float)):
        return
    if isinstance(value, str):
        if re.fullmatch(r"\d+(?:_\d+)*", value) or re.fullmatch(r"\d+(?:\.\d+)?", value):
            return
    add_issue(
        errors,
        "error",
        path,
        "model_size_in_billions must be an int, float, or radix-style string such as 1_8",
    )


def validate_virtualenv(value: Any, path: str, errors: list[Issue]) -> None:
    if value is None:
        return
    if not is_mapping(value):
        add_issue(errors, "error", path, "virtualenv must be an object")
        return
    packages = value.get("packages")
    if not isinstance(packages, list) or not all(isinstance(item, str) for item in packages):
        add_issue(errors, "error", f"{path}.packages", "virtualenv.packages must be a list of strings")
    for key in ("inherit_pip_config", "no_build_isolation"):
        if key in value and not isinstance(value[key], bool):
            add_issue(errors, "error", f"{path}.{key}", f"virtualenv.{key} must be a boolean")
    for key in ("index_url", "index_strategy"):
        if key in value and value[key] is not None and not isinstance(value[key], str):
            add_issue(errors, "error", f"{path}.{key}", f"virtualenv.{key} must be a string or null")
    for key in ("extra_index_url", "find_links", "trusted_host"):
        if key not in value or value[key] is None:
            continue
        current = value[key]
        if isinstance(current, str):
            continue
        if isinstance(current, list) and all(isinstance(item, str) for item in current):
            continue
        add_issue(errors, "error", f"{path}.{key}", f"virtualenv.{key} must be a string, list of strings, or null")


def validate_spec(
    spec: Any,
    index: int,
    errors: list[Issue],
    warnings: list[Issue],
    model_type: str,
) -> None:
    spec_path = f"model_specs[{index}]"
    if not is_mapping(spec):
        add_issue(errors, "error", spec_path, "spec must be an object")
        return

    required = SPEC_REQUIRED_LLM if model_type == "LLM" else SPEC_REQUIRED_COMMON
    missing = [field for field in required if field not in spec]
    for field in missing:
        add_issue(errors, "error", f"{spec_path}.{field}", "missing required field")

    unknown = sorted(set(spec) - SPEC_FIELDS)
    for field in unknown:
        add_issue(warnings, "warning", f"{spec_path}.{field}", "unknown field for a custom model spec")

    if "model_format" in spec and not isinstance(spec["model_format"], str):
        add_issue(errors, "error", f"{spec_path}.model_format", "model_format must be a string")

    if "model_size_in_billions" in spec:
        validate_size(spec["model_size_in_billions"], f"{spec_path}.model_size_in_billions", errors)

    if "quantization" in spec and not isinstance(spec["quantization"], str):
        add_issue(errors, "error", f"{spec_path}.quantization", "quantization must be a string")

    if not spec.get("model_id") and not spec.get("model_uri"):
        add_issue(errors, "error", spec_path, "either model_id or model_uri must be present")

    if spec.get("model_uri"):
        validate_model_uri(spec.get("model_uri"), f"{spec_path}.model_uri", errors, warnings)

    if spec.get("model_file_name_template") is not None and not isinstance(spec.get("model_file_name_template"), str):
        add_issue(errors, "error", f"{spec_path}.model_file_name_template", "model_file_name_template must be a string")

    if spec.get("draft_quantizations") is not None:
        dq = spec.get("draft_quantizations")
        if not isinstance(dq, list) or not all(isinstance(item, str) for item in dq):
            add_issue(errors, "error", f"{spec_path}.draft_quantizations", "draft_quantizations must be a list of strings")

    if "quantizations" in spec:
        add_issue(
            warnings,
            "warning",
            f"{spec_path}.quantizations",
            "legacy v1 field; prefer quantization in custom model JSON",
        )

    if spec.get("quantization_parts") is not None and not isinstance(spec.get("quantization_parts"), dict):
        add_issue(errors, "error", f"{spec_path}.quantization_parts", "quantization_parts must be an object")


def validate_model(payload: Mapping[str, Any], model_type: str) -> ValidationResult:
    errors: list[Issue] = []
    warnings: list[Issue] = []

    if model_type == "catalog":
        add_issue(
            errors,
            "error",
            "root",
            "this looks like a model hub catalog entry; direct custom registration JSON is expected instead",
        )
        return ValidationResult(model_type=model_type, errors=errors, warnings=warnings)

    if model_type == "video":
        add_issue(
            warnings,
            "warning",
            "root",
            "video-like custom payloads are recognized, but custom video registration is not supported",
        )

    allowed = expected_top_level_fields(model_type)
    unknown = sorted(set(payload) - allowed)
    for field in unknown:
        add_issue(warnings, "warning", field, "unknown top-level field for this custom model type")

    if "model_name" not in payload:
        add_issue(errors, "error", "model_name", "missing required field")
    else:
        validate_model_name(payload.get("model_name"), "model_name", errors)

    if "version" in payload and model_type != "flexible" and payload.get("version") not in (2, "2"):
        add_issue(warnings, "warning", "version", "custom model families generally use version 2")

    if model_type == "LLM":
        required = ["model_lang", "model_ability", "model_specs"]
        for field in required:
            if field not in payload:
                add_issue(errors, "error", field, "missing required field")
        if not isinstance(payload.get("model_lang"), list):
            add_issue(errors, "error", "model_lang", "model_lang must be a list of strings")
        if not isinstance(payload.get("model_ability"), list):
            add_issue(errors, "error", "model_ability", "model_ability must be a list of strings")
        if not payload.get("model_family"):
            add_issue(errors, "error", "model_family", "missing required field")
        if not isinstance(payload.get("model_specs"), list) or not payload.get("model_specs"):
            add_issue(errors, "error", "model_specs", "model_specs must be a non-empty list")
        for idx, spec in enumerate(payload.get("model_specs", []) if isinstance(payload.get("model_specs"), list) else []):
            validate_spec(spec, idx, errors, warnings, model_type)
        if "chat" in (payload.get("model_ability") or []) and not payload.get("chat_template"):
            add_issue(
                warnings,
                "warning",
                "chat_template",
                "chat_template is missing; Xinference will fall back to model_family, which only works cleanly for built-in prompt styles",
            )
        if payload.get("model_family") and payload.get("model_ability") and "vision" in payload.get("model_ability", []):
            add_issue(
                warnings,
                "warning",
                "model_ability",
                "vision/tool ability matching still depends on the backend family list",
            )
        if payload.get("model_family") and payload.get("model_ability") and "tools" in payload.get("model_ability", []):
            add_issue(
                warnings,
                "warning",
                "model_ability",
                "tool-call support has extra family restrictions",
            )

    elif model_type == "embedding":
        for field in ["dimensions", "max_tokens", "language", "model_specs"]:
            if field not in payload:
                add_issue(errors, "error", field, "missing required field")
        if not isinstance(payload.get("dimensions"), int):
            add_issue(errors, "error", "dimensions", "dimensions must be an integer")
        if not isinstance(payload.get("max_tokens"), int):
            add_issue(errors, "error", "max_tokens", "max_tokens must be an integer")
        if not isinstance(payload.get("language"), list):
            add_issue(errors, "error", "language", "language must be a list of strings")
        if not isinstance(payload.get("model_specs"), list) or not payload.get("model_specs"):
            add_issue(errors, "error", "model_specs", "model_specs must be a non-empty list")
        for idx, spec in enumerate(payload.get("model_specs", []) if isinstance(payload.get("model_specs"), list) else []):
            validate_spec(spec, idx, errors, warnings, model_type)

    elif model_type == "rerank":
        for field in ["language", "model_specs"]:
            if field not in payload:
                add_issue(errors, "error", field, "missing required field")
        if not isinstance(payload.get("language"), list):
            add_issue(errors, "error", "language", "language must be a list of strings")
        if "max_tokens" in payload and payload.get("max_tokens") is not None and not isinstance(payload.get("max_tokens"), int):
            add_issue(errors, "error", "max_tokens", "max_tokens must be an integer when present")
        if not isinstance(payload.get("model_specs"), list) or not payload.get("model_specs"):
            add_issue(errors, "error", "model_specs", "model_specs must be a non-empty list")
        for idx, spec in enumerate(payload.get("model_specs", []) if isinstance(payload.get("model_specs"), list) else []):
            validate_spec(spec, idx, errors, warnings, model_type)

    elif model_type == "image":
        if not payload.get("model_family"):
            add_issue(errors, "error", "model_family", "missing required field")
        if payload.get("controlnet") is not None and not isinstance(payload.get("controlnet"), list):
            add_issue(errors, "error", "controlnet", "controlnet must be a list when present")
        if payload.get("controlnet"):
            for idx, controlnet in enumerate(payload.get("controlnet", [])):
                nested = validate_model(controlnet, "image") if is_mapping(controlnet) else None
                if nested is None:
                    add_issue(errors, "error", f"controlnet[{idx}]", "nested controlnet must be an image-family object")
                elif not nested.ok:
                    for issue in nested.errors:
                        add_issue(errors, issue.level, f"controlnet[{idx}].{issue.path}", issue.message)
                    for issue in nested.warnings:
                        add_issue(warnings, issue.level, f"controlnet[{idx}].{issue.path}", issue.message)
        if not payload.get("model_id") and not payload.get("model_uri"):
            add_issue(errors, "error", "model_id", "either model_id or model_uri must be present for a custom image model")
        if payload.get("model_uri"):
            validate_model_uri(payload.get("model_uri"), "model_uri", errors, warnings)

    elif model_type == "audio":
        if not payload.get("model_family"):
            add_issue(errors, "error", "model_family", "missing required field")
        if "multilingual" not in payload:
            add_issue(errors, "error", "multilingual", "missing required field")
        if not payload.get("model_id") and not payload.get("model_uri"):
            add_issue(errors, "error", "model_id", "either model_id or model_uri must be present for a custom audio model")
        if payload.get("model_uri"):
            validate_model_uri(payload.get("model_uri"), "model_uri", errors, warnings)

    elif model_type == "flexible":
        for field in ["launcher"]:
            if field not in payload:
                add_issue(errors, "error", field, "missing required field")
        if payload.get("launcher_args") is not None:
            if not isinstance(payload.get("launcher_args"), str):
                add_issue(errors, "error", "launcher_args", "launcher_args must be a JSON string")
            else:
                try:
                    json.loads(payload.get("launcher_args"))
                except Exception as exc:
                    add_issue(errors, "error", "launcher_args", f"launcher_args is not valid JSON: {exc}")
        if not payload.get("model_id") and not payload.get("model_uri"):
            add_issue(
                warnings,
                "warning",
                "model_id",
                "flexible models usually need a source path or id, but this checker cannot infer launcher-specific requirements",
            )
        if payload.get("model_uri"):
            validate_model_uri(payload.get("model_uri"), "model_uri", errors, warnings)

    elif model_type == "video":
        if not payload.get("model_family"):
            add_issue(errors, "error", "model_family", "missing required field")
        if not payload.get("model_id") and not payload.get("model_uri"):
            add_issue(errors, "error", "model_id", "either model_id or model_uri must be present for a custom video payload")

    else:
        raise ValidationError(f"Unsupported model type: {model_type}")

    if payload.get("virtualenv") is not None:
        validate_virtualenv(payload.get("virtualenv"), "virtualenv", errors)

    return ValidationResult(model_type=model_type, errors=errors, warnings=warnings)


def format_issues(issues: Iterable[Issue]) -> list[str]:
    lines = []
    for issue in issues:
        location = f"{issue.path}: " if issue.path else ""
        lines.append(f"- {location}{issue.message}")
    return lines


def print_report(result: ValidationResult, print_template: bool, input_path: str) -> int:
    print(f"Detected model type: {result.model_type}")
    if result.ok:
        print("Validation: OK")
    else:
        print("Validation: FAILED")

    if result.errors:
        print("\nErrors:")
        for line in format_issues(result.errors):
            print(line)

    if result.warnings:
        print("\nWarnings:")
        for line in format_issues(result.warnings):
            print(line)

    if print_template and result.ok and result.model_type not in {"catalog", "video"}:
        print("\nRegister command template:")
        print(f"xinference register --model-type {result.model_type} --file {input_path}")
        print("Add --persist if you want the registration stored on disk.")
    elif print_template and result.model_type == "video":
        print("\nRegister command template:")
        print("custom video registration is not supported in this repository")

    return 0 if result.ok else 1


def load_payload(path: str) -> Any:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Xinference custom model JSON offline, without downloads.",
    )
    parser.add_argument(
        "config",
        help="Path to a custom model JSON file, or - for stdin.",
    )
    parser.add_argument(
        "--model-type",
        help="Override the inferred model type (LLM, embedding, rerank, image, audio, flexible, or video).",
    )
    parser.add_argument(
        "--print-register-command",
        action="store_true",
        help="Print a register command template when validation succeeds.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        payload = load_payload(args.config)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON: {exc}")

    if not is_mapping(payload):
        parser.error("the file must contain a single JSON object")

    if args.model_type is not None:
        model_type = normalize_model_type(args.model_type)
        if not model_type:
            parser.error("unsupported model type override")
    else:
        try:
            model_type = infer_model_type(payload)
        except ValidationError as exc:
            parser.error(str(exc))

    if model_type == "catalog":
        result = ValidationResult(model_type=model_type, errors=[], warnings=[])
        result.errors.append(Issue("error", "root", "this looks like a model hub catalog entry; direct custom registration JSON is expected instead"))
        return print_report(result, args.print_register_command, args.config)

    if model_type == "video" and args.model_type is None:
        # Keep video as a best-effort classification only; the custom workflow is unsupported.
        pass

    result = validate_model(payload, model_type)
    return print_report(result, args.print_register_command, args.config)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
