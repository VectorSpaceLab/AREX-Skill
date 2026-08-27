#!/usr/bin/env python3
"""Safely inspect CrewAI file inputs and provider constraints.

This diagnostic adapts CrewAI's internal file-input smoke-runner pattern into a
self-contained preflight tool. By default it does not call LLMs, upload files,
read remote URLs, use credentials, or mutate provider state.
"""

from __future__ import annotations

import argparse
import base64
import binascii
from dataclasses import asdict, dataclass, field
import json
import mimetypes
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import unquote_to_bytes


DATA_URI_RE = re.compile(r"^data:([^;,]+)?((?:;[^,]*)?),(.*)$", re.DOTALL)
BASE64_MARKER_RE = re.compile(r"(?:^|;)base64(?:;|$)", re.IGNORECASE)


@dataclass
class InputSpec:
    """A parsed user input before conversion to crewai_files objects."""

    name: str
    source_type: str
    value: str
    filename: str | None = None
    kind: str = "auto"


@dataclass
class CheckResult:
    """Serializable summary for one inspected file input."""

    name: str
    ok: bool
    class_name: str | None = None
    source_kind: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    provider_supported: bool | None = None
    delivery: str | None = None
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def parse_name_value(raw: str, flag_name: str) -> tuple[str, str]:
    """Parse NAME=VALUE arguments."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"{flag_name} expects NAME=VALUE")
    name, value = raw.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"{flag_name} name cannot be empty")
    if not value:
        raise argparse.ArgumentTypeError(f"{flag_name} value cannot be empty")
    return name, value


def build_map(items: list[str] | None, flag_name: str) -> dict[str, str]:
    """Build a dictionary from repeated NAME=VALUE options."""
    result: dict[str, str] = {}
    for item in items or []:
        name, value = parse_name_value(item, flag_name)
        result[name] = value
    return result


def decode_base64_payload(value: str) -> bytes:
    """Decode a base64 payload with forgiving padding."""
    compact = "".join(value.split())
    padded = compact + "=" * (-len(compact) % 4)
    try:
        return base64.b64decode(padded, validate=True)
    except binascii.Error as exc:
        raise ValueError(f"invalid base64 payload: {exc}") from exc


def decode_data_uri(value: str) -> tuple[bytes, str | None]:
    """Decode a data URI and return bytes plus MIME type."""
    match = DATA_URI_RE.match(value)
    if match is None:
        raise ValueError("invalid data URI")
    mime_type = match.group(1) or None
    metadata = match.group(2) or ""
    payload = match.group(3)
    if BASE64_MARKER_RE.search(metadata):
        return decode_base64_payload(payload), mime_type
    return unquote_to_bytes(payload), mime_type


def filename_for_mime(name: str, mime_type: str | None) -> str:
    """Create a stable diagnostic filename for byte inputs."""
    extension = mimetypes.guess_extension(mime_type or "") or ".bin"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "file"
    return f"{safe_name}{extension}"


def load_crewai_files() -> dict[str, Any]:
    """Import crewai_files lazily with a concise error if unavailable."""
    try:
        from crewai_files import (  # type: ignore[import-not-found]
            AudioFile,
            File,
            FileBytes,
            FilePath,
            FileUrl,
            ImageFile,
            PDFFile,
            TextFile,
            VideoFile,
            get_constraints_for_provider,
            get_supported_content_types,
            wrap_file_source,
        )
        from crewai_files.core.sources import FileBytes as FileBytesSource
        from crewai_files.core.sources import FilePath as FilePathSource
        from crewai_files.core.sources import FileUrl as FileUrlSource
        from crewai_files.processing.constraints import uses_openai_responses_api
    except Exception as exc:  # pragma: no cover - depends on runtime env
        raise SystemExit(
            "crewai-files is not importable. Install CrewAI file-processing support "
            "before using this checker. Original import error: " + repr(exc)
        ) from exc

    return {
        "AudioFile": AudioFile,
        "File": File,
        "FileBytes": FileBytes,
        "FilePath": FilePath,
        "FileUrl": FileUrl,
        "ImageFile": ImageFile,
        "PDFFile": PDFFile,
        "TextFile": TextFile,
        "VideoFile": VideoFile,
        "get_constraints_for_provider": get_constraints_for_provider,
        "get_supported_content_types": get_supported_content_types,
        "wrap_file_source": wrap_file_source,
        "FileBytesSource": FileBytesSource,
        "FilePathSource": FilePathSource,
        "FileUrlSource": FileUrlSource,
        "uses_openai_responses_api": uses_openai_responses_api,
    }


def make_specs(args: argparse.Namespace) -> list[InputSpec]:
    """Create ordered input specs from CLI arguments."""
    filenames = build_map(args.filename, "--filename")
    kinds = build_map(args.kind, "--kind")
    specs: list[InputSpec] = []

    for item in args.file or []:
        name, value = parse_name_value(item, "--file")
        specs.append(
            InputSpec(
                name=name,
                source_type="file",
                value=value,
                filename=filenames.get(name),
                kind=kinds.get(name, "auto"),
            )
        )
    for item in args.base64 or []:
        name, value = parse_name_value(item, "--base64")
        specs.append(
            InputSpec(
                name=name,
                source_type="base64",
                value=value,
                filename=filenames.get(name),
                kind=kinds.get(name, "auto"),
            )
        )
    for item in args.data_uri or []:
        name, value = parse_name_value(item, "--data-uri")
        specs.append(
            InputSpec(
                name=name,
                source_type="data-uri",
                value=value,
                filename=filenames.get(name),
                kind=kinds.get(name, "auto"),
            )
        )
    for item in args.text or []:
        name, value = parse_name_value(item, "--text")
        specs.append(
            InputSpec(
                name=name,
                source_type="text",
                value=value,
                filename=filenames.get(name) or f"{name}.txt",
                kind=kinds.get(name, "text"),
            )
        )

    invalid_kinds = {spec.kind for spec in specs} - {
        "auto",
        "file",
        "image",
        "pdf",
        "text",
        "audio",
        "video",
    }
    if invalid_kinds:
        raise SystemExit(f"Invalid --kind values: {', '.join(sorted(invalid_kinds))}")
    return specs


def make_source(spec: InputSpec, api: dict[str, Any]) -> Any:
    """Convert an InputSpec into a crewai_files source object."""
    if spec.source_type == "file":
        value = spec.value
        if value.startswith(("http://", "https://")):
            return api["FileUrlSource"](url=value, filename=spec.filename)
        return api["FilePathSource"](path=Path(value).expanduser())

    if spec.source_type == "base64":
        data = decode_base64_payload(spec.value)
        return api["FileBytesSource"](
            data=data,
            filename=spec.filename or f"{spec.name}.bin",
        )

    if spec.source_type == "data-uri":
        data, mime_type = decode_data_uri(spec.value)
        return api["FileBytesSource"](
            data=data,
            filename=spec.filename or filename_for_mime(spec.name, mime_type),
        )

    if spec.source_type == "text":
        return api["FileBytesSource"](
            data=spec.value.encode(),
            filename=spec.filename or f"{spec.name}.txt",
        )

    raise ValueError(f"unsupported source type: {spec.source_type}")


def wrap_file(source: Any, kind: str, api: dict[str, Any]) -> Any:
    """Wrap a source into a typed crewai_files file object."""
    if kind == "auto":
        return api["wrap_file_source"](source)
    mapping = {
        "file": api["File"],
        "image": api["ImageFile"],
        "pdf": api["PDFFile"],
        "text": api["TextFile"],
        "audio": api["AudioFile"],
        "video": api["VideoFile"],
    }
    return mapping[kind](source=source)


def source_kind(source: Any, api: dict[str, Any]) -> str:
    """Return a stable source kind label."""
    if isinstance(source, api["FileUrlSource"]):
        return "url"
    if isinstance(source, api["FilePathSource"]):
        return "path"
    if isinstance(source, api["FileBytesSource"]):
        return "bytes"
    return type(source).__name__


def size_for_source(source: Any, file_input: Any, api: dict[str, Any]) -> int | None:
    """Determine size without reading remote URLs."""
    if isinstance(source, api["FilePathSource"]):
        return int(source.path.stat().st_size)
    if isinstance(source, api["FileBytesSource"]):
        return len(source.data)
    if isinstance(source, api["FileUrlSource"]):
        return None
    try:
        return len(file_input.read())
    except Exception:
        return None


def provider_lookup_key(provider: str, api_variant: str | None, api: dict[str, Any]) -> str:
    """Return the provider key used for constraints."""
    if api["uses_openai_responses_api"](provider, api_variant):
        return "openai_responses"
    return provider


def type_constraint(content_type: str, constraints: Any) -> Any | None:
    """Get the matching type-specific constraint object."""
    if content_type.startswith("image/"):
        return constraints.image
    if content_type == "application/pdf":
        return constraints.pdf
    if content_type.startswith("audio/"):
        return constraints.audio
    if content_type.startswith("video/"):
        return constraints.video
    if content_type.startswith("text/") or content_type in {
        "application/json",
        "application/xml",
        "application/x-yaml",
        "text/xml",
        "text/yaml",
        "text/html",
    }:
        return constraints.text
    return None


def supported_by_constraints(content_type: str, constraints: Any | None) -> bool:
    """Return whether constraints support this content type."""
    if constraints is None:
        return False
    constraint = type_constraint(content_type, constraints)
    if constraint is None:
        return False
    formats = getattr(constraint, "supported_formats", None)
    if formats is not None and content_type not in formats:
        return False
    return True


def validate_basic(
    file_input: Any,
    size_bytes: int | None,
    constraints: Any | None,
) -> list[str]:
    """Validate provider support and basic size/format constraints safely."""
    if constraints is None:
        return ["unknown provider constraints; validation disabled"]

    content_type = file_input.content_type
    constraint = type_constraint(content_type, constraints)
    if constraint is None:
        return [f"provider '{constraints.name}' does not support {content_type}"]

    errors: list[str] = []
    formats = getattr(constraint, "supported_formats", None)
    if formats is not None and content_type not in formats:
        errors.append(
            f"format {content_type!r} is not supported; supported: {', '.join(formats)}"
        )

    max_size = getattr(constraint, "max_size_bytes", None)
    if max_size is None and content_type.startswith("text/"):
        max_size = getattr(constraints, "general_max_size_bytes", None)
    if size_bytes is not None and max_size is not None and size_bytes > max_size:
        errors.append(f"size {size_bytes} exceeds max {max_size}")

    return errors


def predict_delivery(
    file_input: Any,
    source: Any,
    provider: str,
    constraints: Any | None,
    size_bytes: int | None,
    prefer_upload: bool,
    api: dict[str, Any],
) -> tuple[str, list[str]]:
    """Predict resolver delivery without doing network or upload work."""
    notes: list[str] = []
    provider_lower = provider.lower()

    if isinstance(source, api["FileUrlSource"]):
        if (
            constraints is not None
            and constraints.supports_url_references
            and "bedrock" not in provider_lower
            and "aws" not in provider_lower
        ):
            return "url-reference", notes
        return "skipped-url-fetch", [
            "remote URL would need content fetching or provider-specific storage for this provider"
        ]

    if constraints is not None and constraints.supports_file_upload:
        constraint = type_constraint(file_input.content_type, constraints)
        type_max = getattr(constraint, "max_size_bytes", None)
        threshold = constraints.file_upload_threshold_bytes
        if prefer_upload:
            return "upload-candidate-skipped", ["prefer_upload requested; upload not attempted"]
        if size_bytes is not None and type_max is not None and size_bytes > type_max:
            return "upload-candidate-skipped", [
                "file exceeds type inline limit; upload not attempted"
            ]
        if size_bytes is not None and threshold is not None and size_bytes > threshold:
            return "upload-candidate-skipped", [
                "file exceeds provider upload threshold; upload not attempted"
            ]

    if "bedrock" in provider_lower or "aws" in provider_lower:
        return "inline-bytes", notes
    return "inline-base64", notes


def inspect_one(
    spec: InputSpec,
    args: argparse.Namespace,
    api: dict[str, Any],
) -> CheckResult:
    """Inspect one input and return a structured result."""
    result = CheckResult(name=spec.name, ok=False)
    try:
        source = make_source(spec, api)
        file_input = wrap_file(source, spec.kind, api)
        constraints_key = provider_lookup_key(args.provider, args.api, api)
        constraints = api["get_constraints_for_provider"](constraints_key)
        size_bytes = size_for_source(source, file_input, api)
        delivery, delivery_notes = predict_delivery(
            file_input=file_input,
            source=source,
            provider=constraints_key,
            constraints=constraints,
            size_bytes=size_bytes,
            prefer_upload=args.prefer_upload,
            api=api,
        )

        result.class_name = type(file_input).__name__
        result.source_kind = source_kind(source, api)
        result.filename = file_input.filename
        result.content_type = file_input.content_type
        result.size_bytes = size_bytes
        result.provider_supported = supported_by_constraints(
            file_input.content_type, constraints
        )
        result.delivery = delivery
        result.validation_errors = validate_basic(file_input, size_bytes, constraints)
        result.notes.extend(delivery_notes)

        supported_prefixes = api["get_supported_content_types"](args.provider, args.api)
        if supported_prefixes:
            result.notes.append(
                "provider supported prefixes: " + ", ".join(supported_prefixes)
            )

        if result.source_kind == "url":
            result.warnings.append(
                "URL content was not fetched; size/page/duration validation is skipped"
            )
        if result.content_type == "application/octet-stream":
            result.warnings.append(
                "MIME detection fell back to application/octet-stream; add a filename or install python-magic"
            )
        if spec.source_type == "base64" and spec.filename is None:
            result.warnings.append(
                "base64 input has no filename; MIME detection may be too generic"
            )
        if delivery == "upload-candidate-skipped":
            result.warnings.append(
                "provider upload was not attempted by this safe checker"
            )
        if delivery == "skipped-url-fetch":
            result.warnings.append(
                "network fetch is disabled; use a local file for strict validation"
            )

        result.ok = not result.validation_errors and result.provider_supported is True
        return result
    except Exception as exc:
        result.validation_errors.append(str(exc))
        return result


def print_text(results: list[CheckResult]) -> None:
    """Print a compact human-readable report."""
    for item in results:
        status = "OK" if item.ok else "CHECK"
        print(f"[{status}] {item.name}")
        print(f"  class: {item.class_name or '-'}")
        print(f"  source: {item.source_kind or '-'}")
        print(f"  filename: {item.filename or '-'}")
        print(f"  content_type: {item.content_type or '-'}")
        print(f"  size_bytes: {item.size_bytes if item.size_bytes is not None else 'unknown'}")
        print(f"  provider_supported: {item.provider_supported}")
        print(f"  predicted_delivery: {item.delivery or '-'}")
        for message in item.validation_errors:
            print(f"  error: {message}")
        for message in item.warnings:
            print(f"  warning: {message}")
        for message in item.notes:
            print(f"  note: {message}")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect CrewAI file inputs, MIME detection, provider support, "
            "and non-upload delivery decisions."
        )
    )
    parser.add_argument(
        "--provider",
        default="openai",
        help="Provider/model name to check, such as openai, openai/gpt-4o-mini, anthropic, gemini, bedrock, or azure.",
    )
    parser.add_argument(
        "--api",
        default=None,
        help="Optional API variant, such as 'responses' for OpenAI Responses API.",
    )
    parser.add_argument(
        "--file",
        action="append",
        metavar="NAME=PATH_OR_URL",
        help="Local path or HTTP(S) URL input; URL metadata is checked without fetching. Repeat for multiple files.",
    )
    parser.add_argument(
        "--base64",
        action="append",
        metavar="NAME=BASE64",
        help="Base64 payload to decode into FileBytes. Use --filename NAME=FILE for better MIME detection.",
    )
    parser.add_argument(
        "--data-uri",
        action="append",
        metavar="NAME=DATA_URI",
        help="Data URI input such as data:image/png;base64,... . Repeat as needed.",
    )
    parser.add_argument(
        "--text",
        action="append",
        metavar="NAME=TEXT",
        help="Small inline text fixture encoded as UTF-8 bytes.",
    )
    parser.add_argument(
        "--filename",
        action="append",
        metavar="NAME=FILENAME",
        help="Filename hint for --base64, --data-uri, --text, or URL inputs.",
    )
    parser.add_argument(
        "--kind",
        action="append",
        metavar="NAME=KIND",
        help="Override wrapper kind: auto, file, image, pdf, text, audio, or video.",
    )
    parser.add_argument(
        "--prefer-upload",
        action="store_true",
        help="Predict prefer_upload behavior, but still do not upload.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Exit with status 1 when any input has validation errors or unsupported provider constraints.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the checker."""
    parser = build_parser()
    args = parser.parse_args(argv)
    specs = make_specs(args)
    if not specs:
        parser.error("provide at least one --file, --base64, --data-uri, or --text input")

    api = load_crewai_files()
    results = [inspect_one(spec, args, api) for spec in specs]

    if args.json:
        print(json.dumps([asdict(item) for item in results], indent=2, sort_keys=True))
    else:
        print_text(results)

    if args.strict_exit and any(not item.ok for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
