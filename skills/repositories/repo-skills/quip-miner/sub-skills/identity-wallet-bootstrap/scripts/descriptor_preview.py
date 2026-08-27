#!/usr/bin/env python3
"""Preview a quip-miner NodeDescriptor from a backend config without submitting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared.miner_config import load_backend_config, load_toml
from shared.miner_core import build_miner_specs
from shared.system_info import build_descriptor, to_canonical_json, validate_descriptor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--miner-config", type=Path, help="Config whose backend sections populate descriptor miners.")
    parser.add_argument("--node-id", default="quip-miner-preview")
    parser.add_argument("--node-name", required=True)
    parser.add_argument("--public-host")
    parser.add_argument("--public-port", type=int)
    parser.add_argument("--rpc-endpoint", action="append", default=[])
    parser.add_argument("--auto-mine", action="store_true")
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    parser.add_argument("--include-system-info", action="store_true", help="Probe local system info; off by default for side-effect-light preview.")
    args = parser.parse_args()

    specs = []
    if args.miner_config:
        raw = load_toml(args.miner_config)
        backends = load_backend_config(args.miner_config, raw=raw)
        specs = build_miner_specs(args.node_id, backends)

    desc = build_descriptor(
        node_id=args.node_id,
        node_name=args.node_name,
        public_host=args.public_host,
        public_port=args.public_port,
        rpc_endpoints=args.rpc_endpoint,
        auto_mine=args.auto_mine,
        log_level=args.log_level,
        miner_specs=specs,
        include_system_info=args.include_system_info,
    )
    validate_descriptor(desc)
    print(to_canonical_json(desc).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
