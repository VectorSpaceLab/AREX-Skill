#!/usr/bin/env python3
"""Dry-run parser for PINTO_model_zoo download shell scripts.

The helper reads shell text and reports likely network/download behavior. It
never executes shell commands, never imports non-stdlib packages, and never
opens network connections.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.parse import parse_qs, unquote, urlparse

NETWORK_COMMANDS = {
    "curl",
    "wget",
    "aria2c",
    "gdown",
    "git",
    "gsutil",
    "aws",
    "python",
    "python3",
}
ARCHIVE_COMMANDS = {"tar", "unzip", "gunzip", "gzip", "7z", "unrar", "xz"}
MUTATING_COMMANDS = {"rm", "mv", "cp", "mkdir", "ln", "chmod", "chown"}
URL_RE = re.compile(r"https?://[^\s\"'`<>]+")
DRIVE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{15,}$")
DRIVE_FILE_RE = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?[^\s\"'`<>]*id=)([A-Za-z0-9_-]{15,})")
VAR_ASSIGN_RE = re.compile(
    r"(?m)^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([\"']?)([^\"'\s;#]+)\2"
)
OUTPUT_FLAG_RE = re.compile(r"(?:^|\s)(?:-o|--output)\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s;]+))")


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item is None:
            continue
        item = str(item).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc}") from exc


def find_scripts(target: Path, recursive: bool) -> List[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise SystemExit(f"error: target is not a file or directory: {target}")
    pattern = "**/download*.sh" if recursive else "download*.sh"
    scripts = sorted(p for p in target.glob(pattern) if p.is_file())
    if not scripts:
        mode = "recursively " if recursive else ""
        raise SystemExit(f"error: no {mode}download*.sh files found in {target}")
    return scripts


def logical_lines(text: str) -> List[str]:
    """Return shell-like logical lines by joining backslash continuations."""
    lines: List[str] = []
    current = ""
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            current += stripped[:-1] + " "
            continue
        lines.append(current + raw)
        current = ""
    if current:
        lines.append(current)
    return lines


def shell_tokens(line: str) -> List[str]:
    try:
        return shlex.split(line, comments=False, posix=True)
    except ValueError:
        return []


def command_name(token: str) -> str:
    return Path(token).name.lower()


def collect_assignments(text: str) -> Dict[str, str]:
    assignments: Dict[str, str] = {}
    for name, _quote, value in VAR_ASSIGN_RE.findall(text):
        assignments[name] = value.strip()
    return assignments


def resolve_shell_ref(value: str, assignments: Dict[str, str]) -> str:
    value = value.strip()
    if value.startswith("${") and value.endswith("}"):
        return assignments.get(value[2:-1], value)
    if value.startswith("$") and len(value) > 1:
        return assignments.get(value[1:], value)
    return value


def looks_like_drive_id(value: str) -> bool:
    if not DRIVE_ID_RE.match(value):
        return False
    # Avoid treating obvious archive or URL strings as IDs.
    lowered = value.lower()
    if "." in value or "/" in value or lowered.endswith(("tar", "gz", "zip", "onnx", "tflite")):
        return False
    return True


def extract_urls(text: str) -> List[str]:
    urls = []
    for match in URL_RE.findall(text):
        urls.append(html.unescape(match).rstrip(").,;"))
    return unique(urls)


def extract_drive_ids(text: str, assignments: Dict[str, str], urls: Sequence[str]) -> List[str]:
    candidates: List[str] = []

    for name, value in assignments.items():
        lowered = name.lower()
        if "id" in lowered or "file" in lowered or "drive" in lowered:
            resolved = resolve_shell_ref(value, assignments)
            if looks_like_drive_id(resolved):
                candidates.append(resolved)

    for url in urls:
        unescaped = unquote(url)
        direct_match = DRIVE_FILE_RE.search(unescaped)
        if direct_match:
            candidates.append(direct_match.group(1))
        parsed = urlparse(unescaped)
        if "drive.google.com" in parsed.netloc:
            params = parse_qs(parsed.query)
            for raw_id in params.get("id", []):
                resolved = resolve_shell_ref(raw_id, assignments)
                if looks_like_drive_id(resolved):
                    candidates.append(resolved)

    # Common shell snippets include id=${fileid}; the assignment is the useful ID.
    for raw in re.findall(r"(?:fileid|file_id|gdrive_id|google_drive_id)\s*=\s*[\"']?([A-Za-z0-9_-]{15,})", text, re.I):
        if looks_like_drive_id(raw):
            candidates.append(raw)

    return unique(candidates)


def extract_output_files(lines: Sequence[str]) -> List[str]:
    outputs: List[str] = []
    for line in lines:
        tokens = shell_tokens(line)
        if tokens:
            for index, token in enumerate(tokens):
                if token in {"-o", "--output", "-O"} and index + 1 < len(tokens):
                    outputs.append(tokens[index + 1])
                elif token.startswith("--output="):
                    outputs.append(token.split("=", 1)[1])
                elif token.startswith("-o") and len(token) > 2 and not token.startswith("--"):
                    outputs.append(token[2:])
        else:
            for groups in OUTPUT_FLAG_RE.findall(line):
                outputs.extend(value for value in groups if value)
    return unique(outputs)


def detect_commands(lines: Sequence[str]) -> Tuple[List[str], List[str], List[str]]:
    network: List[str] = []
    archive: List[str] = []
    mutating: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = shell_tokens(stripped)
        if not tokens:
            continue
        # Handle simple env-prefix commands such as VAR=x curl ...
        command = ""
        for token in tokens:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                continue
            command = command_name(token)
            break
        if not command:
            continue
        if command in NETWORK_COMMANDS:
            network.append(command)
        if command in ARCHIVE_COMMANDS:
            archive.append(command)
        if command in MUTATING_COMMANDS:
            mutating.append(command)
    return unique(network), unique(archive), unique(mutating)


def inspect_script(path: Path) -> Dict[str, object]:
    text = read_text(path)
    lines = logical_lines(text)
    assignments = collect_assignments(text)
    urls = extract_urls(text)
    google_drive_ids = extract_drive_ids(text, assignments, urls)
    output_files = extract_output_files(lines)
    network_commands, archive_commands, mutating_commands = detect_commands(lines)

    contains_google_drive = any("drive.google.com" in urlparse(u).netloc for u in urls) or bool(google_drive_ids)
    contains_network = bool(network_commands or urls)
    cookie_or_confirmation = bool(
        re.search(r"confirm=|download_warning|cookie|--cookie|-c\s+\.?/?cookie|-b\s+\.?/?cookie", text, re.I)
    )
    archive_or_cleanup = unique(archive_commands + mutating_commands)

    warnings: List[str] = [
        "dry-run only: this helper did not execute shell or network commands",
    ]
    if contains_network:
        warnings.append("network approval required before running this script")
    else:
        warnings.append("no obvious network command found, but shell side effects still require review")
    if contains_google_drive:
        warnings.append("Google Drive links can require confirmation tokens, cookies, credentials, or quota")
    if cookie_or_confirmation:
        warnings.append("cookie/confirmation flow detected; protect cookie files and watch for HTML error downloads")
    if archive_commands:
        warnings.append("archive extraction detected; verify free space and inspect overwrite risk")
    if mutating_commands:
        warnings.append("file mutation/cleanup commands detected; review targets before execution")
    if not output_files:
        warnings.append("no explicit -o/--output filename found; manual review needed to know all writes")

    return {
        "script": str(path),
        "google_drive_file_ids": google_drive_ids,
        "urls": urls,
        "output_files": output_files,
        "network_commands": network_commands,
        "contains_network_command": contains_network,
        "contains_google_drive": contains_google_drive,
        "cookie_or_confirmation_flow": cookie_or_confirmation,
        "archive_or_cleanup_signals": archive_or_cleanup,
        "warnings": unique(warnings),
    }


def print_text_report(results: Sequence[Dict[str, object]]) -> None:
    for index, result in enumerate(results):
        if index:
            print()
        print(f"script: {result['script']}")
        print_list("likely Google Drive file IDs", result["google_drive_file_ids"])
        print_list("explicit output files from -o/--output", result["output_files"])
        print_list("URLs", result["urls"])
        print_list("network commands", result["network_commands"])
        print(f"contains Google Drive: {yes_no(result['contains_google_drive'])}")
        print(f"cookie/confirmation flow: {yes_no(result['cookie_or_confirmation_flow'])}")
        print_list("archive or cleanup signals", result["archive_or_cleanup_signals"])
        print_list("warnings", result["warnings"])


def print_list(label: str, values: object) -> None:
    seq = list(values) if isinstance(values, list) else []
    print(f"{label}:")
    if not seq:
        print("  - (none found)")
        return
    for value in seq:
        print(f"  - {value}")


def yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run parse a PINTO_model_zoo download shell script or a directory "
            "containing download*.sh files. No commands or network requests are executed."
        )
    )
    parser.add_argument(
        "target",
        type=Path,
        help="download*.sh file or directory containing download*.sh files",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="when target is a directory, inspect download*.sh files recursively",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a JSON array instead of a text report",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    scripts = find_scripts(args.target, args.recursive)
    results = [inspect_script(script) for script in scripts]
    if args.json:
        json.dump(results, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_text_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
