#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
import sys


def main():
    p = argparse.ArgumentParser(description="Inspect Petals distributed-block imports, signatures, QuantType names, and optional config metadata without loading weights.")
    p.add_argument("--inspect-config")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    out = {"schema": "petals.block-api.v1", "loads_weights": False, "network_allowed": args.allow_network, "checks": {}}
    try:
        from petals import AutoDistributedConfig, RemoteSequential
        from petals.client.inference_session import InferenceSession
        from petals.server.from_pretrained import load_pretrained_block
        from petals.utils.convert_block import QuantType, check_device_balance, convert_block, make_tensor_parallel

        out["checks"]["api"] = {
            "status": "ok",
            "signatures": {
                "RemoteSequential.__init__": str(inspect.signature(RemoteSequential.__init__)),
                "RemoteSequential.forward": str(inspect.signature(RemoteSequential.forward)),
                "InferenceSession.step": str(inspect.signature(InferenceSession.step)),
                "load_pretrained_block": str(inspect.signature(load_pretrained_block)),
                "convert_block": str(inspect.signature(convert_block)),
                "make_tensor_parallel": str(inspect.signature(make_tensor_parallel)),
            },
            "quant_types": [q.name.lower() for q in QuantType],
            "bitsandbytes_imported": "bitsandbytes" in sys.modules,
        }
        if args.inspect_config:
            cfg = AutoDistributedConfig.from_pretrained(args.inspect_config, local_files_only=not args.allow_network)
            out["checks"]["config"] = {
                "status": "ok",
                "model_type": getattr(cfg, "model_type", None),
                "num_hidden_layers": getattr(cfg, "num_hidden_layers", None),
                "dht_prefix": getattr(cfg, "dht_prefix", None),
                "block_prefix": getattr(cfg, "block_prefix", None),
            }
    except Exception as exc:
        out["checks"]["error"] = {"status": "error", "error": repr(exc)}
    out["status"] = "error" if any(v.get("status") == "error" for v in out["checks"].values()) else "ok"
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print("Petals distributed-block API inspection:", out["status"])
        for key, value in out["checks"].items():
            print(key, value)
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
