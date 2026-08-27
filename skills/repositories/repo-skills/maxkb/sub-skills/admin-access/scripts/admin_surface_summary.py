#!/usr/bin/env python3
"""Static summary of MaxKB admin and automation surfaces."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]
SURFACE_FILES = {
    "users": REPO_ROOT / "apps" / "users" / "urls.py",
    "system_manage": REPO_ROOT / "apps" / "system_manage" / "urls.py",
    "folders": REPO_ROOT / "apps" / "folders" / "urls.py",
    "homepage": REPO_ROOT / "apps" / "homepage" / "urls.py",
    "oss": REPO_ROOT / "apps" / "oss" / "urls.py",
    "tools": REPO_ROOT / "apps" / "tools" / "urls.py",
    "trigger": REPO_ROOT / "apps" / "trigger" / "urls.py",
}


def extract_paths(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [m.group(2) for m in re.finditer(r"path\((['\"])(.*?)\1", text)]


def main() -> int:
    report = {name: extract_paths(path) for name, path in SURFACE_FILES.items()}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
