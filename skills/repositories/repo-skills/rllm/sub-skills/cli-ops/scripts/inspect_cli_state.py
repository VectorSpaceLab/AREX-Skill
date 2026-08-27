#!/usr/bin/env python3
"""Read-only redacted summary of rLLM CLI state files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {"api_key", "token", "secret", "password", "authorization"}


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                out[k] = "<redacted>" if v else v
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return redact(json.loads(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=None, help="Override rLLM home (default: RLLM_HOME or ~/.rllm)")
    args = parser.parse_args()
    home = args.home or Path(os.environ.get("RLLM_HOME", "~/.rllm")).expanduser()
    files = ["config.json", "agents.json", "evaluators.json", "snapshots.json"]
    report = {"rllm_home": str(home), "files": {name: load_json(home / name) for name in files}}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
