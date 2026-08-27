#!/usr/bin/env python3
"""Static check for the MaxKB frontend build and routing contract."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]
PACKAGE_JSON = REPO_ROOT / "ui" / "package.json"
VITE_CONFIG = REPO_ROOT / "ui" / "vite.config.ts"
ROUTER = REPO_ROOT / "ui" / "src" / "router" / "routes.ts"
CHAT_ROUTER = REPO_ROOT / "ui" / "src" / "router" / "chat" / "routes.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_simple(pattern: str, text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(pattern, text)]


def first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def main() -> int:
    package = json.loads(read(PACKAGE_JSON) or "{}")
    vite_text = read(VITE_CONFIG)
    router_text = read(ROUTER)
    chat_router_text = read(CHAT_ROUTER)
    proxy_targets = [t for t in extract_simple(r"target:\s*'([^']+)'", vite_text) if t.startswith("http")]
    route_paths = extract_simple(r"path:\s*['\"]([^'\"]+)['\"]", router_text)
    chat_paths = extract_simple(r"path:\s*['\"]([^'\"]+)['\"]", chat_router_text)
    report = {
        "scripts": sorted((package.get("scripts") or {}).keys()),
        "vite": {
            "base": first_match(r"base:\s*'([^']+)'", vite_text),
            "outDir": first_match(r"outDir:\s*`([^`]+)`", vite_text),
            "proxy_targets": sorted(set(proxy_targets)),
        },
        "admin_routes": route_paths[:40],
        "chat_routes": chat_paths[:40],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
