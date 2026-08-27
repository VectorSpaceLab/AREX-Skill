#!/usr/bin/env python3
"""Inspect Graphify file classification and extractor availability.

This helper is intentionally read-only: it imports Graphify's classification and
extractor-dispatch logic, but it never executes user source files and never builds
a graph. It is safe to run against individual files or a bounded recursive file
list when diagnosing source-format support.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

OPTIONAL_EXTRA_MODULES = {
    "sql": "tree_sitter_sql",
    "terraform": "tree_sitter_hcl",
    "dm": "tree_sitter_dm",
    "pascal": "tree_sitter_pascal",
}

PASCAL_EXTS = {".pas", ".pp", ".dpr", ".dpk", ".lpr", ".inc"}
BYOND_SIDE_EXTS = {".dmi", ".dmm", ".dmf"}
DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "graphify-out",
}


def _import_graphify() -> tuple[Any, Any, str | None]:
    try:
        import graphify.detect as detect_mod
        import graphify.extract as extract_mod
    except Exception as exc:  # pragma: no cover - exercised by user envs
        return None, None, f"could not import graphify classification modules: {type(exc).__name__}: {exc}"
    return detect_mod, extract_mod, None


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def _file_type_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _iter_files(inputs: list[Path], *, recursive: bool, follow_symlinks: bool, max_files: int) -> tuple[list[Path], list[dict[str, Any]], bool]:
    files: list[Path] = []
    notes: list[dict[str, Any]] = []
    truncated = False

    def add_file(path: Path) -> None:
        nonlocal truncated
        if truncated:
            return
        if len(files) >= max_files:
            truncated = True
            return
        files.append(path)

    for path in inputs:
        if path.is_dir():
            if not recursive:
                notes.append({
                    "path": str(path),
                    "status": "directory_skipped",
                    "note": "pass --recursive to inspect files under this directory",
                })
                continue
            for dirpath, dirnames, filenames in os.walk(path, followlinks=follow_symlinks):
                dirnames[:] = [d for d in dirnames if d not in DEFAULT_SKIP_DIRS]
                for filename in filenames:
                    add_file(Path(dirpath) / filename)
                    if truncated:
                        break
                if truncated:
                    break
        else:
            add_file(path)
    return files, notes, truncated


def _extractor_for_path(extract_mod: Any, path: Path) -> tuple[str | None, str | None]:
    getter = getattr(extract_mod, "_get_extractor", None)
    if callable(getter):
        try:
            extractor = getter(path)
        except Exception as exc:
            return None, f"extractor lookup failed: {type(exc).__name__}: {exc}"
        if extractor is None:
            return None, None
        return getattr(extractor, "__name__", repr(extractor)), None

    dispatch = getattr(extract_mod, "_DISPATCH", {}) or {}
    extractor = dispatch.get(path.suffix) or dispatch.get(path.suffix.lower())
    if extractor is None:
        return None, None
    return getattr(extractor, "__name__", repr(extractor)), None


def inspect_path(path: Path, detect_mod: Any, extract_mod: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "suffix": path.suffix.lower(),
        "classification": None,
        "extractor": None,
        "status": "unknown",
        "missing_extra": None,
        "optional_ast_extra": None,
        "parser_module": None,
        "parser_available": None,
        "notes": [],
    }

    try:
        classification = detect_mod.classify_file(path)
        result["classification"] = _file_type_value(classification)
    except Exception as exc:
        result["status"] = "classification_error"
        result["notes"].append(f"classify_file failed: {type(exc).__name__}: {exc}")
        classification = None

    extractor_name, extractor_error = _extractor_for_path(extract_mod, path)
    result["extractor"] = extractor_name
    if extractor_error:
        result["notes"].append(extractor_error)

    suffix = result["suffix"]
    hard_extra_map = getattr(extract_mod, "_EXTRA_FOR_EXTENSION", {}) or {}
    hard_extra = hard_extra_map.get(suffix)
    if hard_extra:
        module_name = OPTIONAL_EXTRA_MODULES.get(hard_extra)
        result["missing_extra"] = None
        result["parser_module"] = module_name
        if module_name:
            available = _module_available(module_name)
            result["parser_available"] = available
            if not available:
                result["missing_extra"] = hard_extra

    if suffix in PASCAL_EXTS:
        module_name = OPTIONAL_EXTRA_MODULES["pascal"]
        result["optional_ast_extra"] = "pascal"
        result["parser_module"] = module_name
        result["parser_available"] = _module_available(module_name)
        if not result["parser_available"]:
            result["notes"].append("Pascal regex fallback is available, but graphifyy[pascal] enables the AST parser")

    if suffix in BYOND_SIDE_EXTS:
        result["notes"].append("BYOND side format: does not require tree_sitter_dm")

    if path.name.lower().endswith(".blade.php"):
        result["notes"].append("Blade template route is matched by filename before generic .php dispatch")

    if suffix == ".h" and extractor_name:
        result["notes"].append(".h route is content-sniffed: Objective-C markers first, then C++ markers, else C")
    if suffix == ".m" and extractor_name is None:
        result["notes"].append("marker-free .m is not parsed as Objective-C; MATLAB/Octave is currently not AST-extracted")
    if not suffix and result["classification"] == "code" and extractor_name is None:
        result["notes"].append("shebang is classified as code, but this interpreter has no AST extractor dispatch")

    code_exts = getattr(detect_mod, "CODE_EXTENSIONS", set()) or set()
    if result["missing_extra"]:
        result["status"] = "missing_optional_extra"
    elif result["classification"] is None:
        result["status"] = "unclassified"
    elif result["classification"] == "code" and extractor_name is None:
        result["status"] = "code_without_ast_extractor"
    elif result["classification"] == "code" and extractor_name:
        result["status"] = "extractor_available"
    elif result["classification"] != "code" and extractor_name:
        result["status"] = "non_code_classification_with_extractor_route"
    else:
        result["status"] = "non_code_input"

    if suffix in code_exts and extractor_name is None and result["classification"] == "code":
        result["notes"].append("suffix is in CODE_EXTENSIONS but no AST extractor is wired for it")

    if not result["exists"]:
        result["notes"].append("path does not exist; suffix-based facts are still useful, content-sniffed routes may be inconclusive")

    return result


def _print_text(results: list[dict[str, Any]], notes: list[dict[str, Any]], truncated: bool) -> None:
    header = ["status", "classification", "extractor", "extra", "parser", "path"]
    print("\t".join(header))
    for item in results:
        extra = item.get("missing_extra") or item.get("optional_ast_extra") or ""
        parser = ""
        if item.get("parser_module"):
            parser = f"{item['parser_module']}={'yes' if item.get('parser_available') else 'no'}"
        row = [
            str(item.get("status") or ""),
            str(item.get("classification") or ""),
            str(item.get("extractor") or ""),
            str(extra),
            parser,
            str(item.get("path") or ""),
        ]
        print("\t".join(row))
        for note in item.get("notes") or []:
            print(f"  note[{item.get('path')}]: {note}")
    for note in notes:
        print(f"note[{note.get('path')}]: {note.get('status')}: {note.get('note')}")
    if truncated:
        print("note: file list truncated at --max-files; increase the limit for a complete recursive inspection")

    counts = Counter(str(item.get("status") or "unknown") for item in results)
    if counts:
        print("summary: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Graphify file classification and extractor availability without executing source files.",
    )
    parser.add_argument("paths", nargs="+", help="File paths, or directories with --recursive")
    parser.add_argument("--recursive", action="store_true", help="Walk directories and inspect files under them")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks while walking directories")
    parser.add_argument("--max-files", type=int, default=1000, help="Maximum files to inspect during recursive walks (default: 1000)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.max_files < 1:
        print("error: --max-files must be >= 1", file=sys.stderr)
        return 2

    detect_mod, extract_mod, import_error = _import_graphify()
    if import_error:
        payload = {"ok": False, "error": import_error}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"error: {import_error}", file=sys.stderr)
        return 2

    input_paths = [Path(p) for p in args.paths]
    files, notes, truncated = _iter_files(
        input_paths,
        recursive=args.recursive,
        follow_symlinks=args.follow_symlinks,
        max_files=args.max_files,
    )
    results = [inspect_path(path, detect_mod, extract_mod) for path in files]

    if args.json:
        print(json.dumps({
            "ok": True,
            "truncated": truncated,
            "notes": notes,
            "summary": dict(Counter(str(item.get("status") or "unknown") for item in results)),
            "files": results,
        }, indent=2, sort_keys=True))
    else:
        _print_text(results, notes, truncated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
