#!/usr/bin/env python3
"""
Read-only diagnostics for Gerev search/indexing source shape and storage files.

The helper avoids importing the Gerev app because app imports can load large
Hugging Face models and may currently fail on the missing PDF split helper.
It uses only the Python standard library except for an optional NLTK data probe
when nltk is installed in the active environment.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import sqlite3
import sys
import urllib.parse
from typing import Any, Dict, List, Tuple

EXPECTED_FILES = [
    "search_logic.py",
    "models.py",
    "main.py",
    "db_engine.py",
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

STORAGE_FILENAMES = [
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


def infer_storage_dir(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    if os.environ.get("DOCKER_DEPLOYMENT"):
        return Path("/opt/storage").resolve()
    return (Path.home() / ".gerev" / "storage").resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def defined_functions(path: Path) -> Tuple[List[str], str | None]:
    text = read_text(path)
    if not text:
        return [], "file missing or unreadable"
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [], f"syntax error: {exc}"
    names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return sorted(names), None


def source_shape(app_dir: Path) -> Dict[str, Any]:
    missing = [rel for rel in EXPECTED_FILES if not (app_dir / rel).exists()]
    pdf_functions, pdf_parse_error = defined_functions(app_dir / "parsers" / "pdf.py")
    index_documents_text = read_text(app_dir / "indexing" / "index_documents.py")
    models_text = read_text(app_dir / "models.py")
    search_text = read_text(app_dir / "search_logic.py")

    model_mentions = {model: (model in models_text) for model in EXPECTED_MODELS}
    missing_model_mentions = [model for model, present in model_mentions.items() if not present]

    imports_split = "split_PDF_into_paragraphs" in index_documents_text
    defines_split = "split_PDF_into_paragraphs" in pdf_functions

    return {
        "app_dir": str(app_dir),
        "missing_expected_files": missing,
        "pdf_functions": pdf_functions,
        "pdf_parse_error": pdf_parse_error,
        "index_documents_imports_split_PDF_into_paragraphs": imports_split,
        "pdf_defines_split_PDF_into_paragraphs": defines_split,
        "known_split_pdf_import_defect": bool(imports_split and not defines_split),
        "model_mentions": model_mentions,
        "missing_model_mentions": missing_model_mentions,
        "search_logic_downloads_punkt": "nltk.download('punkt')" in search_text or 'nltk.download("punkt")' in search_text,
    }


def nltk_probe() -> Dict[str, Any]:
    result: Dict[str, Any] = {"nltk_importable": False, "resources": {}}
    try:
        import nltk  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller environment
        result["error"] = repr(exc)
        return result

    result["nltk_importable"] = True
    for resource in ["tokenizers/punkt", "tokenizers/punkt_tab"]:
        try:
            found = nltk.data.find(resource)
            result["resources"][resource] = {"present": True, "path": str(found)}
        except LookupError as exc:
            result["resources"][resource] = {"present": False, "error": str(exc).splitlines()[0] if str(exc) else "LookupError"}
        except Exception as exc:  # pragma: no cover
            result["resources"][resource] = {"present": False, "error": repr(exc)}
    return result


def sqlite_readonly_summary(path: Path) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"tables": {}, "errors": []}
    if not path.exists():
        return summary
    try:
        uri = "file:" + urllib.parse.quote(str(path.resolve()), safe="/") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    except Exception as exc:
        summary["errors"].append(f"open failed: {exc}")
        return summary

    try:
        rows = conn.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
        ).fetchall()
        for (table_name,) in rows:
            try:
                count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                summary["tables"][table_name] = count
            except Exception as exc:
                summary["tables"][table_name] = f"count failed: {exc}"
    except Exception as exc:
        summary["errors"].append(f"table scan failed: {exc}")
    finally:
        conn.close()
    return summary


def storage_shape(storage_dir: Path, include_sqlite: bool) -> Dict[str, Any]:
    files: Dict[str, Any] = {}
    for filename in STORAGE_FILENAMES:
        path = storage_dir / filename
        info: Dict[str, Any] = {"exists": path.exists()}
        if path.exists():
            try:
                stat = path.stat()
                info.update({"size_bytes": stat.st_size, "is_file": path.is_file()})
            except OSError as exc:
                info["stat_error"] = repr(exc)
            if include_sqlite and filename.endswith(".sqlite3"):
                info["sqlite"] = sqlite_readonly_summary(path)
        files[filename] = info
    return {"storage_dir": str(storage_dir), "exists": storage_dir.exists(), "files": files}


def classify(report: Dict[str, Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    src = report["source"]
    if src["missing_expected_files"]:
        findings.append({
            "severity": "error",
            "code": "missing-source-files",
            "message": "Expected search/indexing source files are missing: " + ", ".join(src["missing_expected_files"]),
        })
    if src["known_split_pdf_import_defect"]:
        findings.append({
            "severity": "error",
            "code": "split-pdf-import-defect",
            "message": "indexing/index_documents.py imports split_PDF_into_paragraphs, but parsers/pdf.py does not define it.",
        })
    if src["missing_model_mentions"]:
        findings.append({
            "severity": "warning",
            "code": "model-id-drift",
            "message": "Expected model ids were not found in models.py: " + ", ".join(src["missing_model_mentions"]),
        })
    nltk = report["nltk"]
    if not nltk.get("nltk_importable"):
        findings.append({
            "severity": "warning",
            "code": "nltk-not-importable",
            "message": "nltk is not importable in the current helper environment; BM25 tokenization cannot be checked here.",
        })
    else:
        missing = [name for name, data in nltk.get("resources", {}).items() if not data.get("present")]
        if missing:
            findings.append({
                "severity": "warning",
                "code": "missing-nltk-data",
                "message": "Missing NLTK resources: " + ", ".join(missing),
            })
    storage = report["storage"]
    if not storage["exists"]:
        findings.append({
            "severity": "warning",
            "code": "storage-missing",
            "message": "Storage directory does not exist. This is normal before first startup but explains empty search/index state.",
        })
    else:
        db = storage["files"].get("db.sqlite3", {})
        if db.get("exists") and "sqlite" in db:
            tables = db["sqlite"].get("tables", {})
            if "paragraph" in tables and tables.get("paragraph") == 0:
                findings.append({
                    "severity": "info",
                    "code": "no-paragraphs",
                    "message": "The main database has a paragraph table but no paragraph rows; search will return empty results.",
                })
    return findings


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Gerev search/indexing read-only diagnostic")
    lines.append("=" * 45)
    lines.append(f"app_dir: {report['source']['app_dir']}")
    lines.append(f"storage_dir: {report['storage']['storage_dir']}")
    lines.append("")

    lines.append("Source shape:")
    missing = report["source"]["missing_expected_files"]
    lines.append(f"  missing expected files: {', '.join(missing) if missing else 'none'}")
    lines.append(f"  PDF parser functions: {', '.join(report['source']['pdf_functions']) or 'none/read failed'}")
    lines.append(f"  known split_PDF import defect: {report['source']['known_split_pdf_import_defect']}")
    lines.append(f"  search_logic downloads punkt: {report['source']['search_logic_downloads_punkt']}")
    lines.append("  model ids present:")
    for model, present in report["source"]["model_mentions"].items():
        lines.append(f"    - {model}: {present}")
    lines.append("")

    lines.append("NLTK probe:")
    if not report["nltk"].get("nltk_importable"):
        lines.append(f"  nltk importable: false ({report['nltk'].get('error', 'no detail')})")
    else:
        lines.append("  nltk importable: true")
        for resource, data in report["nltk"].get("resources", {}).items():
            status = "present" if data.get("present") else "missing"
            detail = data.get("path") or data.get("error") or ""
            lines.append(f"  {resource}: {status} {detail}".rstrip())
    lines.append("")

    lines.append("Storage files:")
    lines.append(f"  storage exists: {report['storage']['exists']}")
    for filename, data in report["storage"]["files"].items():
        if data.get("exists"):
            lines.append(f"  {filename}: present, {data.get('size_bytes', '?')} bytes")
            sqlite_summary = data.get("sqlite")
            if sqlite_summary:
                tables = sqlite_summary.get("tables", {})
                if tables:
                    rendered = ", ".join(f"{name}={count}" for name, count in tables.items())
                    lines.append(f"    sqlite tables: {rendered}")
                for error in sqlite_summary.get("errors", []):
                    lines.append(f"    sqlite error: {error}")
        else:
            lines.append(f"  {filename}: missing")
    lines.append("")

    lines.append("Findings:")
    if report["findings"]:
        for finding in report["findings"]:
            lines.append(f"  [{finding['severity']}] {finding['code']}: {finding['message']}")
    else:
        lines.append("  none")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only Gerev search/indexing diagnostics")
    parser.add_argument("--app-dir", default=".", help="Path to the Gerev app directory or repository root")
    parser.add_argument("--storage-dir", default=None, help="Storage directory to inspect; defaults to Docker or home storage inference")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--sqlite-details", action="store_true", help="Read SQLite table names/counts in mode=ro")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when error-severity findings are present")
    args = parser.parse_args(argv)

    app_dir = resolve_app_dir(args.app_dir)
    storage_dir = infer_storage_dir(args.storage_dir)
    report: Dict[str, Any] = {
        "source": source_shape(app_dir),
        "nltk": nltk_probe(),
        "storage": storage_shape(storage_dir, include_sqlite=args.sqlite_details),
    }
    report["findings"] = classify(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.strict and any(item["severity"] == "error" for item in report["findings"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
