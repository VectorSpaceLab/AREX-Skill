#!/usr/bin/env python3
"""Inspect a Humanoid-Gym checkout without launching Isaac Gym.

This helper is safe to run from arbitrary working directories. It accepts a
repo root, imports the top-level package, reports package metadata, parses the
XBot-L config source, and optionally checks torch CUDA and asset presence.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, List

CONFIG_RELATIVE = Path("humanoid/envs/custom/humanoid_config.py")
DEFAULT_CHECKS = ["root", "config", "assets", "torch", "cuda"]


def _evaluate(node: ast.AST, env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError("unknown name")
    if isinstance(node, ast.List):
        return [_evaluate(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_evaluate(elt, env) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {_evaluate(k, env): _evaluate(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _evaluate(node.operand, env)
        if isinstance(value, (int, float)):
            return -value
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Pow):
            return left ** right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int" and len(node.args) == 1:
        return int(_evaluate(node.args[0], env))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float" and len(node.args) == 1:
        return float(_evaluate(node.args[0], env))
    raise ValueError("unsupported expression")


def _class_to_dict(class_node: ast.ClassDef) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            try:
                values[stmt.targets[0].id] = _evaluate(stmt.value, values)
            except ValueError:
                continue
        elif isinstance(stmt, ast.ClassDef):
            values[stmt.name] = _class_to_dict(stmt)
    return values


def _load_config(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / CONFIG_RELATIVE
    tree = ast.parse(path.read_text())
    out: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in {"XBotLCfg", "XBotLCfgPPO"}:
            out[node.name] = _class_to_dict(node)
    if "XBotLCfg" not in out or "XBotLCfgPPO" not in out:
        raise RuntimeError("could not locate XBotLCfg and XBotLCfgPPO in config source")
    return out


def _asset_paths(repo_root: Path, cfg: Dict[str, Any]) -> Dict[str, Path]:
    asset_file = cfg["asset"]["file"]
    asset_path = asset_file.replace("{LEGGED_GYM_ROOT_DIR}", str(repo_root))
    return {
        "urdf": Path(asset_path),
        "mjcf_plane": repo_root / "resources/robots/XBot/mjcf/XBot-L.xml",
        "mjcf_terrain": repo_root / "resources/robots/XBot/mjcf/XBot-L-terrain.xml",
        "terrain_png": repo_root / "resources/robots/XBot/terrain/uneven.png",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a Humanoid-Gym checkout without launching Isaac Gym.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, help="Path to the Humanoid-Gym repository root.")
    parser.add_argument("--check", nargs="*", default=DEFAULT_CHECKS, help="Checks to run: root, config, assets, torch, cuda.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(repo_root))

    report: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "checks": [],
        "package": {},
        "config": {},
        "assets": {},
        "backend": {},
    }

    if "root" in args.check:
        try:
            import humanoid  # noqa: F401
            report["package"] = {
                "name": "humanoid",
                "version": version("humanoid"),
                "import_ok": True,
                "root_dir": str(import_module("humanoid").LEGGED_GYM_ROOT_DIR),
            }
            report["checks"].append({"name": "root", "status": "passed"})
        except PackageNotFoundError as exc:
            report["checks"].append({"name": "root", "status": "failed", "error": str(exc)})
            print("ERROR: humanoid distribution is not installed", file=sys.stderr)
            return 2

    cfg = None
    ppo = None
    if "config" in args.check or "assets" in args.check:
        try:
            parsed = _load_config(repo_root)
            cfg = parsed["XBotLCfg"]
            ppo = parsed["XBotLCfgPPO"]
            report["config"] = {
                "num_observations": cfg["env"]["num_observations"],
                "num_actions": cfg["env"]["num_actions"],
                "frame_stack": cfg["env"]["frame_stack"],
                "num_single_obs": cfg["env"]["num_single_obs"],
                "num_privileged_obs": cfg["env"]["num_privileged_obs"],
                "single_num_privileged_obs": cfg["env"]["single_num_privileged_obs"],
                "experiment_name": ppo["runner"]["experiment_name"],
            }
            report["checks"].append({"name": "config", "status": "passed"})
        except Exception as exc:
            report["checks"].append({"name": "config", "status": "failed", "error": str(exc)})
            print("ERROR: failed to parse XBot config: {0}".format(exc), file=sys.stderr)
            return 2

    if "assets" in args.check:
        if cfg is None:
            parsed = _load_config(repo_root)
            cfg = parsed["XBotLCfg"]
        paths = _asset_paths(repo_root, cfg)
        report["assets"] = {key: str(value) for key, value in paths.items()}
        missing = [str(path) for path in paths.values() if not path.exists()]
        if missing:
            report["checks"].append({"name": "assets", "status": "failed", "missing": missing})
            print("ERROR: missing asset files:\n- " + "\n- ".join(missing), file=sys.stderr)
            return 2
        report["checks"].append({"name": "assets", "status": "passed"})

    if "torch" in args.check or "cuda" in args.check:
        try:
            import torch
            report["backend"]["torch_version"] = torch.__version__
            report["backend"]["torch_cuda_version"] = torch.version.cuda
            report["backend"]["cuda_available"] = bool(torch.cuda.is_available())
            report["backend"]["device_count"] = int(torch.cuda.device_count())
            if "cuda" in args.check:
                if torch.cuda.is_available():
                    x = torch.empty((1,), device="cuda")
                    report["backend"]["cuda_device"] = str(x.device)
                    report["checks"].append({"name": "cuda", "status": "passed"})
                else:
                    report["checks"].append({"name": "cuda", "status": "blocked", "reason": "torch.cuda.is_available() is false"})
                    print("ERROR: CUDA is not available in this environment", file=sys.stderr)
                    return 2
            else:
                report["checks"].append({"name": "torch", "status": "passed"})
        except Exception as exc:
            report["checks"].append({"name": "torch/cuda", "status": "failed", "error": str(exc)})
            print("ERROR: torch backend check failed: {0}".format(exc), file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Humanoid-Gym install inspection")
        print("- repo root:", report["repo_root"])
        if report["package"]:
            print("- package:", report["package"]["name"], report["package"]["version"])
            print("- package root:", report["package"]["root_dir"])
        if report["config"]:
            print("- config dims:", report["config"]["num_observations"], report["config"]["num_privileged_obs"], report["config"]["num_actions"])
            print("- experiment:", report["config"]["experiment_name"])
        if report["backend"]:
            print("- torch:", report["backend"].get("torch_version"), "cuda:", report["backend"].get("torch_cuda_version"))
            print("- cuda available:", report["backend"].get("cuda_available"), "device_count:", report["backend"].get("device_count"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
