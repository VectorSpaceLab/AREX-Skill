#!/usr/bin/env python3
"""Inspect a quip-miner TOML config without starting miners."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from shared.miner_config import (
    MinerConfigError,
    load_backend_config,
    load_miner_config,
    load_submission_config,
    load_toml,
    mempool_owner_group,
    present_backend_groups,
    resolve_modes,
)


def inspect_config(path: Path, *, default: str | None = None, image_supports: list[str] | None = None) -> dict[str, Any]:
    raw = load_toml(path)
    miner = load_miner_config(path, raw=raw)
    backends = load_backend_config(path, raw=raw)
    submission = load_submission_config(path, raw=raw)
    modes = resolve_modes(backends, default=default, image_supports=image_supports)
    return {
        "config": str(path),
        "miner_keys": sorted(miner.keys()),
        "backend_sections": sorted(backends.keys()),
        "backend_groups": present_backend_groups(backends),
        "resolved_modes": modes,
        "mempool_owner_group": mempool_owner_group(backends),
        "validators_count": len(miner.get("validators", []) or []),
        "rest_host": miner.get("rest_host"),
        "rest_port": miner.get("rest_port"),
        "signer_key_set": bool(miner.get("signer_key")),
        "submission": {
            "tip_plancks": submission.tip_plancks,
            "max_retries": submission.max_retries,
            "retry_backoff_ms": submission.retry_backoff_ms,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="quip-miner TOML file to inspect.")
    parser.add_argument("--default", choices=("cpu", "gpu", "qpu"), help="Default mode when no backend section exists.")
    parser.add_argument("--image-supports", help="Comma-separated subset of cpu,gpu,qpu supported by this image.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary.")
    args = parser.parse_args()
    image_supports = None
    if args.image_supports:
        image_supports = [part.strip() for part in args.image_supports.split(",") if part.strip()]
    try:
        result = inspect_config(args.config, default=args.default, image_supports=image_supports)
    except (MinerConfigError, ValueError) as exc:
        print(f"CONFIG_ERROR: {exc}")
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Config: {result['config']}")
        print(f"Backend sections: {', '.join(result['backend_sections']) or '(none)'}")
        print(f"Resolved modes: {', '.join(result['resolved_modes'])}")
        print(f"Mempool owner group: {result['mempool_owner_group'] or '(none)'}")
        print(f"Validators: {result['validators_count']} configured")
        print(f"Telemetry: {result['rest_host'] or '(default)'}:{result['rest_port'] or '(default/off)'}")
        print(f"Signer key configured: {result['signer_key_set']}")
        print(f"Submission: {result['submission']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
