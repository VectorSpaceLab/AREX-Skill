#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="Check Petals client imports/signatures without network by default.")
    parser.add_argument("--inspect-config")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    out = {"schema": "petals.client-smoke.v1", "network_allowed": args.allow_network, "checks": {}}
    try:
        before = "bitsandbytes" in sys.modules
        import petals
        from petals import AutoDistributedConfig, AutoDistributedModelForCausalLM, RemoteSequential
        from petals.client.config import ClientConfig

        out["checks"]["imports"] = {
            "status": "ok",
            "petals_version": getattr(petals, "__version__", None),
            "bitsandbytes_eager": before or ("bitsandbytes" in sys.modules),
        }
        out["checks"]["signatures"] = {
            "status": "ok",
            "AutoDistributedModelForCausalLM.from_pretrained": str(inspect.signature(AutoDistributedModelForCausalLM.from_pretrained)),
            "RemoteSequential.forward": str(inspect.signature(RemoteSequential.forward)),
            "ClientConfig": sorted(ClientConfig.__dataclass_fields__),
        }
        if args.inspect_config:
            cfg = AutoDistributedConfig.from_pretrained(args.inspect_config, local_files_only=not args.allow_network)
            out["checks"]["config"] = {
                "status": "ok",
                "model_type": getattr(cfg, "model_type", None),
                "dht_prefix": getattr(cfg, "dht_prefix", None),
                "num_hidden_layers": getattr(cfg, "num_hidden_layers", None),
            }
    except Exception as exc:
        out["checks"].setdefault("error", {"status": "error", "error": repr(exc)})
    out["status"] = "error" if any(v.get("status") == "error" for v in out["checks"].values()) else "ok"
    print(json.dumps(out, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
