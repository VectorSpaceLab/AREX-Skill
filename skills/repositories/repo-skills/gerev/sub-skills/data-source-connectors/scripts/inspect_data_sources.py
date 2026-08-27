#!/usr/bin/env python3
"""Read-only connector inventory for Gerev.

The helper inspects the source tree without importing the application stack.
It lists discovered connector classes, their visible methods, and the UI/API
surface that drives connector setup.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Dict, List


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def iter_python_files(root: Path):
    for path in sorted(root.glob("**/*.py")):
        if path.name != "__init__.py":
            yield path


def base_data_source_classes(app_dir: Path) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for path in iter_python_files(app_dir / "data_source" / "sources"):
        text = read_text(path)
        if "BaseDataSource" not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            inherits = any(
                isinstance(base, ast.Name) and base.id == "BaseDataSource"
                for base in node.bases
            )
            if inherits or node.name.endswith("DataSource"):
                results.append({
                    "file": str(path.relative_to(app_dir)),
                    "class": node.name,
                    "methods": sorted(methods),
                    "has_get_config_fields": "get_config_fields" in methods,
                    "has_validate_config": "validate_config" in methods,
                    "has_feed_new_documents": "_feed_new_documents" in methods,
                    "has_list_locations": "list_locations" in methods,
                    "has_prerequisites": "has_prerequisites" in methods,
                })
    return results


def ui_endpoints(app_dir: Path) -> List[str]:
    text = read_text(app_dir / "api" / "data_source.py") + "\n" + read_text(app_dir / "api" / "search.py") + "\n" + read_text(app_dir / "main.py")
    markers = ["/api/v1/data-sources/types", "/api/v1/data-sources/connected", "/api/v1/data-sources", "/clear-index", "/check-for-new-documents", "/api/v1/search", "/api/v1/status"]
    return [marker for marker in markers if marker in text]


def build_report(app_dir: Path) -> Dict[str, Any]:
    return {
        "app_dir": str(app_dir),
        "connector_classes": base_data_source_classes(app_dir),
        "ui_endpoints": ui_endpoints(app_dir),
        "source_files_present": {
            "data_source_api": (app_dir / "data_source" / "api" / "base_data_source.py").exists(),
            "data_source_context": (app_dir / "data_source" / "api" / "context.py").exists(),
            "data_source_loader": (app_dir / "data_source" / "api" / "dynamic_loader.py").exists(),
            "data_source_sources": (app_dir / "data_source" / "sources").exists(),
            "ui_data_source_panel": (app_dir.parent / "ui" / "src" / "components" / "data-source-panel.tsx").exists(),
        },
    }


def render_text(report: Dict[str, Any]) -> str:
    lines = ["Gerev data-source inventory", "=" * 29, f"app_dir: {report['app_dir']}", ""]
    lines.append("Connectors:")
    for entry in report["connector_classes"]:
        lines.append(f"  - {entry['class']} ({entry['file']})")
        lines.append(f"    methods: {', '.join(entry['methods'])}")
    lines.append("")
    lines.append("UI/API endpoints spotted:")
    lines.append(f"  {', '.join(report['ui_endpoints']) if report['ui_endpoints'] else 'none'}")
    lines.append("")
    lines.append("Source files present:")
    for name, present in report["source_files_present"].items():
        lines.append(f"  - {name}: {present}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", default="app", help="Path to the Gerev app directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if no connectors are found")
    args = parser.parse_args()

    app_dir = Path(args.app_dir).expanduser().resolve()
    if not (app_dir / "main.py").exists() and (app_dir / "app" / "main.py").exists():
        app_dir = (app_dir / "app").resolve()

    report = build_report(app_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.strict and not report["connector_classes"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
