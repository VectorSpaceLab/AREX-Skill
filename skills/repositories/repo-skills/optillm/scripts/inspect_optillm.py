#!/usr/bin/env python3
"""Inspect an installed OptiLLM package without making provider calls.

Examples:
  python inspect_optillm.py
  python inspect_optillm.py --plugins --backend --json
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any

APPROACH_TARGETS = {
    "mcts": "optillm.mcts:chat_with_mcts",
    "bon": "optillm.bon:best_of_n_sampling",
    "moa": "optillm.moa:mixture_of_agents",
    "rto": "optillm.rto:round_trip_optimization",
    "self_consistency": "optillm.self_consistency:advanced_self_consistency_approach",
    "pvg": "optillm.pvg:inference_time_pv_game",
    "cot_reflection": "optillm.cot_reflection:cot_reflection",
    "plansearch": "optillm.plansearch:plansearch",
    "leap": "optillm.leap:leap",
    "re2": "optillm.reread:re2_approach",
    "cepo": "optillm.cepo.cepo:cepo",
    "mars": "optillm.mars:multi_agent_reasoning_system",
}


def _load_object(target: str) -> Any:
    module_name, object_name = target.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def inspect_core(include_signatures: bool) -> dict[str, Any]:
    import optillm
    import optillm.server as server

    result: dict[str, Any] = {
        "version": getattr(optillm, "__version__", None),
        "known_approaches": list(server.known_approaches),
        "server_defaults": dict(server.server_config),
        "provider_env_set": {
            name: bool(os.environ.get(name))
            for name in [
                "OPTILLM_API_KEY",
                "OPENAI_API_KEY",
                "CEREBRAS_API_KEY",
                "AZURE_OPENAI_API_KEY",
                "AZURE_API_VERSION",
                "AZURE_API_BASE",
            ]
        },
        "parse_examples": {},
    }
    for sample in [
        "moa-gpt-4o-mini",
        "bon|moa|mcts-gpt-4o-mini",
        "cot_reflection&moa-gpt-4o-mini",
        "auto",
    ]:
        result["parse_examples"][sample] = server.parse_combined_approach(
            sample, server.known_approaches, {}
        )
    if include_signatures:
        result["signatures"] = {}
        for slug, target in APPROACH_TARGETS.items():
            try:
                result["signatures"][slug] = str(inspect.signature(_load_object(target)))
            except Exception as exc:  # pragma: no cover - diagnostic path
                result["signatures"][slug] = f"ERROR: {type(exc).__name__}: {exc}"
    return result


def inspect_plugins() -> dict[str, Any]:
    import optillm.server as server

    errors: list[str] = []
    try:
        server.load_plugins()
    except Exception as exc:  # load_plugins normally catches per-plugin errors
        errors.append(f"load_plugins raised {type(exc).__name__}: {exc}")
    plugins = {}
    for slug, func in sorted(server.plugin_approaches.items()):
        try:
            plugins[slug] = str(inspect.signature(func))
        except Exception as exc:
            plugins[slug] = f"ERROR: {type(exc).__name__}: {exc}"
    return {"plugins": plugins, "errors": errors}


def inspect_backend() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        import torch

        out["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "mps_available": bool(
                getattr(getattr(torch, "backends", None), "mps", None)
                and torch.backends.mps.is_available()
            ),
        }
        if torch.cuda.is_available():
            out["torch"]["cuda_device_0"] = torch.cuda.get_device_name(0)
            out["torch"]["cuda_capability_0"] = torch.cuda.get_device_capability(0)
    except Exception as exc:
        out["torch_error"] = f"{type(exc).__name__}: {exc}"
    for module in ["transformers", "peft", "bitsandbytes", "mlx", "mlx_lm"]:
        try:
            mod = importlib.import_module(module)
            out[module] = {"imported": True, "version": getattr(mod, "__version__", None)}
        except Exception as exc:
            out[module] = {"imported": False, "error": f"{type(exc).__name__}: {exc}"}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect OptiLLM without provider calls")
    parser.add_argument("--plugins", action="store_true", help="Load and list plugin slugs/signatures")
    parser.add_argument("--backend", action="store_true", help="Probe local inference backend imports")
    parser.add_argument("--signatures", action="store_true", help="Include core approach signatures")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text")
    args = parser.parse_args()

    result: dict[str, Any] = {"core": inspect_core(args.signatures)}
    if args.plugins:
        result["plugins"] = inspect_plugins()
    if args.backend:
        result["backend"] = inspect_backend()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"OptiLLM version: {result['core']['version']}")
        print("Known approaches: " + ", ".join(result["core"]["known_approaches"]))
        print("Provider env set:")
        for key, value in result["core"]["provider_env_set"].items():
            print(f"  {key}: {value}")
        print("Parse examples:")
        for sample, parsed in result["core"]["parse_examples"].items():
            print(f"  {sample!r} -> {parsed}")
        if "plugins" in result:
            print("Plugins: " + ", ".join(result["plugins"]["plugins"].keys()))
        if "backend" in result:
            print("Backend:")
            for key, value in result["backend"].items():
                print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
