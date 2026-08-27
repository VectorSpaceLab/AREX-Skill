#!/usr/bin/env python3
"""Static knowledge + model surface summary for MaxKB."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]
KNOWLEDGE_URLS = REPO_ROOT / "apps" / "knowledge" / "urls.py"
MODEL_URLS = REPO_ROOT / "apps" / "models_provider" / "urls.py"
MODEL_IMPL_ROOT = REPO_ROOT / "apps" / "models_provider" / "impl"
LOCAL_MODEL_URLS = REPO_ROOT / "apps" / "local_model" / "urls.py"
LOCAL_MODEL_PROVIDER = REPO_ROOT / "apps" / "models_provider" / "impl" / "local_model_provider" / "local_model_provider.py"


def extract_paths(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [m.group(2) for m in re.finditer(r"path\((['\"])(.*?)\1", text)]


def extract_local_models(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    models: list[dict[str, str]] = []
    for match in re.finditer(r"ModelInfo\('([^']+)'\s*,\s*''\s*,\s*ModelTypeConst\.([A-Z_]+)", text):
        models.append({"name": match.group(1), "type": match.group(2)})
    return models


def main() -> int:
    provider_dirs = sorted([p.name for p in MODEL_IMPL_ROOT.iterdir() if p.is_dir() and not p.name.startswith("__")]) if MODEL_IMPL_ROOT.exists() else []
    report = {
        "knowledge_routes": extract_paths(KNOWLEDGE_URLS),
        "model_routes": extract_paths(MODEL_URLS),
        "local_model_routes": extract_paths(LOCAL_MODEL_URLS),
        "provider_dirs": provider_dirs,
        "local_model_defaults": extract_local_models(LOCAL_MODEL_PROVIDER),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
