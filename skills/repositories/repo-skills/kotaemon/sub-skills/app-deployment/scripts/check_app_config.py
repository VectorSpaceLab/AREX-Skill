#!/usr/bin/env python3
"""Read-only Kotaemon app configuration diagnostic.

This script parses env-style key/value files and checks common deployment
pitfalls. It never imports Kotaemon, starts Gradio, downloads assets, or prints
secret values.
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path
from typing import Iterable

PLACEHOLDER_PATTERNS = [
    re.compile(r"^$"),
    re.compile(r"<[^>]+>"),
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"your[-_ ]?key", re.IGNORECASE),
    re.compile(r"YOUR_[A-Z0-9_]*KEY", re.IGNORECASE),
]

KEY_LIKE_NAMES = (
    "API_KEY",
    "CREDENTIAL",
    "CLIENT_SECRET",
    "CLIENT_ID",
    "TOKEN",
    "SECRET",
)

CORE_KEYS = [
    "OPENAI_API_KEY",
    "COHERE_API_KEY",
    "LOCAL_MODEL",
    "LOCAL_MODEL_EMBEDDINGS",
    "GRAPHRAG_API_KEY",
    "PDFJS_VERSION_DIST",
    "AUTHENTICATION_METHOD",
]

OPTIONAL_PATH_KEYS = ["PDFJS_PREBUILT_DIR", "GRADIO_TEMP_DIR"]


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            print(f"WARN env:{line_number}: ignored line without '='")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = strip_inline_comment(value.strip())
        values[key] = unquote(value.strip())
    return values


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def merged_config(env_file_values: dict[str, str]) -> dict[str, str]:
    merged = dict(env_file_values)
    for key, value in os.environ.items():
        merged.setdefault(key, value)
    return merged


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return any(pattern.search(stripped) for pattern in PLACEHOLDER_PATTERNS)


def is_key_like(key: str) -> bool:
    upper_key = key.upper()
    return any(fragment in upper_key for fragment in KEY_LIKE_NAMES)


def redact_status(value: str | None) -> str:
    if value is None:
        return "missing"
    if is_placeholder(value):
        return "placeholder-or-empty"
    return "set"


def default_pdfjs_dir(repo_root: Path, config: dict[str, str]) -> Path:
    version_dist = config.get("PDFJS_VERSION_DIST", "pdfjs-4.0.379-dist")
    configured = config.get("PDFJS_PREBUILT_DIR")
    if configured:
        return Path(configured).expanduser()
    return repo_root / "libs" / "ktem" / "ktem" / "assets" / "prebuilt" / version_dist


def path_mode(path: Path) -> str:
    try:
        mode = path.stat().st_mode
    except OSError:
        return "unknown"
    bits = []
    for flag, label in [
        (stat.S_IRUSR, "owner-read"),
        (stat.S_IWUSR, "owner-write"),
        (stat.S_IXUSR, "owner-exec"),
    ]:
        if mode & flag:
            bits.append(label)
    return ",".join(bits) if bits else "no-owner-bits"


def check_env(path: Path, file_values: dict[str, str], config: dict[str, str]) -> int:
    issues = 0
    print("== Env file ==")
    if path.exists():
        print(f"OK env file found: {path}")
    else:
        print(f"WARN env file not found: {path}")
        issues += 1

    print("\n== Core variables ==")
    for key in CORE_KEYS:
        value = config.get(key)
        status = redact_status(value)
        prefix = "OK" if status == "set" or key in {"AUTHENTICATION_METHOD"} else "WARN"
        if prefix == "WARN":
            issues += 1
        origin = "env-file" if key in file_values else "process-env" if key in os.environ else "default/missing"
        print(f"{prefix} {key}: {status} ({origin})")

    print("\n== Secret-like values ==")
    secret_keys = sorted(key for key in config if is_key_like(key))
    if not secret_keys:
        print("OK no secret-like keys detected")
    for key in secret_keys:
        status = redact_status(config.get(key))
        prefix = "WARN" if status != "set" else "OK"
        if prefix == "WARN":
            issues += 1
        print(f"{prefix} {key}: {status}")

    return issues


def check_urls(config: dict[str, str], docker_context: bool) -> int:
    issues = 0
    print("\n== Local provider URLs ==")
    url_keys = [key for key in config if key.endswith("URL") or key.endswith("BASE") or key.endswith("ENDPOINT")]
    inspected = False
    for key in sorted(url_keys):
        value = config.get(key, "")
        if "localhost" not in value and "127.0.0.1" not in value:
            continue
        inspected = True
        if docker_context:
            print(f"WARN {key}: localhost-style URL may point inside the container")
            issues += 1
        else:
            print(f"INFO {key}: localhost-style URL; OK for same-host local services")
    if not inspected:
        print("OK no localhost-style provider URLs detected")
    return issues


def check_paths(repo_root: Path, config: dict[str, str]) -> int:
    issues = 0
    print("\n== Paths ==")

    for key in OPTIONAL_PATH_KEYS:
        if key not in config:
            continue
        path = Path(config[key]).expanduser()
        prefix = "OK" if path.exists() else "WARN"
        if prefix == "WARN":
            issues += 1
        print(f"{prefix} {key}: {'exists' if path.exists() else 'missing'} ({path})")

    app_data = repo_root / "ktem_app_data"
    if app_data.exists():
        print(f"OK default app data dir exists: {app_data} [{path_mode(app_data)}]")
        for relative in ["user_data", "user_data/files", "user_data/vectorstore", "gradio_tmp"]:
            child = app_data / relative
            status = "exists" if child.exists() else "missing"
            prefix = "OK" if child.exists() else "INFO"
            print(f"{prefix} {relative}: {status}")
    else:
        print(f"INFO default app data dir not present yet: {app_data}")

    pdfjs_dir = default_pdfjs_dir(repo_root, config)
    if pdfjs_dir.exists():
        print(f"OK PDF.js directory exists: {pdfjs_dir}")
        expected = [pdfjs_dir / "web", pdfjs_dir / "build", pdfjs_dir / "web" / "viewer.html"]
        if any(path.exists() for path in expected):
            print("OK PDF.js directory resembles a distribution")
        else:
            print("WARN PDF.js directory exists but expected web/build assets were not found")
            issues += 1
    else:
        print(f"WARN PDF.js directory missing: {pdfjs_dir}")
        issues += 1

    return issues


def check_repo_shape(repo_root: Path) -> int:
    issues = 0
    print("\n== Repo shape ==")
    expected_files = ["app.py", "flowsettings.py", ".env.example"]
    for relative in expected_files:
        path = repo_root / relative
        prefix = "OK" if path.exists() else "WARN"
        if prefix == "WARN":
            issues += 1
        print(f"{prefix} {relative}: {'found' if path.exists() else 'missing'}")

    for relative in ["libs/kotaemon", "libs/ktem"]:
        path = repo_root / relative
        prefix = "OK" if path.exists() else "WARN"
        if prefix == "WARN":
            issues += 1
        print(f"{prefix} {relative}: {'found' if path.exists() else 'missing'}")
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Kotaemon app config diagnostic. Never starts the server."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env-style file to inspect (default: .env).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Kotaemon checkout/deployment root for path checks (default: current directory).",
    )
    parser.add_argument(
        "--docker-context",
        action="store_true",
        help="Warn when localhost-style provider URLs would be used from a container.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env_file = args.env_file.expanduser().resolve()
    repo_root = args.repo_root.expanduser().resolve()

    file_values = parse_env_file(env_file)
    config = merged_config(file_values)

    issues = 0
    issues += check_env(env_file, file_values, config)
    issues += check_urls(config, args.docker_context)
    issues += check_paths(repo_root, config)
    issues += check_repo_shape(repo_root)

    print("\n== Summary ==")
    if issues:
        print(f"WARN completed with {issues} warning(s). No files were modified and no server was started.")
        return 1
    print("OK no warnings detected. No files were modified and no server was started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
