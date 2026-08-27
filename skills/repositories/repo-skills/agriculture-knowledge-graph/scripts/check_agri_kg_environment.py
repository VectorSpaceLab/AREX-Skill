#!/usr/bin/env python3
"""Non-destructive environment and checkout preflight for Agriculture_KnowledgeGraph.

The check is intentionally conservative: it imports optional Python packages,
checks for expected repo files when --repo-root is supplied, and optionally
probes service sockets. It does not start Django, crawl the network, connect to
Neo4j/Mongo with credentials, download models, or run training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List

DEPENDENCIES = {
    "Django": "django",
    "THULAC": "thulac",
    "py2neo": "py2neo",
    "Neo4j Python driver": "neo4j",
    "pymongo": "pymongo",
    "pyfasttext": "pyfasttext",
    "Scrapy": "scrapy",
    "numpy": "numpy",
    "fire": "fire",
    "tqdm": "tqdm",
    "requests": "requests",
    "beautifulsoup4": "bs4",
}

EXPECTED_FILES = [
    "README.md",
    "requirement.txt",
    "hudong_pedia.csv",
    "hudong_pedia2.csv",
    "attributes.csv",
    "labels.txt",
    "predict_labels.txt",
    "demo/manage.py",
    "demo/demo/urls.py",
    "demo/toolkit/predict_labels.txt",
    "demo/toolkit/micropedia_tree.txt",
    "demo/toolkit/leaf_list.txt",
    "KNN_predict/classifier.py",
    "MyCrawler/scrapy.cfg",
    "wikidataSpider/readme.md",
    "wikidataSpider/wikidataProcessing/wikidata_relation.csv",
    "wikidataSpider/wikidataProcessing/wikidata_relation2.csv",
    "wikidataSpider/wikidataProcessing/new_node.csv",
    "wikidataSpider/weatherData/weather_plant.csv",
    "relationExtraction/readme.md",
    "relationExtraction/data/preprocessing.py",
]

SERVICES = {
    "neo4j-http": ("127.0.0.1", 7474),
    "mongodb": ("127.0.0.1", 27017),
}


def import_status(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "ok": True,
            "version": getattr(module, "__version__", None),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - diagnostic output only
        return {"ok": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}


def file_status(repo_root: Path) -> List[Dict[str, Any]]:
    rows = []
    for rel in EXPECTED_FILES:
        path = repo_root / rel
        rows.append({"path": rel, "exists": path.exists(), "is_file": path.is_file()})
    return rows


def probe_socket(host: str, port: int, timeout: float) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "error": None}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "legacy_python_hint": "The original repo targets old Python 3/Django 1.11-era dependencies; Python 3.7 is the safest starting point for legacy installs.",
        },
        "dependencies": {label: import_status(module) for label, module in DEPENDENCIES.items()},
        "repo_files": [],
        "services": {},
        "warnings": [],
    }

    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser().resolve()
        report["repo_root"] = str(repo_root)
        report["repo_files"] = file_status(repo_root)
        missing = [row["path"] for row in report["repo_files"] if not row["exists"]]
        if missing:
            report["warnings"].append(f"Missing expected files: {', '.join(missing[:12])}")
    else:
        report["warnings"].append("No --repo-root supplied; skipped checkout file checks.")

    if args.check_services:
        for name, (host, port) in SERVICES.items():
            report["services"][name] = probe_socket(host, port, args.timeout)
    else:
        report["warnings"].append("Skipped Neo4j/MongoDB socket probes; pass --check-services to include them.")

    missing_deps = [label for label, status in report["dependencies"].items() if not status["ok"]]
    if missing_deps:
        report["warnings"].append(
            "Missing optional/runtime imports: " + ", ".join(missing_deps)
        )
    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"Python: {report['python']['version']} ({report['python']['executable']})")
    print("\nDependencies:")
    for label, status in report["dependencies"].items():
        mark = "OK" if status["ok"] else "MISSING"
        version = f" {status['version']}" if status.get("version") else ""
        error = f" - {status['error']}" if status.get("error") else ""
        print(f"  {mark:7} {label}{version}{error}")
    if report.get("repo_files"):
        print("\nRepo files:")
        for row in report["repo_files"]:
            mark = "OK" if row["exists"] else "MISSING"
            print(f"  {mark:7} {row['path']}")
    if report.get("services"):
        print("\nServices:")
        for name, status in report["services"].items():
            mark = "OPEN" if status["ok"] else "CLOSED"
            error = f" - {status['error']}" if status.get("error") else ""
            print(f"  {mark:7} {name}{error}")
    if report.get("warnings"):
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Agriculture_KnowledgeGraph dependencies, files, and optional service sockets.")
    parser.add_argument("--repo-root", help="Path to an Agriculture_KnowledgeGraph checkout to inspect.")
    parser.add_argument("--check-services", action="store_true", help="Also probe localhost Neo4j HTTP and MongoDB sockets.")
    parser.add_argument("--timeout", type=float, default=0.5, help="Socket probe timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when dependencies or expected files are missing.")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)

    if args.strict:
        missing_deps = any(not status["ok"] for status in report["dependencies"].values())
        missing_files = any(not row["exists"] for row in report.get("repo_files", []))
        if missing_deps or missing_files:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
