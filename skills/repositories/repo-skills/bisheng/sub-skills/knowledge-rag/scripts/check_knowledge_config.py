#!/usr/bin/env python3
"""Check BiSheng knowledge config key presence without connecting to services."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

KEYS = [
    "knowledge",
    "loader_provider",
    "etl4lm",
    "mineru",
    "paddle_ocr",
    "vector_stores",
    "milvus",
    "elasticsearch",
    "object_storage",
    "minio",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BiSheng knowledge config key presence.")
    parser.add_argument("--config", required=True, help="config YAML/text file to scan")
    args = parser.parse_args()
    path = Path(args.config)
    text = path.read_text(encoding="utf-8", errors="replace")
    print(f"knowledge config scan: {path}")
    findings = {}
    for key in KEYS:
        found = re.search(rf"(?m)^\s*{re.escape(key)}\s*:", text) is not None
        findings[key] = found
        print(f"{key:20} {'present' if found else 'missing'}")
    providers = [k for k in ("etl4lm", "mineru", "paddle_ocr") if findings[k]]
    print("providers_declared:", ", ".join(providers) if providers else "none")
    if not findings["knowledge"]:
        print("knowledge_section: not declared in this file; BiSheng may be relying on defaults or DB/env overrides")
    if findings["object_storage"] and findings["minio"]:
        print("object_storage_minio: present")
    print("note: this checker does not validate credentials, URLs, service reachability, or DB/Redis overrides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
