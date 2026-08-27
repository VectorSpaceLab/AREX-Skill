#!/usr/bin/env python3
"""Safe diagnostics for Nexent knowledge/data/vector/storage/memory code paths.

The script performs static file checks, route extraction, config-name discovery,
and optional import/signature probes. It never starts Redis, Elasticsearch,
MinIO, Celery, Ray, LibreOffice, or model-provider calls.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


EXPECTED_FILES = [
    "sdk/nexent/data_process/core.py",
    "sdk/nexent/data_process/file_splitter.py",
    "sdk/nexent/data_process/unstructured_processor.py",
    "sdk/nexent/vector_database/base.py",
    "sdk/nexent/vector_database/elasticsearch_core.py",
    "sdk/nexent/vector_database/datamate_core.py",
    "sdk/nexent/storage/minio.py",
    "sdk/nexent/storage/minio_config.py",
    "sdk/nexent/memory/models.py",
    "sdk/nexent/memory/service.py",
    "sdk/nexent/memory/retrieval/pipeline.py",
    "sdk/nexent/memory/dreaming/service.py",
    "sdk/nexent/core/tools/knowledge_base_search_tool.py",
    "backend/apps/data_process_app.py",
    "backend/apps/vectordatabase_app.py",
    "backend/apps/knowledge_summary_app.py",
    "backend/apps/memory_config_app.py",
    "backend/apps/memory_record_app.py",
    "backend/apps/memory_dreaming_app.py",
    "backend/apps/memory_long_term_app.py",
    "backend/services/data_process_service.py",
    "backend/services/vectordatabase_service.py",
    "backend/services/memory_record_service.py",
    "backend/services/memory_retrieval_service.py",
    "backend/services/memory_context_service.py",
    "backend/services/memory_dreaming_service.py",
    "backend/consts/const.py",
]

CONFIG_NAMES_OF_INTEREST = [
    "ELASTICSEARCH_HOST",
    "ELASTICSEARCH_API_KEY",
    "ELASTICSEARCH_SERVICE",
    "DATA_PROCESS_SERVICE",
    "CLIP_MODEL_PATH",
    "TABLE_TRANSFORMER_MODEL_PATH",
    "UNSTRUCTURED_DEFAULT_MODEL_INITIALIZE_PARAMS_JSON_PATH",
    "MAX_FILE_SIZE",
    "MAX_CONCURRENT_CONVERSIONS",
    "LIBREOFFICE_PROFILE_DIR",
    "MINIO_ENDPOINT",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "MINIO_REGION",
    "MINIO_DEFAULT_BUCKET",
    "MINIO_SECURE",
    "REDIS_URL",
    "REDIS_BACKEND_URL",
    "DP_REDIS_CHUNKS_WAIT_TIMEOUT_S",
    "DP_REDIS_CHUNKS_POLL_INTERVAL_MS",
    "FORWARD_REDIS_RETRY_DELAY_S",
    "FORWARD_REDIS_RETRY_MAX",
    "DP_PART_PROCESSOR_COUNT",
    "DP_FILE_SPLIT_SIZE_MB",
    "RAY_ACTOR_NUM_CPUS",
    "MEMORY_SWITCH_KEY",
    "DREAMING_SWITCH_KEY",
    "MEMORY_AGENT_SHARE_KEY",
    "MMR_LAMBDA",
    "MMR_CANDIDATE_TOP_K",
    "MMR_FINAL_TOP_K",
    "MMR_DUPLICATE_THRESHOLD",
    "AGENT_SHORT_TERM_HALF_LIFE_DAYS",
    "W_AGENT_SHORT_TERM",
    "W_EXTERNAL",
    "MEMORY_TOKEN_BUDGET",
    "LIGHT_SLEEP_WINDOW_DAYS",
    "MIN_PROMOTION_SCORE",
    "MIN_RECALL_COUNT",
    "MIN_UNIQUE_QUERIES",
]

IMPORT_PROBES = [
    ("nexent.data_process.core", "DataProcessCore"),
    ("nexent.vector_database.base", "VectorDatabaseCore"),
    ("nexent.vector_database.elasticsearch_core", "ElasticSearchCore"),
    ("nexent.vector_database.datamate_core", "DataMateCore"),
    ("nexent.storage.minio_config", "MinIOStorageConfig"),
    ("nexent.storage.storage_client_factory", "create_storage_client_from_config"),
    ("nexent.memory.models", "MemorySearchRequest"),
    ("nexent.memory.service", "MemoryService"),
    ("nexent.memory.retrieval.pipeline", "RetrievalPipeline"),
    ("nexent.core.tools.knowledge_base_search_tool", "KnowledgeBaseSearchTool"),
    ("consts.const", None),
    ("services.memory_record_service", "MemoryRecordService"),
    ("services.memory_retrieval_service", "MemoryRetrievalService"),
    ("services.memory_context_service", "MemoryContextService"),
]

SIGNATURE_PROBES = [
    "nexent.data_process.core:DataProcessCore.file_process",
    "nexent.data_process.core:DataProcessCore.file_split",
    "nexent.vector_database.base:VectorDatabaseCore.vectorize_documents",
    "nexent.vector_database.base:VectorDatabaseCore.hybrid_search",
    "nexent.core.tools.knowledge_base_search_tool:KnowledgeBaseSearchTool.forward",
    "nexent.memory.service:MemoryService.store_memory",
    "nexent.memory.service:MemoryService.search_memory",
    "nexent.memory.retrieval.pipeline:RetrievalPipeline.run",
]

ROUTE_FILES = [
    "backend/apps/data_process_app.py",
    "backend/apps/vectordatabase_app.py",
    "backend/apps/knowledge_summary_app.py",
    "backend/apps/memory_config_app.py",
    "backend/apps/memory_record_app.py",
    "backend/apps/memory_dreaming_app.py",
    "backend/apps/memory_long_term_app.py",
]


def _add_source_paths(repo_root: Path) -> None:
    """Add checkout source roots to sys.path for import-only diagnostics."""
    for rel in ("backend", "sdk"):
        candidate = repo_root / rel
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def _short_error(exc: BaseException) -> Dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc).splitlines()[0][:500]}


def check_files(repo_root: Path) -> List[Dict[str, Any]]:
    results = []
    for rel in EXPECTED_FILES:
        path = repo_root / rel
        results.append({"path": rel, "exists": path.is_file()})
    return results


def discover_config_names(repo_root: Path) -> Dict[str, Any]:
    const_file = repo_root / "backend/consts/const.py"
    found: Dict[str, Dict[str, Optional[str]]] = {}
    if not const_file.is_file():
        return {"found": found, "missing_interest": CONFIG_NAMES_OF_INTEREST}

    text = const_file.read_text(encoding="utf-8", errors="replace")
    assign_re = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=\s*(.+)$", re.MULTILINE)
    getenv_re = re.compile(r"os\.getenv\(\s*['\"]([^'\"]+)['\"]")
    for match in assign_re.finditer(text):
        name, rhs = match.group(1), match.group(2).strip()
        env_match = getenv_re.search(rhs)
        found[name] = {
            "env_name": env_match.group(1) if env_match else None,
            "uses_os_getenv": bool(env_match),
        }
    missing = [name for name in CONFIG_NAMES_OF_INTEREST if name not in found]
    return {"found": {k: found[k] for k in CONFIG_NAMES_OF_INTEREST if k in found}, "missing_interest": missing}


def import_probe(module_name: str, attr_name: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"module": module_name, "attr": attr_name, "ok": False}
    try:
        module = importlib.import_module(module_name)
        if attr_name:
            getattr(module, attr_name)
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - diagnostics should capture every import failure
        result["error"] = _short_error(exc)
    return result


def resolve_object(spec: str) -> Any:
    module_name, object_path = spec.split(":", 1)
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in object_path.split("."):
        obj = getattr(obj, part)
    return obj


def signature_probe(spec: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"object": spec, "ok": False}
    try:
        obj = resolve_object(spec)
        result["signature"] = str(inspect.signature(obj))
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001
        result["error"] = _short_error(exc)
    return result


def _literal_str(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_routes(repo_root: Path) -> List[Dict[str, Any]]:
    routes: List[Dict[str, Any]] = []
    for rel in ROUTE_FILES:
        path = repo_root / rel
        if not path.is_file():
            routes.append({"file": rel, "ok": False, "error": "file missing"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text)
        except Exception as exc:  # noqa: BLE001
            routes.append({"file": rel, "ok": False, "error": _short_error(exc)})
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                method = None
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id.endswith("router") or func.value.id == "router":
                        method = func.attr.upper()
                if not method:
                    continue
                route_path = _literal_str(dec.args[0]) if dec.args else ""
                routes.append({
                    "file": rel,
                    "method": method,
                    "path": route_path,
                    "function": node.name,
                })
    return routes


def summarize_status(file_checks: Iterable[Dict[str, Any]], imports: Iterable[Dict[str, Any]]) -> str:
    missing_required = [item for item in file_checks if not item.get("exists")]
    failed_imports = [item for item in imports if not item.get("ok")]
    if missing_required:
        return "incomplete"
    if failed_imports:
        return "degraded"
    return "ok"


def build_report(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    _add_source_paths(repo_root)
    file_checks = check_files(repo_root)
    imports = [import_probe(module, attr) for module, attr in IMPORT_PROBES]
    signatures = [signature_probe(spec) for spec in SIGNATURE_PROBES]
    report = {
        "status": summarize_status(file_checks, imports),
        "repo_root_name": repo_root.name,
        "python": sys.version.split()[0],
        "checks": {
            "expected_files": file_checks,
            "config_names": discover_config_names(repo_root),
            "imports": imports,
            "signatures": signatures,
            "routes": extract_routes(repo_root),
        },
        "notes": [
            "Import failures usually indicate missing optional dependencies or backend extras; they do not prove live services are unavailable.",
            "This script performs no network calls and starts no Redis, Elasticsearch, MinIO, Celery, Ray, LibreOffice, or provider processes.",
        ],
    }
    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"repo: {report['repo_root_name']}")
    missing = [item["path"] for item in report["checks"]["expected_files"] if not item["exists"]]
    print(f"expected files: {'ok' if not missing else 'missing ' + ', '.join(missing)}")
    failed_imports = [item for item in report["checks"]["imports"] if not item["ok"]]
    if failed_imports:
        print("failed imports:")
        for item in failed_imports:
            err = item.get("error", {})
            attr = f":{item['attr']}" if item.get("attr") else ""
            print(f"  - {item['module']}{attr}: {err.get('type')}: {err.get('message')}")
    else:
        print("imports: ok")
    missing_config = report["checks"]["config_names"].get("missing_interest", [])
    print(f"config names of interest: {'ok' if not missing_config else 'missing ' + ', '.join(missing_config)}")
    print(f"routes discovered: {len(report['checks']['routes'])}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Safe Nexent knowledge/data/vector/storage/memory diagnostics")
    parser.add_argument("--repo-root", default=".", help="Path to the Nexent repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact text summary")
    args = parser.parse_args(argv)

    report = build_report(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
