#!/usr/bin/env python3
"""Read-only static inventory for a CubeStudio checkout.

This helper is intentionally safe:
- it does not import the original repository
- it does not connect to services
- it does not run Docker, Kubernetes, npm, or build commands
- it only inspects files and prints a compact summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


KEY_FILES = [
    "README.md",
    "install/README.md",
    "install/docker/README.md",
    "install/docker/docker-compose.yml",
    "install/docker/config.py",
    "install/docker/project.py",
    "install/docker/entrypoint.sh",
    "myapp/__init__.py",
    "myapp/cli.py",
    "myapp/config.py",
    "myapp/project.py",
    "myapp/init/init-job-template.json",
    "myapp/init/init-pipeline.json",
    "myapp/init/init-service.json",
    "myapp/init/init-inference.json",
    "myapp/init/init-aihub.json",
    "myapp/init/init-chat.json",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def file_info(path: Path) -> Dict[str, Any]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {"exists": False}
    info = {"exists": True, "size": stat.st_size, "is_empty": stat.st_size == 0}
    if path.suffix == ".json":
        try:
            with path.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            info["json_type"] = type(obj).__name__
            info["json_len"] = len(obj) if hasattr(obj, "__len__") else None
        except Exception as exc:
            info["json_error"] = str(exc)
    if path.name == "package.json":
        try:
            with path.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            info["package_name"] = obj.get("name")
            info["scripts"] = sorted((obj.get("scripts") or {}).keys())
        except Exception as exc:
            info["package_error"] = str(exc)
    return info


def yaml_summary(path: Path) -> Dict[str, Any]:
    if yaml is None:
        return {"available": False}
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = yaml.safe_load(f)
        summary: Dict[str, Any] = {"available": True, "type": type(obj).__name__}
        if isinstance(obj, dict):
            if "services" in obj and isinstance(obj["services"], dict):
                summary["services"] = sorted(obj["services"].keys())
            if "kind" in obj:
                summary["kind"] = obj.get("kind")
            if "apiVersion" in obj:
                summary["apiVersion"] = obj.get("apiVersion")
        return summary
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def collect(root: Path) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"root": str(root), "files": {}, "warnings": [], "counts": {}}

    for rel in KEY_FILES:
        summary["files"][rel] = file_info(root / rel)

    summary["counts"]["myapp_py"] = sum(1 for _ in root.glob("myapp/**/*.py"))
    summary["counts"]["job_template_readmes"] = sum(1 for _ in root.glob("job-template/job/*/README.md"))
    summary["counts"]["image_dockerfiles"] = sum(1 for _ in root.glob("images/**/Dockerfile*"))
    summary["counts"]["k8s_manifests"] = sum(1 for _ in root.glob("install/kubernetes/**/*.[yY][aA][mM][lL]"))

    for placeholder in ["myapp/config.py", "myapp/project.py"]:
        info = summary["files"][placeholder]
        if info.get("exists") and info.get("is_empty"):
            summary["warnings"].append(f"{placeholder} is empty; runtime overlays are expected")

    package_jsons = [root / "myapp/frontend/package.json", root / "myapp/vision/package.json", root / "myapp/visionPlus/package.json"]
    summary["packages"] = {}
    for path in package_jsons:
        if path.exists():
            summary["packages"][str(path.relative_to(root))] = file_info(path)

    compose = root / "install/docker/docker-compose.yml"
    if compose.exists():
        summary["compose"] = yaml_summary(compose)

    for path in sorted((root / "myapp/init").glob("*.json")):
        summary.setdefault("seed_json", {})[path.name] = file_info(path)

    return summary


def print_text(summary: Dict[str, Any]) -> None:
    print(f"CubeStudio static check: {summary['root']}")
    for rel, info in summary["files"].items():
        status = "missing"
        if info.get("exists"):
            status = f"present size={info['size']}"
            if info.get("is_empty"):
                status += " empty"
        print(f"- {rel}: {status}")
    print("counts:")
    for key, value in summary["counts"].items():
        print(f"- {key}: {value}")
    if summary.get("packages"):
        print("package_json:")
        for rel, info in summary["packages"].items():
            print(f"- {rel}: scripts={info.get('scripts', [])}")
    if summary.get("compose"):
        print(f"compose: {summary['compose']}")
    if summary.get("warnings"):
        print("warnings:")
        for warning in summary["warnings"]:
            print(f"- {warning}")
    if summary.get("seed_json"):
        print("seed_json:")
        for rel, info in summary["seed_json"].items():
            msg = info.get("json_type", "unknown")
            if info.get("json_len") is not None:
                msg += f" len={info['json_len']}"
            print(f"- {rel}: {msg}")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="CubeStudio checkout or manifest directory to inspect")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    summary = collect(root)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
