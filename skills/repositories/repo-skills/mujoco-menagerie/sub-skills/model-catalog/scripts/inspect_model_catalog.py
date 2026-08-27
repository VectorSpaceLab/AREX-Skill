#!/usr/bin/env python3
"""Inspect a MuJoCo Menagerie checkout and emit a compact model catalog.

This script is intentionally read-only except for explicit --json/--markdown
output files requested by the caller. It parses repository metadata with the
Python standard library only; it never imports or executes Menagerie modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict
from typing import Any

SKIP_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "assets",
    "opensource",
    "skills",
    "test",
}
DEFAULT_NO_SCENE_REQUIRED = {"realsense_d435i"}
README_TITLE_SUFFIX = re.compile(
    r"\s*(description\s*)?\(mjcf\)\s*$|\s+description\s*$", re.IGNORECASE
)
REQUIRES_MUJOCO = re.compile(
    r"requires\s+mujoco\s+([0-9]+(?:\.[0-9]+){1,2})\s+or\s+later", re.IGNORECASE
)
VERSION = re.compile(r"(?<![A-Za-z0-9_])([0-9]+(?:\.[0-9]+){1,3})(?![A-Za-z0-9_])")
MUJOCO_VERSION_LINE = re.compile(r"mujoco.*[0-9]+\.[0-9]+", re.IGNORECASE)


def _literal_dict_of_strings(node: ast.AST) -> dict[str, str]:
    if not isinstance(node, ast.Dict):
        return {}
    out: dict[str, str] = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            continue
        try:
            k = ast.literal_eval(key)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            out[str(k)] = value.value
    return out


def parse_gallery(repo_root: pathlib.Path) -> dict[str, Any]:
    """Parse generate_gallery.py without importing it."""
    gallery = repo_root / "generate_gallery.py"
    result: dict[str, Any] = {
        "model_map": {},
        "preview_overrides": {},
        "display_name_overrides": {},
        "section_labels": {},
        "model_type_order": [],
    }
    if not gallery.is_file():
        return result

    tree = ast.parse(gallery.read_text(encoding="utf-8"), filename=str(gallery))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ModelType":
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        result["model_type_order"].append(target.id)
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "DISPLAY_NAME_OVERRIDE" in names:
            result["display_name_overrides"] = _literal_dict_of_strings(node.value)
        elif "PREVIEW_OVERRIDES" in names:
            result["preview_overrides"] = _literal_dict_of_strings(node.value)
        elif "MODEL_MAP" in names and isinstance(node.value, ast.Dict):
            mapping: dict[str, str] = {}
            for key, value in zip(node.value.keys, node.value.values):
                if key is None:
                    continue
                try:
                    k = ast.literal_eval(key)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(value, ast.Attribute):
                    mapping[str(k)] = value.attr
            result["model_map"] = mapping
        elif "SECTION_LABEL" in names and isinstance(node.value, ast.Dict):
            labels: dict[str, str] = {}
            for key, value in zip(node.value.keys, node.value.values):
                if key is None:
                    continue
                if isinstance(key, ast.Attribute) and isinstance(value, ast.Constant):
                    labels[key.attr] = str(value.value)
            result["section_labels"] = labels
    return result


def parse_scene_exceptions(repo_root: pathlib.Path) -> set[str]:
    test_path = repo_root / "test" / "model_dir_test.py"
    if not test_path.is_file():
        return set(DEFAULT_NO_SCENE_REQUIRED)
    try:
        tree = ast.parse(test_path.read_text(encoding="utf-8"), filename=str(test_path))
    except SyntaxError:
        return set(DEFAULT_NO_SCENE_REQUIRED)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "_NO_SCENE_REQUIRED" for t in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            return set(DEFAULT_NO_SCENE_REQUIRED)
        if isinstance(value, (set, list, tuple)):
            return {str(item) for item in value}
    return set(DEFAULT_NO_SCENE_REQUIRED)


def detect_license(license_path: pathlib.Path) -> str | None:
    if not license_path.is_file():
        return None
    lower = license_path.read_text(encoding="utf-8", errors="replace").lower()
    if "apache license" in lower and "version 2" in lower:
        return "Apache-2.0"
    if "clear bsd" in lower:
        return "BSD-3-Clause-Clear"
    if "redistribution and use in source" in lower:
        return "BSD-3-Clause" if "neither the name" in lower else "BSD-2-Clause"
    if "permission is hereby granted, free of charge" in lower:
        return "MIT"
    return "Unknown"


def first_heading(readme: pathlib.Path) -> tuple[str | None, int | None]:
    if not readme.is_file():
        return None, None
    for lineno, line in enumerate(readme.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip(), lineno
    return None, None


def display_name(entry: str, title: str | None, display_overrides: dict[str, str]) -> str:
    if entry in display_overrides:
        return display_overrides[entry]
    if title:
        short = README_TITLE_SUFFIX.sub("", title).rstrip()
        if short:
            return short
    return entry.split("/")[-1]


def readme_versions(readme: pathlib.Path) -> tuple[str | None, list[dict[str, Any]]]:
    if not readme.is_file():
        return None, []
    min_version: str | None = None
    evidence: list[dict[str, Any]] = []
    for lineno, line in enumerate(readme.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if MUJOCO_VERSION_LINE.search(line):
            versions = VERSION.findall(line)
            evidence.append({"line": lineno, "text": line.strip(), "versions": versions})
            match = REQUIRES_MUJOCO.search(line)
            if match and min_version is None:
                min_version = match.group(1)
    return min_version, evidence


def git_commit(repo_root: pathlib.Path) -> str | None:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = proc.stdout.strip()
    return value or None


def model_dirs(repo_root: pathlib.Path) -> list[pathlib.Path]:
    dirs: list[pathlib.Path] = []
    for child in sorted(repo_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith(".") or child.name in SKIP_DIRS:
            continue
        if any(child.glob("*.xml")):
            dirs.append(child)
    return dirs


def collect_catalog(repo_root: pathlib.Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    gallery = parse_gallery(repo_root)
    no_scene_required = parse_scene_exceptions(repo_root)
    by_dir: dict[str, list[dict[str, str]]] = defaultdict(list)
    section_labels: dict[str, str] = gallery["section_labels"]

    titles: dict[str, str | None] = {}
    for directory in model_dirs(repo_root):
        title, _ = first_heading(directory / "README.md")
        titles[directory.name] = title

    for entry, category in gallery["model_map"].items():
        maker = entry.split("/")[0]
        preview = gallery["preview_overrides"].get(entry, f"{maker}/scene.xml")
        by_dir[maker].append(
            {
                "entry": entry,
                "model_stem": entry.split("/", 1)[1],
                "category": category,
                "category_label": section_labels.get(category, category.title().replace("_", " ")),
                "display_name": display_name(entry, titles.get(maker), gallery["display_name_overrides"]),
                "preview_xml": preview,
            }
        )

    models: list[dict[str, Any]] = []
    all_category_entries: Counter[str] = Counter()
    for directory in model_dirs(repo_root):
        xml_files = sorted(path.name for path in directory.glob("*.xml"))
        scene_xmls = [name for name in xml_files if name.startswith("scene")]
        mjx_xmls = [name for name in xml_files if "mjx" in name.lower()]
        non_scene_xmls = [name for name in xml_files if name not in scene_xmls]
        asset_dirs = sorted(path.name for path in directory.iterdir() if path.is_dir())
        extension_counts: Counter[str] = Counter()
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix:
                extension_counts[path.suffix.lower()] += 1
        readme = directory / "README.md"
        title, title_line = first_heading(readme)
        min_version, version_evidence = readme_versions(readme)
        entries = sorted(by_dir.get(directory.name, []), key=lambda item: item["entry"])
        categories = sorted({entry["category_label"] for entry in entries})
        category_keys = sorted({entry["category"] for entry in entries})
        for category in categories:
            all_category_entries[category] += 1
        recommended = sorted({entry["preview_xml"] for entry in entries})
        if not recommended:
            if "scene.xml" in scene_xmls:
                recommended = [f"{directory.name}/scene.xml"]
            elif scene_xmls:
                recommended = [f"{directory.name}/{scene_xmls[0]}"]
            elif xml_files:
                recommended = [f"{directory.name}/{xml_files[0]}"]
        models.append(
            {
                "dir": directory.name,
                "title": title,
                "title_line": title_line,
                "categories": categories,
                "category_keys": category_keys,
                "known_category": bool(categories),
                "gallery_entries": entries,
                "recommended_load_xmls": recommended,
                "xml_files": xml_files,
                "scene_xmls": scene_xmls,
                "mjx_xmls": mjx_xmls,
                "non_scene_xmls": non_scene_xmls,
                "scene_required": directory.name not in no_scene_required,
                "scene_exception": directory.name in no_scene_required,
                "asset_dirs": asset_dirs,
                "asset_file_extensions": dict(sorted(extension_counts.items())),
                "has_assets": bool(asset_dirs),
                "has_readme": readme.is_file(),
                "has_license": (directory / "LICENSE").is_file(),
                "license_spdx": detect_license(directory / "LICENSE"),
                "has_changelog": (directory / "CHANGELOG.md").is_file(),
                "min_mujoco_version": min_version,
                "mujoco_version_evidence": version_evidence[:4],
            }
        )

    unknown_category_dirs = [model["dir"] for model in models if not model["known_category"]]
    missing_min_version_dirs = [model["dir"] for model in models if not model["min_mujoco_version"]]
    missing_scene_dirs = [model["dir"] for model in models if model["scene_required"] and not model["scene_xmls"]]
    catalog = {
        "schemaVersion": 1,
        "repo": "mujoco_menagerie",
        "sourceCommit": git_commit(repo_root),
        "summary": {
            "modelDirectoryCount": len(models),
            "xmlFileCount": sum(len(model["xml_files"]) for model in models),
            "sceneXmlCount": sum(len(model["scene_xmls"]) for model in models),
            "mjxDirectoryCount": sum(1 for model in models if model["mjx_xmls"]),
            "mjxXmlCount": sum(len(model["mjx_xmls"]) for model in models),
            "galleryEntryCount": sum(len(model["gallery_entries"]) for model in models),
            "unknownCategoryDirs": unknown_category_dirs,
            "missingMinVersionDirs": missing_min_version_dirs,
            "sceneExceptionDirs": sorted(no_scene_required),
            "missingRequiredSceneDirs": missing_scene_dirs,
            "categoryEntryCounts": dict(sorted(all_category_entries.items())),
        },
        "categoryLabels": section_labels,
        "models": models,
    }
    return catalog


def write_json(catalog: dict[str, Any], destination: str | None) -> None:
    text = json.dumps(catalog, sort_keys=True, separators=(",", ":")) + "\n"
    if not destination or destination == "-":
        sys.stdout.write(text)
        return
    path = pathlib.Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_catalog(catalog: dict[str, Any]) -> str:
    lines: list[str] = []
    summary = catalog["summary"]
    lines.append("# MuJoCo Menagerie Model Catalog")
    lines.append("")
    lines.append(
        f"- Models: {summary['modelDirectoryCount']} directories, {summary['xmlFileCount']} top-level XML files."
    )
    lines.append(
        f"- MJX coverage: {summary['mjxDirectoryCount']} directories, {summary['mjxXmlCount']} XML files."
    )
    lines.append(f"- Scene exception directories: {', '.join(summary['sceneExceptionDirs']) or 'none'}.")
    if summary["unknownCategoryDirs"]:
        lines.append("- Unknown gallery categories: " + ", ".join(summary["unknownCategoryDirs"]) + ".")
    if summary["missingMinVersionDirs"]:
        lines.append("- Missing explicit README minimum MuJoCo version: " + ", ".join(summary["missingMinVersionDirs"]) + ".")
    lines.append("")
    lines.append("| Directory | Categories | Recommended XML | Scene XMLs | MJX XMLs | Min MuJoCo | License |")
    lines.append("|---|---|---|---|---|---|---|")
    for model in catalog["models"]:
        categories = ", ".join(model["categories"]) or "unknown"
        recommended = ", ".join(model["recommended_load_xmls"]) or "—"
        scenes = ", ".join(model["scene_xmls"]) or "—"
        mjx = ", ".join(model["mjx_xmls"]) or "—"
        min_version = model["min_mujoco_version"] or "not stated"
        license_name = model["license_spdx"] or "missing"
        lines.append(
            f"| `{model['dir']}` | {categories} | `{recommended}` | `{scenes}` | `{mjx}` | {min_version} | {license_name} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_markdown(catalog: dict[str, Any], destination: str | None) -> None:
    text = markdown_catalog(catalog)
    if not destination or destination == "-":
        sys.stdout.write(text)
        return
    path = pathlib.Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect MuJoCo Menagerie model directories without importing MuJoCo."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a MuJoCo Menagerie checkout or exported tree (default: current directory).",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const="-",
        dest="json_path",
        help="Emit JSON to stdout, or to the optional path if provided.",
    )
    parser.add_argument(
        "--markdown",
        nargs="?",
        const="-",
        dest="markdown_path",
        help="Emit Markdown to stdout, or to the optional path if provided.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = pathlib.Path(args.repo_root)
    if not repo_root.is_dir():
        print(f"error: --repo-root is not a directory: {repo_root}", file=sys.stderr)
        return 2
    catalog = collect_catalog(repo_root)
    if not args.json_path and not args.markdown_path:
        write_markdown(catalog, "-")
        return 0
    if args.json_path:
        write_json(catalog, args.json_path)
    if args.markdown_path:
        write_markdown(catalog, args.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
