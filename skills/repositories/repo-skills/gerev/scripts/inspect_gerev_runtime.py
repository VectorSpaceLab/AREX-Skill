#!/usr/bin/env python3
"""Read-only diagnostics for Gerev runtime structure.

This helper avoids importing the full Gerev app because the app import can
load large Hugging Face models and currently fails on the known missing PDF
split helper. It uses only the Python standard library plus an optional NLTK
probe when nltk is installed in the active environment.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import sqlite3
import urllib.parse
from typing import Any, Dict, List, Tuple

EXPECTED_FILES = [
    "main.py",
    "models.py",
    "search_logic.py",
    "db_engine.py",
    "paths.py",
    "api/data_source.py",
    "api/search.py",
    "data_source/api/base_data_source.py",
    "data_source/api/context.py",
    "data_source/api/dynamic_loader.py",
    "indexing/index_documents.py",
    "indexing/bm25_index.py",
    "indexing/faiss_index.py",
    "indexing/background_indexer.py",
    "queues/index_queue.py",
    "queues/task_queue.py",
    "parsers/pdf.py",
    "parsers/html.py",
    "parsers/docx.py",
    "parsers/pptx.py",
    "parsers/txt.py",
    "schemas/document.py",
    "schemas/paragraph.py",
]

EXPECTED_MODELS = [
    "multi-qa-MiniLM-L6-cos-v1",
    "cross-encoder/ms-marco-TinyBERT-L-2-v2",
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "deepset/roberta-base-squad2",
]

STORAGE_FILES = [
    "db.sqlite3",
    "tasks.sqlite3",
    "indexing.sqlite3",
    "faiss_index.bin",
    "bm25_index.bin",
    ".uuid",
]


def resolve_app_dir(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if (candidate / "main.py").exists() and (candidate / "search_logic.py").exists():
        return candidate.resolve()
    if (candidate / "app" / "main.py").exists() and (candidate / "app" / "search_logic.py").exists():
        return (candidate / "app").resolve()
    return candidate.resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def ast_tree(path: Path):
    text = read_text(path)
    if not text:
        return None, "file missing or unreadable"
    try:
        return ast.parse(text, filename=str(path)), None
    except SyntaxError as exc:
        return None, f"syntax error: {exc}"


def function_names(path: Path) -> Tuple[List[str], str | None]:
    tree, error = ast_tree(path)
    if error or tree is None:
        return [], error
    names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return sorted(names), None


def class_methods(path: Path) -> Dict[str, List[str]]:
    tree, error = ast_tree(path)
    if error or tree is None:
        return {}
    result: Dict[str, List[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            result[node.name] = sorted(methods)
    return result


def source_summary(app_dir: Path) -> Dict[str, Any]:
    main_text = read_text(app_dir / "main.py")
    search_text = read_text(app_dir / "search_logic.py")
    models_text = read_text(app_dir / "models.py")
    index_text = read_text(app_dir / "indexing" / "index_documents.py")
    pdf_functions, pdf_error = function_names(app_dir / "parsers" / "pdf.py")

    connectors = []
    for path in sorted((app_dir / "data_source" / "sources").glob("**/*.py")):
        if path.name == "__init__.py":
            continue
        methods = class_methods(path)
        for class_name, method_list in methods.items():
            if "BaseDataSource" in read_text(path):
                connectors.append({
                    "file": str(path.relative_to(app_dir)),
                    "class": class_name,
                    "methods": method_list,
                })

    routes = []
    for path in [app_dir / "api" / "data_source.py", app_dir / "api" / "search.py", app_dir / "main.py"]:
        tree, error = ast_tree(path)
        if error or tree is None:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                route_names = []
                for deco in node.decorator_list:
                    text = ast.get_source_segment(read_text(path), deco) or ""
                    if "router." in text or "app." in text or "repeat_every" in text:
                        route_names.append(text.strip())
                if route_names:
                    routes.append({"file": str(path.relative_to(app_dir)), "function": node.name, "decorators": route_names})

    return {
        "expected_files_missing": [f for f in EXPECTED_FILES if not (app_dir / f).exists()],
        "known_split_pdf_import_defect": "split_PDF_into_paragraphs" in index_text and "split_PDF_into_paragraphs" not in pdf_functions,
        "pdf_functions": pdf_functions,
        "pdf_parse_error": pdf_error,
        "model_mentions": {model: (model in models_text) for model in EXPECTED_MODELS},
        "search_logic_downloads_punkt": "nltk.download('punkt')" in search_text or 'nltk.download("punkt")' in search_text,
        "connectors": connectors,
        "routes": routes,
        "main_has_startup_event": "startup_event" in main_text,
    }


def ui_summary(app_dir: Path) -> Dict[str, Any]:
    pkg = app_dir.parent / "ui" / "package.json"
    try:
        data = json.loads(read_text(pkg)) if pkg.exists() else {}
    except json.JSONDecodeError:
        data = {}
    return {
        "package_json_exists": pkg.exists(),
        "scripts": data.get("scripts", {}),
    }


def storage_summary(storage_dir: Path, include_sqlite: bool) -> Dict[str, Any]:
    files: Dict[str, Any] = {}
    for filename in STORAGE_FILES:
        path = storage_dir / filename
        info: Dict[str, Any] = {"exists": path.exists()}
        if path.exists():
            try:
                stat = path.stat()
                info.update({"size_bytes": stat.st_size, "is_file": path.is_file()})
            except OSError as exc:
                info["stat_error"] = repr(exc)
            if include_sqlite and filename.endswith(".sqlite3"):
                try:
                    uri = "file:" + urllib.parse.quote(str(path.resolve()), safe="/") + "?mode=ro"
                    conn = sqlite3.connect(uri, uri=True)
                    try:
                        rows = conn.execute(
                            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
                        ).fetchall()
                        info["tables"] = {name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for (name,) in rows}
                    finally:
                        conn.close()
                except Exception as exc:
                    info["sqlite_error"] = str(exc)
        files[filename] = info
    return {"exists": storage_dir.exists(), "storage_dir": str(storage_dir), "files": files}


def nltk_summary() -> Dict[str, Any]:
    result: Dict[str, Any] = {"importable": False, "resources": {}}
    try:
        import nltk  # type: ignore
    except Exception as exc:
        result["error"] = repr(exc)
        return result

    result["importable"] = True
    for resource in ["tokenizers/punkt", "tokenizers/punkt_tab"]:
        try:
            found = nltk.data.find(resource)
            result["resources"][resource] = {"present": True, "path": str(found)}
        except LookupError as exc:
            result["resources"][resource] = {"present": False, "error": str(exc).splitlines()[0] if str(exc) else "LookupError"}
        except Exception as exc:
            result["resources"][resource] = {"present": False, "error": repr(exc)}
    return result


def build_report(app_dir: Path, storage_dir: Path | None) -> Dict[str, Any]:
    report = {
        "app_dir": str(app_dir),
        "source": source_summary(app_dir),
        "ui": ui_summary(app_dir),
        "nltk": nltk_summary(),
        "storage": storage_summary(storage_dir, include_sqlite=True) if storage_dir else {"exists": False, "storage_dir": None, "files": {}},
    }
    return report


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Gerev runtime diagnostic")
    lines.append("=" * 24)
    lines.append(f"app_dir: {report['app_dir']}")
    lines.append("")
    src = report["source"]
    lines.append("Source summary:")
    lines.append(f"  missing files: {', '.join(src['expected_files_missing']) if src['expected_files_missing'] else 'none'}")
    lines.append(f"  split_PDF import defect: {src['known_split_pdf_import_defect']}")
    lines.append(f"  search_logic downloads punkt: {src['search_logic_downloads_punkt']}")
    lines.append(f"  startup event present: {src['main_has_startup_event']}")
    lines.append("  model mentions:")
    for model, present in src["model_mentions"].items():
        lines.append(f"    - {model}: {present}")
    lines.append(f"  connectors discovered: {len(src['connectors'])}")
    lines.append(f"  route-like functions discovered: {len(src['routes'])}")
    lines.append("")
    lines.append("UI summary:")
    lines.append(f"  package.json present: {report['ui']['package_json_exists']}")
    if report['ui']['scripts']:
        lines.append(f"  scripts: {', '.join(sorted(report['ui']['scripts']))}")
    lines.append("")
    lines.append("NLTK summary:")
    if report["nltk"].get("importable"):
        for resource, data in report["nltk"].get("resources", {}).items():
            status = "present" if data.get("present") else "missing"
            detail = data.get("path") or data.get("error") or ""
            lines.append(f"  {resource}: {status} {detail}".rstrip())
    else:
        lines.append(f"  nltk importable: false ({report['nltk'].get('error', 'no detail')})")
    lines.append("")
    lines.append("Storage summary:")
    storage = report["storage"]
    lines.append(f"  storage dir: {storage['storage_dir']}")
    lines.append(f"  exists: {storage['exists']}")
    for name, data in storage.get("files", {}).items():
        if data.get("exists"):
            lines.append(f"  {name}: present ({data.get('size_bytes', '?')} bytes)")
            if "tables" in data:
                table_summary = ", ".join(f"{table}={count}" for table, count in data["tables"].items())
                lines.append(f"    tables: {table_summary}")
            if "sqlite_error" in data:
                lines.append(f"    sqlite error: {data['sqlite_error']}")
        else:
            lines.append(f"  {name}: missing")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", default="app", help="Path to the Gerev app directory")
    parser.add_argument("--storage-dir", help="Optional storage directory to inspect")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when known source defects are present")
    args = parser.parse_args()

    app_dir = resolve_app_dir(args.app_dir)
    storage_dir = Path(args.storage_dir).expanduser().resolve() if args.storage_dir else None
    report = build_report(app_dir, storage_dir)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.strict and (report["source"]["known_split_pdf_import_defect"] or report["source"]["expected_files_missing"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
