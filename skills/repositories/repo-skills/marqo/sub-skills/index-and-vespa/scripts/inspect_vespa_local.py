#!/usr/bin/env python3
"""Read-only Marqo Vespa-local prerequisite inspector.

The script accepts a repository root and checks for the files and host tools that
matter before a human/agent decides to start Vespa, deploy a schema, or build the
custom Java searcher. It never starts Docker/Vespa, never runs Maven, and never
executes repository scripts.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

EXPECTED_FILES = {
    "vespa_local_script": "components/marqo/scripts/vespa_local/vespa_local.py",
    "semi_template_current": (
        "components/marqo/src/marqo/core/semi_structured_vespa_index/"
        "semi_structured_vespa_schema_template_2_16.sd.jinja2"
    ),
    "semi_template_legacy": (
        "components/marqo/src/marqo/core/semi_structured_vespa_index/"
        "semi_structured_vespa_schema_template.sd.jinja2"
    ),
    "vespa_pom": "components/marqo/vespa/pom.xml",
    "custom_searcher": "components/marqo/vespa/src/main/java/ai/marqo/search/HybridSearcher.java",
    "index_settings_def": "components/marqo/vespa/src/main/resources/configdefinitions/index-settings.def",
}

HOST_TOOLS = {
    "docker": "required before starting local Vespa containers",
    "java": "required before building the custom Vespa searcher bundle",
    "mvn": "required before running the custom-searcher Maven package build",
    "curl": "useful for manual Vespa/Marqo health checks",
}

EXPECTED_MODES = [
    "full-start",
    "start",
    "restart",
    "deploy-config",
    "stop",
    "generate-and-deploy",
]


def _file_info(repo_root: Path, rel_path: str) -> Dict[str, Any]:
    path = repo_root / rel_path
    info: Dict[str, Any] = {
        "path": rel_path,
        "exists": path.is_file(),
    }
    if path.is_file():
        stat = path.stat()
        info.update({"bytes": stat.st_size})
    return info


def _read_text_if_exists(repo_root: Path, rel_path: str, max_bytes: int = 200_000) -> Optional[str]:
    path = repo_root / rel_path
    if not path.is_file():
        return None
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def _inspect_vespa_local_script(repo_root: Path) -> Dict[str, Any]:
    rel = EXPECTED_FILES["vespa_local_script"]
    text = _read_text_if_exists(repo_root, rel)
    result: Dict[str, Any] = {"path": rel, "exists": text is not None}
    if text is None:
        return result

    result["declared_modes"] = [mode for mode in EXPECTED_MODES if f'"{mode}"' in text or f"'{mode}'" in text]
    result["contains_docker_invocation"] = "docker" in text
    result["contains_deploy_call"] = "deploy" in text.lower()
    result["default_config_url"] = _regex_value(text, r'VESPA_CONFIG_URL\s*=\s*["\']([^"\']+)')
    result["default_document_url"] = _regex_value(text, r'VESPA_DOCUMENT_URL\s*=\s*["\']([^"\']+)')
    result["default_query_url"] = _regex_value(text, r'VESPA_QUERY_URL\s*=\s*["\']([^"\']+)')
    result["default_vespa_version"] = _regex_value(text, r"VESPA_VERSION\s*=\s*os\.getenv\([^,]+,\s*[\"']([^\"']+)")
    result["default_disk_limit"] = _regex_value(text, r"VESPA_DISK_USAGE_LIMIT\s*=\s*float\(os\.getenv\([^,]+,\s*([^\)]+)\)\)")
    return result


def _regex_value(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def _inspect_pom(repo_root: Path) -> Dict[str, Any]:
    rel = EXPECTED_FILES["vespa_pom"]
    path = repo_root / rel
    result: Dict[str, Any] = {"path": rel, "exists": path.is_file()}
    if not path.is_file():
        return result

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        result["parse_error"] = str(exc)
        return result

    ns = {"m": "http://maven.apache.org/POM/4.0.0"}

    def find_text(expr: str) -> Optional[str]:
        value = root.findtext(expr, namespaces=ns)
        return value.strip() if value else None

    result.update(
        {
            "group_id": find_text("m:groupId") or find_text("m:parent/m:groupId"),
            "artifact_id": find_text("m:artifactId"),
            "version": find_text("m:version"),
            "packaging": find_text("m:packaging"),
            "java_version": find_text("m:properties/m:java.version"),
            "vespa_parent_version": find_text("m:parent/m:version"),
        }
    )
    return result


def _host_tools() -> Dict[str, Dict[str, Any]]:
    return {
        tool: {"available": shutil.which(tool) is not None, "purpose": purpose}
        for tool, purpose in HOST_TOOLS.items()
    }


def _overall_status(files: Dict[str, Dict[str, Any]], tools: Dict[str, Dict[str, Any]]) -> str:
    required_file_keys = [
        "vespa_local_script",
        "semi_template_current",
        "semi_template_legacy",
        "vespa_pom",
        "custom_searcher",
        "index_settings_def",
    ]
    missing_files = [key for key in required_file_keys if not files[key]["exists"]]
    missing_core_tools = [tool for tool in ["docker", "java", "mvn"] if not tools[tool]["available"]]
    if missing_files:
        return "missing-files"
    if missing_core_tools:
        return "files-ok-tools-missing"
    return "ready-for-reviewed-service-plan"


def build_report(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.expanduser().resolve()
    files = {key: _file_info(repo_root, rel) for key, rel in EXPECTED_FILES.items()}
    tools = _host_tools()
    report = {
        "script_policy": {
            "read_only": True,
            "does_not_start_docker_or_vespa": True,
            "does_not_run_maven": True,
            "does_not_execute_repository_scripts": True,
        },
        "files": files,
        "vespa_local_script": _inspect_vespa_local_script(repo_root),
        "pom": _inspect_pom(repo_root),
        "host_tools": tools,
        "required_services_for_later_mutating_steps": {
            "local_vespa_single_node": {
                "config_url": "http://localhost:19071",
                "document_url": "http://localhost:8080",
                "query_url": "http://localhost:8080",
                "zookeeper": "localhost:2181",
            },
            "custom_searcher_build": {
                "requires": ["JDK 17", "Maven", "Vespa application package redeploy after build"],
            },
        },
        "status": "unknown",
    }
    report["status"] = _overall_status(files, tools)
    return report


def print_text_report(report: Dict[str, Any]) -> None:
    print("Marqo Vespa-local prerequisite inspection (read-only)")
    print(f"Status: {report['status']}")
    print("\nFiles:")
    for key, info in report["files"].items():
        state = "OK" if info["exists"] else "MISSING"
        suffix = f" ({info['bytes']} bytes)" if info.get("bytes") is not None else ""
        print(f"  - {key}: {state} {info['path']}{suffix}")

    vespa_script = report["vespa_local_script"]
    print("\nLocal Vespa helper:")
    if vespa_script.get("exists"):
        print(f"  - modes detected: {', '.join(vespa_script.get('declared_modes', [])) or 'none'}")
        print(f"  - default config URL: {vespa_script.get('default_config_url') or 'not detected'}")
        print(f"  - default document URL: {vespa_script.get('default_document_url') or 'not detected'}")
        print(f"  - default query URL: {vespa_script.get('default_query_url') or 'not detected'}")
        print(f"  - default Vespa version: {vespa_script.get('default_vespa_version') or 'not detected'}")
        print(f"  - contains Docker/deploy code: {vespa_script.get('contains_docker_invocation')} / {vespa_script.get('contains_deploy_call')}")
    else:
        print("  - helper script missing")

    pom = report["pom"]
    print("\nCustom searcher Maven package:")
    if pom.get("exists") and not pom.get("parse_error"):
        for field in ["group_id", "artifact_id", "version", "packaging", "java_version", "vespa_parent_version"]:
            print(f"  - {field}: {pom.get(field) or 'not detected'}")
    elif pom.get("parse_error"):
        print(f"  - parse error: {pom['parse_error']}")
    else:
        print("  - pom missing")

    print("\nHost tools (not executed):")
    for tool, info in report["host_tools"].items():
        state = "available" if info["available"] else "missing"
        print(f"  - {tool}: {state} — {info['purpose']}")

    print("\nPolicy:")
    for key, value in report["script_policy"].items():
        print(f"  - {key}: {value}")

    print("\nNext step: if service mutation is required, switch to the local-development guidance for the reviewed command plan.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only inspection of Marqo local Vespa files and custom-searcher prerequisites."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable report.",
    )
    args = parser.parse_args(argv)

    report = build_report(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
