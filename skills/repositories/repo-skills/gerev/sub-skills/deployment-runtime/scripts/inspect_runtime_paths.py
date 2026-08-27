#!/usr/bin/env python3
"""Read-only runtime layout inspector for Gerev.

The helper avoids importing the full app and instead inspects the source tree,
startup scripts, Docker/compose settings, and UI package scripts.
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


def parse_ui_scripts(ui_dir: Path) -> Dict[str, Any]:
    pkg = ui_dir / "package.json"
    if not pkg.exists():
        return {"exists": False, "scripts": {}}
    try:
        data = json.loads(read_text(pkg))
    except json.JSONDecodeError:
        return {"exists": True, "scripts": {}, "error": "invalid JSON"}
    return {"exists": True, "scripts": data.get("scripts", {})}


def storage_logic(app_dir: Path) -> Dict[str, Any]:
    text = read_text(app_dir / "paths.py")
    return {
        "docker_deployment_gate": "DOCKER_DEPLOYMENT" in text,
        "docker_storage_path": "/opt/storage" in text,
        "local_storage_fallback": ".gerev/storage" in text,
        "ui_build_path": "../ui/build" in text or "/ui/" in text,
    }


def routes_and_startup(app_dir: Path) -> Dict[str, Any]:
    text = read_text(app_dir / "main.py")
    return {
        "warnings_about_cuda": "CUDA is not available" in text,
        "startup_event_present": "startup_event" in text,
        "status_route_present": "/api/v1/status" in text,
        "clear_index_route_present": "/clear-index" in text,
        "check_new_documents_route_present": "/check-for-new-documents" in text,
        "serve_ui_route_present": "serve_ui" in text,
    }


def build_report(app_dir: Path) -> Dict[str, Any]:
    repo_root = app_dir.parent
    return {
        "app_dir": str(app_dir),
        "root_files": {
            "run.sh": (repo_root / "run.sh").exists(),
            "Dockerfile": (repo_root / "Dockerfile").exists(),
            "docker-compose.yaml": (repo_root / "docker-compose.yaml").exists(),
            "app_readme": (app_dir / "README.md").exists(),
        },
        "storage_logic": storage_logic(app_dir),
        "startup_and_routes": routes_and_startup(app_dir),
        "ui": parse_ui_scripts(repo_root / "ui"),
        "known_split_pdf_import_defect": "split_PDF_into_paragraphs" in read_text(app_dir / "indexing" / "index_documents.py") and "split_PDF_into_paragraphs" not in read_text(app_dir / "parsers" / "pdf.py"),
    }


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Gerev deployment/runtime inventory")
    lines.append("=" * 36)
    lines.append(f"app_dir: {report['app_dir']}")
    lines.append("")
    lines.append("Root files:")
    for key, present in report["root_files"].items():
        lines.append(f"  - {key}: {present}")
    lines.append("")
    lines.append("Storage logic:")
    for key, value in report["storage_logic"].items():
        lines.append(f"  - {key}: {value}")
    lines.append("")
    lines.append("Startup/routes:")
    for key, value in report["startup_and_routes"].items():
        lines.append(f"  - {key}: {value}")
    lines.append("")
    lines.append("UI scripts:")
    if report["ui"]["exists"]:
        lines.append(f"  scripts: {', '.join(sorted(report['ui']['scripts'])) if report['ui']['scripts'] else 'none'}")
    else:
        lines.append("  package.json missing")
    lines.append("")
    lines.append(f"known_split_pdf_import_defect: {report['known_split_pdf_import_defect']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", default="app", help="Path to the Gerev app directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required runtime files are missing")
    args = parser.parse_args()

    app_dir = Path(args.app_dir).expanduser().resolve()
    if not (app_dir / "main.py").exists() and (app_dir / "app" / "main.py").exists():
        app_dir = (app_dir / "app").resolve()

    report = build_report(app_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.strict and (
        not all(report["root_files"].values()) or report["known_split_pdf_import_defect"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
