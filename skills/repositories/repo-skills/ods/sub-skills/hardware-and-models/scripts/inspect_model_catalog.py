#!/usr/bin/env python3
"""Read-only ODS model catalog, backend contract, and hardware class summary.

The script accepts either an ODS source root (containing ``config/``) or a
project root that contains ``ods/config/``. It never writes files, downloads
artifacts, starts Docker, or imports ODS runtime code.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any


KNOWN_CONFIG_REL = Path("config/model-library.json")


def resolve_ods_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if (root / KNOWN_CONFIG_REL).is_file():
        return root
    if (root / "ods" / KNOWN_CONFIG_REL).is_file():
        return root / "ods"
    raise SystemExit(
        f"error: {root} is not an ODS root and does not contain ods/{KNOWN_CONFIG_REL}"
    )


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: invalid JSON in {path}: {exc}") from exc


def artifact_count(model: dict[str, Any]) -> int:
    parts = model.get("gguf_parts")
    if isinstance(parts, list) and parts:
        return len([part for part in parts if isinstance(part, dict)])
    if model.get("gguf_file") or model.get("gguf"):
        return 1
    return 0


def has_download_url(model: dict[str, Any]) -> bool:
    parts = model.get("gguf_parts")
    if isinstance(parts, list) and parts:
        return all(isinstance(part, dict) and bool(part.get("url")) for part in parts)
    return bool(model.get("gguf_url"))


def has_sha(model: dict[str, Any]) -> bool:
    parts = model.get("gguf_parts")
    if isinstance(parts, list) and parts:
        return all(isinstance(part, dict) and len(str(part.get("sha256") or "")) == 64 for part in parts)
    return len(str(model.get("gguf_sha256") or "")) == 64


def summarize_catalog(ods_root: Path) -> dict[str, Any]:
    path = ods_root / "config" / "model-library.json"
    data = load_json(path) or {}
    models = [model for model in data.get("models", []) if isinstance(model, dict)]
    families = collections.Counter(str(model.get("family") or "<missing>") for model in models)
    specialties = collections.Counter(str(model.get("specialty") or "<missing>") for model in models)
    install_disabled = [model for model in models if model.get("install_recommendation") is False]
    runtime_profile_models = [model for model in models if isinstance(model.get("runtime_profiles"), list) and model.get("runtime_profiles")]
    missing_url = [model.get("id") for model in models if artifact_count(model) and not has_download_url(model)]
    missing_sha = [model.get("id") for model in models if artifact_count(model) and not has_sha(model)]
    largest = sorted(
        models,
        key=lambda model: float(model.get("size_mb") or 0),
        reverse=True,
    )[:8]
    compatibility = collections.Counter()
    for model in models:
        compat = model.get("app_compatibility")
        if not isinstance(compat, dict):
            continue
        for app, verdict in compat.items():
            if isinstance(verdict, dict):
                compatibility[f"{app}:{verdict.get('status', '<missing>')}"] += 1
            else:
                compatibility[f"{app}:{verdict}"] += 1
    return {
        "path": str(path),
        "version": data.get("version"),
        "model_count": len(models),
        "families": dict(sorted(families.items())),
        "specialties": dict(sorted(specialties.items())),
        "install_recommendation_false": [model.get("id") for model in install_disabled],
        "runtime_profile_models": [model.get("id") for model in runtime_profile_models],
        "missing_download_url": [item for item in missing_url if item],
        "missing_or_short_sha256": [item for item in missing_sha if item],
        "largest_models": [
            {
                "id": model.get("id"),
                "size_mb": model.get("size_mb"),
                "vram_required_gb": model.get("vram_required_gb"),
                "context_length": model.get("context_length"),
            }
            for model in largest
        ],
        "compatibility_status_counts": dict(sorted(compatibility.items())),
    }


def summarize_backends(ods_root: Path) -> list[dict[str, Any]]:
    backend_dir = ods_root / "config" / "backends"
    rows: list[dict[str, Any]] = []
    for path in sorted(backend_dir.glob("*.json")):
        data = load_json(path) or {}
        runtime = data.get("runtime") if isinstance(data.get("runtime"), dict) else {}
        lemonade = runtime.get("lemonade") if isinstance(runtime.get("lemonade"), dict) else {}
        rows.append(
            {
                "file": str(path),
                "id": data.get("id"),
                "llm_engine": data.get("llm_engine"),
                "service_name": data.get("service_name"),
                "public_api_port": data.get("public_api_port"),
                "public_health_url": data.get("public_health_url"),
                "provider_name": data.get("provider_name"),
                "provider_url": data.get("provider_url"),
                "lemonade": {
                    key: lemonade.get(key)
                    for key in (
                        "container_image",
                        "windows_version",
                        "api_port",
                        "health_path",
                        "linux_backend",
                        "windows_backend",
                    )
                    if lemonade.get(key) is not None
                },
            }
        )
    return rows


def summarize_hardware_classes(ods_root: Path) -> dict[str, Any]:
    candidates = [
        ods_root / "config" / "hardware-classes.json",
        ods_root / "config" / "gpu-database.json",
    ]
    summary: dict[str, Any] = {}
    hardware = load_json(candidates[0])
    if isinstance(hardware, dict):
        classes = [item for item in hardware.get("classes", []) if isinstance(item, dict)]
        by_backend = collections.Counter(
            str((item.get("recommended") or {}).get("backend") or "<missing>")
            for item in classes
        )
        by_tier = collections.Counter(
            str((item.get("recommended") or {}).get("tier") or "<missing>")
            for item in classes
        )
        summary["hardware_classes"] = {
            "path": str(candidates[0]),
            "version": hardware.get("version"),
            "count": len(classes),
            "by_backend": dict(sorted(by_backend.items())),
            "by_tier": dict(sorted(by_tier.items())),
            "classes": [
                {
                    "id": item.get("id"),
                    "label": item.get("label"),
                    "match": item.get("match"),
                    "recommended": item.get("recommended"),
                }
                for item in classes
            ],
        }
    gpu_db = load_json(candidates[1])
    if isinstance(gpu_db, dict):
        heuristics = [item for item in gpu_db.get("heuristic_classes", []) if isinstance(item, dict)]
        known = [item for item in gpu_db.get("known_gpus", []) if isinstance(item, dict)]
        heuristic_tiers = collections.Counter(
            str((item.get("recommended") or {}).get("tier") or "<missing>")
            for item in heuristics
        )
        summary["gpu_database"] = {
            "path": str(candidates[1]),
            "schema_version": gpu_db.get("schema_version"),
            "known_gpu_count": len(known),
            "heuristic_class_count": len(heuristics),
            "heuristic_tiers": dict(sorted(heuristic_tiers.items())),
        }
    return summary


def text_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"ODS root: {payload['ods_root']}")
    catalog = payload["catalog"]
    lines.append("")
    lines.append("Model catalog")
    lines.append(f"  version: {catalog.get('version')}")
    lines.append(f"  models: {catalog.get('model_count')}")
    lines.append("  families: " + ", ".join(f"{k}={v}" for k, v in catalog.get("families", {}).items()))
    if catalog.get("runtime_profile_models"):
        lines.append("  runtime profiles: " + ", ".join(catalog["runtime_profile_models"]))
    if catalog.get("install_recommendation_false"):
        lines.append("  install_recommendation=false: " + ", ".join(catalog["install_recommendation_false"]))
    if catalog.get("missing_download_url"):
        lines.append("  models with artifacts but missing URL: " + ", ".join(catalog["missing_download_url"]))
    if catalog.get("missing_or_short_sha256"):
        lines.append("  models with missing/short SHA256: " + ", ".join(catalog["missing_or_short_sha256"]))
    lines.append("  largest models:")
    for item in catalog.get("largest_models", []):
        lines.append(
            "    - {id}: size_mb={size_mb}, vram_required_gb={vram_required_gb}, context={context_length}".format(**item)
        )

    lines.append("")
    lines.append("Backend contracts")
    for backend in payload.get("backends", []):
        lines.append(
            "  - {id}: engine={llm_engine}, service={service_name}, port={public_api_port}, provider={provider_name}".format(**backend)
        )
        if backend.get("lemonade"):
            lem = backend["lemonade"]
            lines.append(
                "      lemonade: linux={linux_backend}, windows={windows_backend}, image={container_image}".format(
                    linux_backend=lem.get("linux_backend", ""),
                    windows_backend=lem.get("windows_backend", ""),
                    container_image=lem.get("container_image", ""),
                )
            )

    hw = payload.get("hardware", {})
    if hw.get("hardware_classes"):
        classes = hw["hardware_classes"]
        lines.append("")
        lines.append("Hardware classes")
        lines.append(f"  count: {classes.get('count')}")
        lines.append("  by backend: " + ", ".join(f"{k}={v}" for k, v in classes.get("by_backend", {}).items()))
        lines.append("  by tier: " + ", ".join(f"{k}={v}" for k, v in classes.get("by_tier", {}).items()))
    if hw.get("gpu_database"):
        db = hw["gpu_database"]
        lines.append("")
        lines.append("GPU database")
        lines.append(f"  known GPUs: {db.get('known_gpu_count')}")
        lines.append(f"  heuristic classes: {db.get('heuristic_class_count')}")
    lines.append("")
    lines.append("Read-only summary complete; no files were modified.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="ODS source root or project root containing ods/ (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    ods_root = resolve_ods_root(args.root)
    payload = {
        "ods_root": str(ods_root),
        "catalog": summarize_catalog(ods_root),
        "backends": summarize_backends(ods_root),
        "hardware": summarize_hardware_classes(ods_root),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(text_report(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
