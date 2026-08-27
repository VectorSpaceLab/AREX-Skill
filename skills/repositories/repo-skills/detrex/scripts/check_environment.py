#!/usr/bin/env python3
"""Safe detrex environment checker.

This script performs import/config/backend/tool-help checks only. It does not
download models or data, train, evaluate, register datasets, or run benchmarks.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import traceback
from importlib import metadata
from typing import Any, Dict, Iterable, List


IMPORTS = [
    "torch",
    "torchvision",
    "detectron2",
    "detrex",
    "detrex.layers",
    "detrex.modeling",
    "detrex.config",
    "detrex.data",
    "detrex.checkpoint",
    "detrex.utils",
]

TOOL_MODULES = {
    "train": "tools.train_net",
    "hydra": "tools.hydra_train_net",
    "analyze": "tools.analyze_model",
    "benchmark": "tools.benchmark",
    "visualize-data": "tools.visualize_data",
    "visualize-json": "tools.visualize_json_results",
    "demo": "demo.demo",
}


def import_check(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": getattr(module, "__version__", None)}
    except BaseException as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def dist_version(name: str) -> Dict[str, Any]:
    try:
        return {"ok": True, "version": metadata.version(name)}
    except BaseException as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def torch_backend_check() -> Dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
        out: Dict[str, Any] = {
            "ok": True,
            "torch_version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            try:
                out["cuda_device_name_0"] = torch.cuda.get_device_name(0)
                out["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                out["cuda_tensor_allocation"] = "passed"
            except BaseException as exc:
                out["cuda_tensor_allocation"] = f"failed: {type(exc).__name__}: {exc}"
                out["ok"] = False
        return out
    except BaseException as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cuda_extension_check() -> Dict[str, Any]:
    out: Dict[str, Any] = {"requested": True}
    try:
        ext = importlib.import_module("detrex._C")
        symbols = ["ms_deform_attn_forward", "ms_deform_attn_backward"]
        out["import_ok"] = True
        out["symbols"] = {name: hasattr(ext, name) for name in symbols}
        out["ok"] = all(out["symbols"].values())
    except BaseException as exc:
        out.update({"import_ok": False, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return out


def config_check(config_name: str) -> Dict[str, Any]:
    try:
        cfg_mod = importlib.import_module("detrex.config")
        cfg = cfg_mod.get_config(config_name)
        keys = list(cfg.keys()) if hasattr(cfg, "keys") else []
        return {"ok": True, "config": config_name, "top_level_keys": keys}
    except BaseException as exc:
        return {"ok": False, "config": config_name, "error": f"{type(exc).__name__}: {exc}"}


def tool_help_check(tool: str, timeout: int, repo_root: str = "") -> Dict[str, Any]:
    module = TOOL_MODULES[tool]
    try:
        proc = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            cwd=repo_root or None,
        )
        return {
            "ok": proc.returncode == 0,
            "module": module,
            "cwd": repo_root or None,
            "exit_code": proc.returncode,
            "stdout_head": proc.stdout.splitlines()[:8],
            "stderr_head": proc.stderr.splitlines()[:8],
        }
    except BaseException as exc:
        return {"ok": False, "module": module, "error": f"{type(exc).__name__}: {exc}"}


def tiny_cpu_check() -> Dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
        layers = importlib.import_module("detrex.layers")
        losses = importlib.import_module("detrex.modeling.losses")
        mask = torch.zeros(1, 4, 5, dtype=torch.bool)
        pos = layers.PositionEmbeddingSine(num_pos_feats=8, normalize=True)(mask)
        ffn = layers.FFN(embed_dim=16, feedforward_dim=32, output_dim=16, num_fcs=2)
        ffn_out = ffn(torch.randn(2, 3, 16))
        focal = losses.FocalLoss(activated=False)
        loss = focal(torch.randn(4, 3), torch.tensor([0, 1, 2, 1]), avg_factor=2)
        return {
            "ok": True,
            "position_embedding_shape": list(pos.shape),
            "ffn_shape": list(ffn_out.shape),
            "focal_loss_scalar": float(loss.detach().cpu()),
        }
    except BaseException as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=3),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check detrex imports, package metadata, optional CUDA extension, config resources, and tool help.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="emit full JSON report")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if any requested check fails")
    parser.add_argument("--check-cuda-extension", action="store_true", help="check detrex._C deformable-attention symbols")
    parser.add_argument("--check-config", default="", metavar="RESOURCE", help="packaged detrex config such as common/train.py")
    parser.add_argument("--tiny-cpu", action="store_true", help="run tiny CPU layer/loss checks")
    parser.add_argument(
        "--tool-help",
        nargs="*",
        choices=sorted(TOOL_MODULES),
        default=[],
        help="run --help for selected installed detrex tool modules",
    )
    parser.add_argument("--tool-timeout", type=int, default=20, help="seconds per tool-help check")
    parser.add_argument(
        "--repo-root",
        default="",
        help="optional detrex source checkout to use as cwd for tool --help subprocesses; useful for Hydra configs/hydra validation",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: Dict[str, Any] = {
        "imports": {name: import_check(name) for name in IMPORTS},
        "distributions": {name: dist_version(name) for name in ["detrex", "detectron2", "torch", "torchvision"]},
        "torch_backend": torch_backend_check(),
        "checks": {},
    }
    if args.check_cuda_extension:
        report["checks"]["cuda_extension"] = cuda_extension_check()
    if args.check_config:
        report["checks"]["config"] = config_check(args.check_config)
    if args.tiny_cpu:
        report["checks"]["tiny_cpu"] = tiny_cpu_check()
    if args.tool_help:
        report["checks"]["tool_help"] = {
            tool: tool_help_check(tool, args.tool_timeout, args.repo_root) for tool in args.tool_help
        }

    failures: List[str] = []
    for group, values in report.items():
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, dict) and value.get("ok") is False:
                    failures.append(f"{group}.{key}")
                if key == "tool_help" and isinstance(value, dict):
                    for tool, tool_result in value.items():
                        if isinstance(tool_result, dict) and tool_result.get("ok") is False:
                            failures.append(f"tool_help.{tool}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        ok_imports = sum(1 for value in report["imports"].values() if value.get("ok"))
        print(f"imports: {ok_imports}/{len(report['imports'])} ok")
        print(f"torch backend: {'ok' if report['torch_backend'].get('ok') else 'failed'}")
        for name, result in report["checks"].items():
            if name == "tool_help":
                passed = sum(1 for value in result.values() if value.get("ok"))
                print(f"tool_help: {passed}/{len(result)} ok")
            else:
                print(f"{name}: {'ok' if result.get('ok') else 'failed'}")
        if failures:
            print("failures:")
            for failure in failures:
                print(f"- {failure}")
        else:
            print("failures: none")

    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
