#!/usr/bin/env python3
"""Safe Petals environment checker."""
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import inspect
import io
import json
import sys


def rec(out, key, status, **extra):
    out.setdefault("checks", {})[key] = {"status": status, **extra}


def check_metadata(out):
    try:
        rec(out, "metadata", "ok", version=metadata.version("petals"), requirements=metadata.requires("petals") or [])
    except Exception as exc:
        rec(out, "metadata", "error", error=repr(exc))


def check_imports(out):
    try:
        before = "bitsandbytes" in sys.modules
        import petals
        from petals import (  # noqa: F401
            AutoDistributedConfig,
            AutoDistributedModelForCausalLM,
            AutoDistributedModelForSequenceClassification,
            AutoDistributedSpeculativeModel,
            InferenceSession,
            RemoteSequential,
        )

        rec(
            out,
            "public_imports",
            "ok",
            petals_version=getattr(petals, "__version__", None),
            bitsandbytes_imported_before=before,
            bitsandbytes_imported_after="bitsandbytes" in sys.modules,
        )
    except Exception as exc:
        rec(out, "public_imports", "error", error=repr(exc))


def check_api(out):
    try:
        from petals import AutoDistributedConfig, AutoDistributedModelForCausalLM, RemoteSequential
        from petals.client.config import ClientConfig
        from petals.server.from_pretrained import load_pretrained_block
        from petals.utils.convert_block import QuantType

        rec(
            out,
            "api_signatures",
            "ok",
            signatures={
                "AutoDistributedConfig.from_pretrained": str(inspect.signature(AutoDistributedConfig.from_pretrained)),
                "AutoDistributedModelForCausalLM.from_pretrained": str(
                    inspect.signature(AutoDistributedModelForCausalLM.from_pretrained)
                ),
                "RemoteSequential.__init__": str(inspect.signature(RemoteSequential.__init__)),
                "RemoteSequential.forward": str(inspect.signature(RemoteSequential.forward)),
                "load_pretrained_block": str(inspect.signature(load_pretrained_block)),
            },
            client_config_fields=sorted(ClientConfig.__dataclass_fields__),
            quant_types=[q.name.lower() for q in QuantType],
        )
    except Exception as exc:
        rec(out, "api_signatures", "error", error=repr(exc))


def cli_help(module_name):
    try:
        mod = importlib.import_module(module_name)
        old = sys.argv[:]
        buf = io.StringIO()
        try:
            sys.argv = [module_name.rsplit(".", 1)[-1], "--help"]
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    mod.main()
                except SystemExit as exc:
                    if isinstance(exc.code, int) and exc.code not in (0,):
                        return {"status": "error", "exit_code": exc.code, "excerpt": buf.getvalue()[:800]}
        finally:
            sys.argv = old
        text = buf.getvalue()
        return {"status": "ok", "usage_seen": "usage:" in text.lower(), "excerpt": text[:800]}
    except Exception as exc:
        return {"status": "error", "error": repr(exc)}


def check_cli(out):
    data = {"run_server": cli_help("petals.cli.run_server"), "run_dht": cli_help("petals.cli.run_dht")}
    rec(
        out,
        "cli_help",
        "ok" if all(v.get("status") == "ok" and v.get("usage_seen") for v in data.values()) else "error",
        commands=data,
    )


def check_torch(out, cuda=False):
    try:
        import torch

        data = {
            "torch_version": torch.__version__,
            "torch_cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        }
        if cuda and torch.cuda.is_available():
            x = torch.empty((1,), device="cuda")
            data.update(
                cuda_device_name_0=torch.cuda.get_device_name(0),
                cuda_device_capability_0=torch.cuda.get_device_capability(0),
                cuda_tensor={"device": x.device.type, "numel": x.numel()},
            )
        rec(out, "torch_backend", "ok", **data)
    except Exception as exc:
        rec(out, "torch_backend", "error", error=repr(exc))


def check_bnb(out):
    try:
        import bitsandbytes  # noqa: F401

        rec(out, "bitsandbytes", "ok", imported=True)
    except Exception as exc:
        rec(
            out,
            "bitsandbytes",
            "warning",
            imported=False,
            error=repr(exc),
            note="Optional for base client/server planning; required for verified quantized/adapted server paths.",
        )


def main():
    parser = argparse.ArgumentParser(description="Check local Petals package health without contacting swarms by default.")
    parser.add_argument("--check-cuda", action="store_true")
    parser.add_argument("--check-bitsandbytes", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    out = {"schema": "petals.environment-check.v1", "network_or_service_side_effects": False, "model_weight_downloads": False}
    check_metadata(out)
    check_imports(out)
    check_api(out)
    check_cli(out)
    check_torch(out, args.check_cuda)
    if args.check_bitsandbytes:
        check_bnb(out)
    required = ["metadata", "public_imports", "api_signatures", "cli_help", "torch_backend"]
    out["status"] = "error" if any(out["checks"].get(k, {}).get("status") == "error" for k in required) else "ok"
    print(json.dumps(out, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
