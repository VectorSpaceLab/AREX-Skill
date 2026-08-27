#!/usr/bin/env python3
"""Statically audit JSON tool requests and executable-looking arguments.

This checker never imports Mellea, starts a process, opens a network connection,
executes JSON, expands a shell, or prints input values. It is an advisory
preflight, not an approval mechanism. Exit status is 0 when no error-level
finding is emitted, 1 when a request needs rejection/review, and 2 for invalid
CLI/input usage.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]{0,127}$")
MAX_DEFAULT_BYTES = 1_048_576
SCHEMA_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
SHELL_KEYS = {
    "command",
    "cmd",
    "shell",
    "shell_command",
    "script",
    "bash",
    "sh",
    "terminal",
}
CODE_KEYS = {"code", "source", "python"}
NETWORK_COMMANDS = {"curl", "wget", "ssh", "scp", "sftp", "nc", "ncat", "telnet"}
DANGEROUS_COMMANDS = {
    "sudo",
    "su",
    "doas",
    "passwd",
    "visudo",
    "chsh",
    "chfn",
    "useradd",
    "userdel",
    "usermod",
    "groupadd",
    "groupdel",
    "groupmod",
}
SHELL_NAMES = {"bash", "sh", "zsh", "ksh", "tcsh"}
SHELL_OPERATORS = {"|", ">", ">>", "&&", "||", ";", "&", "<", "<<", "|&"}
PATH_PREFIXES = ("/etc", "/root", "/proc", "/sys", "/boot", "/var/log", "/var/www")
SECRET_WORDS = (
    "authorization",
    "bearer ",
    "api_key",
    "apikey",
    "secret",
    "password",
    "private_key",
)


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting ambiguous duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate JSON object key")
        result[key] = value
    return result


@dataclass(frozen=True)
class Finding:
    """One redacted static finding."""

    level: str
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        """Return a value-only JSON representation of the finding."""
        return {
            "level": self.level,
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


def add(
    findings: list[Finding], level: str, code: str, location: str, message: str
) -> None:
    """Append a finding without including the audited value."""
    findings.append(Finding(level, code, location, message))


def _looks_like_schema(obj: dict[str, Any]) -> bool:
    function = obj.get("function")
    return (
        obj.get("type") == "function"
        and isinstance(function, dict)
        and "parameters" in function
    )


def _looks_like_call(obj: dict[str, Any]) -> bool:
    return isinstance(obj.get("name"), str) and any(
        key in obj for key in ("arguments", "args", "parameters")
    )


def _parse_arguments(
    value: Any, location: str, findings: list[Finding]
) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            add(
                findings,
                "error",
                "arguments-not-json",
                location,
                "Arguments string is not valid JSON.",
            )
            return None
    if not isinstance(value, dict):
        add(
            findings,
            "error",
            "arguments-not-object",
            location,
            "Tool arguments must be a JSON object.",
        )
        return None
    return value


def _audit_schema(schema: Any, location: str, findings: list[Finding]) -> None:
    if not isinstance(schema, dict):
        add(
            findings,
            "error",
            "schema-not-object",
            location,
            "Tool parameters schema must be an object.",
        )
        return
    if schema.get("type") not in (None, "object"):
        add(
            findings,
            "error",
            "schema-not-object-type",
            location,
            "Tool parameters must have type object.",
        )
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        add(
            findings,
            "error",
            "properties-not-object",
            location,
            "Schema properties must be an object.",
        )
        properties = {}
    required = schema.get("required", [])
    if required is not None and not isinstance(required, list):
        add(
            findings,
            "error",
            "required-not-list",
            location,
            "Schema required must be a list.",
        )
        required = []
    for name in required or []:
        if not isinstance(name, str) or name not in properties:
            add(
                findings,
                "error",
                "required-unknown",
                location,
                "Schema required contains a name absent from properties.",
            )
    for name, property_schema in properties.items():
        _audit_schema_nodes(property_schema, f"{location}.properties.{name}", findings)
    if "additionalProperties" not in schema:
        add(
            findings,
            "warning",
            "extra-fields-unspecified",
            location,
            "Schema does not state whether extra arguments are allowed.",
        )
    if "$ref" in schema or "oneOf" in schema or "discriminator" in schema:
        add(
            findings,
            "warning",
            "complex-schema",
            location,
            "Schema uses a provider-sensitive reference/union/discriminator construct.",
        )


def _audit_schema_nodes(node: Any, location: str, findings: list[Finding]) -> None:
    if isinstance(node, dict):
        kind = node.get("type")
        if isinstance(kind, str) and "," not in kind and kind not in SCHEMA_TYPES:
            add(
                findings,
                "error",
                "unknown-schema-type",
                location,
                "Schema contains an unknown JSON type.",
            )
        if "$ref" in node or "oneOf" in node or "anyOf" in node or "allOf" in node:
            add(
                findings,
                "warning",
                "nested-schema-construct",
                location,
                "Nested schema construct may not be accepted by every tool-calling backend.",
            )
        for key, value in (
            node.get("properties", {}).items()
            if isinstance(node.get("properties"), dict)
            else []
        ):
            _audit_schema_nodes(value, f"{location}.properties.{key}", findings)
        if isinstance(node.get("items"), dict):
            _audit_schema_nodes(node["items"], f"{location}.items", findings)
        for key in ("anyOf", "oneOf", "allOf"):
            if isinstance(node.get(key), list):
                for index, value in enumerate(node[key]):
                    _audit_schema_nodes(value, f"{location}.{key}[{index}]", findings)


def _audit_shell(text: str, location: str, findings: list[Finding]) -> None:
    """Check shell-like text conservatively without invoking a shell."""
    try:
        argv = shlex.split(text, posix=True)
    except ValueError:
        add(
            findings,
            "error",
            "shell-parse",
            location,
            "Shell-like text has malformed quoting.",
        )
        return
    if not argv:
        add(
            findings,
            "warning",
            "empty-command",
            location,
            "Executable command is empty.",
        )
        return
    for operator in sorted(SHELL_OPERATORS, key=lambda item: (-len(item), item)):
        if operator in argv or operator in text:
            # A semicolon inside a quoted token is also worth review; this is a
            # static checker, so false positives are preferable to execution.
            add(
                findings,
                "error",
                "shell-operator",
                location,
                f"Shell operator {operator!r} is present.",
            )
            break
    if "$(" in text or "`" in text or "${" in text:
        add(
            findings,
            "error",
            "shell-substitution",
            location,
            "Command or variable substitution is present.",
        )
    commands = [token.rsplit("/", 1)[-1].lower() for token in argv]
    if commands[0] in DANGEROUS_COMMANDS:
        add(
            findings,
            "error",
            "dangerous-command",
            location,
            "Privilege, account, or interactive command is not admissible.",
        )
    if any(command in DANGEROUS_COMMANDS for command in commands[1:]):
        add(
            findings,
            "error",
            "nested-dangerous-command",
            location,
            "Nested dangerous command is present.",
        )
    if commands[0] in SHELL_NAMES and any(
        flag in argv for flag in ("-c", "-e", "-i", "-l", "--interactive", "--login")
    ):
        add(
            findings,
            "error",
            "shell-indirection",
            location,
            "Shell code-execution or interactive mode is present.",
        )
    if commands[0] in {"python", "python3", "perl", "ruby", "node"} and any(
        flag in argv for flag in ("-c", "-e", "-m")
    ):
        add(
            findings,
            "error",
            "interpreter-indirection",
            location,
            "Inline/interpreter module execution is present.",
        )
    if commands[0] == "rm" and any(
        flag in argv for flag in ("-r", "-R", "-rf", "-fr", "--recursive")
    ):
        add(
            findings,
            "error",
            "destructive-remove",
            location,
            "Recursive removal is present.",
        )
    if commands[0] == "git" and any(
        flag.startswith("--force") or flag in ("-f", "--hard") for flag in argv
    ):
        add(
            findings,
            "error",
            "destructive-git",
            location,
            "Force/hard Git operation is present.",
        )
    if any(command in NETWORK_COMMANDS for command in commands):
        add(
            findings,
            "warning",
            "network-command",
            location,
            "Command may contact or upload to an external system.",
        )
    if any(
        token.startswith(PATH_PREFIXES) or "../" in token or token == ".."
        for token in argv
    ):
        add(
            findings,
            "error",
            "sensitive-path",
            location,
            "Command names a protected or traversal path.",
        )
    lowered = text.lower()
    if any(word in lowered for word in SECRET_WORDS):
        add(
            findings,
            "warning",
            "credential-like-text",
            location,
            "Command contains credential-like markers; keep secrets out of requests and logs.",
        )


def _audit_values(
    value: Any, location: str, findings: list[Finding], key_hint: str = ""
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else str(key)
            key_lower = str(key).lower()
            if key_lower in SHELL_KEYS and isinstance(child, str):
                _audit_shell(child, child_location, findings)
                continue
            if key_lower in CODE_KEYS and isinstance(child, str):
                lowered = child.lower()
                if (
                    "subprocess" in lowered
                    or "os.system" in lowered
                    or "eval(" in lowered
                    or "exec(" in lowered
                ):
                    add(
                        findings,
                        "warning",
                        "code-execution-api",
                        child_location,
                        "Code contains a process or dynamic-execution API.",
                    )
                if "socket" in lowered or "requests." in lowered or "httpx." in lowered:
                    add(
                        findings,
                        "warning",
                        "code-network-api",
                        child_location,
                        "Code contains a network-capable API.",
                    )
                if any(word in lowered for word in SECRET_WORDS):
                    add(
                        findings,
                        "warning",
                        "credential-like-text",
                        child_location,
                        "Code contains credential-like markers.",
                    )
                continue
            _audit_values(child, child_location, findings, key_lower)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _audit_values(child, f"{location}[{index}]", findings, key_hint)
    elif isinstance(value, str) and key_hint in SHELL_KEYS:
        _audit_shell(value, location, findings)


def _audit_call(
    obj: dict[str, Any], location: str, findings: list[Finding], allowed: set[str]
) -> None:
    name = obj.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        add(
            findings,
            "error",
            "invalid-tool-name",
            location,
            "Tool name is missing or has an invalid shape.",
        )
        return
    if allowed and name not in allowed:
        add(
            findings,
            "error",
            "tool-not-allowed",
            location,
            "Tool is not in the supplied static allowlist.",
        )
    arg_key = next(
        (key for key in ("arguments", "args", "parameters") if key in obj), None
    )
    if arg_key is None:
        add(
            findings,
            "error",
            "missing-arguments",
            location,
            "Tool request has no arguments field.",
        )
    else:
        parsed = _parse_arguments(obj[arg_key], f"{location}.{arg_key}", findings)
        if parsed is not None and isinstance(obj[arg_key], str):
            _audit_values(parsed, f"{location}.{arg_key}", findings)


def _walk_requests(
    value: Any, location: str, findings: list[Finding], allowed: set[str]
) -> None:
    if isinstance(value, dict):
        if _looks_like_schema(value):
            function = value["function"]
            name = function.get("name")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                add(
                    findings,
                    "error",
                    "invalid-schema-name",
                    location,
                    "Function schema has an invalid name.",
                )
            _audit_schema(
                function.get("parameters", {}),
                f"{location}.function.parameters",
                findings,
            )
            return
        if _looks_like_call(value):
            _audit_call(value, location, findings, allowed)
        for key, child in value.items():
            _walk_requests(
                child, f"{location}.{key}" if location else str(key), findings, allowed
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_requests(child, f"{location}[{index}]", findings, allowed)


def _contains_tool_record(value: Any) -> bool:
    """Return whether a nested value contains a recognized call or schema."""
    if isinstance(value, dict):
        if _looks_like_call(value) or _looks_like_schema(value):
            return True
        return any(_contains_tool_record(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_tool_record(child) for child in value)
    return False


def audit(value: Any, allowed: set[str]) -> list[Finding]:
    """Audit a decoded JSON value and return redacted static findings."""
    findings: list[Finding] = []
    if not isinstance(value, (dict, list)):
        add(
            findings,
            "error",
            "root-not-object",
            "$",
            "Root JSON value must be an object or list.",
        )
        return findings
    if not _contains_tool_record(value):
        add(
            findings,
            "error",
            "no-tool-record",
            "$",
            "No recognized tool call or OpenAI-compatible function schema was found.",
        )
    _walk_requests(value, "$", findings, allowed)
    _audit_values(value, "$", findings)
    if not findings:
        add(
            findings,
            "info",
            "no-static-findings",
            "$",
            "No known static pattern was found; manual approval is still required.",
        )
    return findings


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser without reading or executing input."""
    parser = argparse.ArgumentParser(
        description="Audit JSON tool requests, schemas, and shell-like arguments without executing them."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="JSON file path, or - to read stdin (default: -).",
    )
    parser.add_argument(
        "--allowed-tool",
        action="append",
        default=[],
        help="Exact allowed tool name; repeat for multiple names.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=MAX_DEFAULT_BYTES,
        help="Maximum input bytes (default: 1048576).",
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON report.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Read bounded JSON, emit a redacted report, and return a stable status."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    try:
        if args.input == "-":
            raw = sys.stdin.buffer.read(args.max_bytes + 1)
        else:
            with open(args.input, "rb") as handle:
                raw = handle.read(args.max_bytes + 1)
        if len(raw) > args.max_bytes:
            report = {
                "status": "rejected",
                "findings": [
                    {
                        "level": "error",
                        "code": "input-too-large",
                        "location": "$",
                        "message": "Input exceeds the configured byte limit.",
                    }
                ],
            }
            print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
            return 1
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateKeyError,
    ) as exc:
        print(
            json.dumps(
                {"status": "invalid-input", "error": type(exc).__name__}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 2
    findings = audit(value, set(args.allowed_tool))
    has_error = any(item.level == "error" for item in findings)
    report = {
        "status": "review-required"
        if has_error
        else "static-check-passed-not-approved",
        "findings": [item.as_dict() for item in findings],
        "finding_counts": {
            "error": sum(item.level == "error" for item in findings),
            "warning": sum(item.level == "warning" for item in findings),
            "info": sum(item.level == "info" for item in findings),
        },
    }
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
