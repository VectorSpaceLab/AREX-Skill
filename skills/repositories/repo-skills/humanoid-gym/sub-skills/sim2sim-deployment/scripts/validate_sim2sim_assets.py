#!/usr/bin/env python3
"""Validate Humanoid-Gym sim2sim assets and optional policy shape safely.

This helper does not launch MuJoCo. It checks that the XBot asset files exist
and, when a policy is supplied, that the TorchScript policy can accept the
expected XBot-L observation size and return the expected action size.
"""
from __future__ import annotations

import argparse
import ast
import json
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

CONFIG_RELATIVE = Path("humanoid/envs/custom/humanoid_config.py")
SIM2SIM_RELATIVE = Path("humanoid/scripts/sim2sim.py")
DEFAULT_POLICY_INPUT = 705
DEFAULT_POLICY_OUTPUT = 12
DEFAULT_FRAME_STACK = 15
DEFAULT_SINGLE_OBS = 47

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

def _parse_xml(path: Path) -> Tuple[Optional[ET.Element], Optional[str]]:
    """Parse an XML asset without importing MuJoCo or a ROS package."""
    try:
        return ET.parse(path).getroot(), None
    except (ET.ParseError, OSError) as exc:
        return None, str(exc)


def _resolve_reference(base_dir: Path, reference: str) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve the local URI forms used by the bundled MJCF and URDF files."""
    reference = reference.strip()
    if not reference:
        return None, "empty file reference"
    if reference.startswith("package://"):
        return None, "package:// references are not supported by this local validator"
    if reference.startswith("file://"):
        reference = reference[7:]
    path = Path(reference).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(), None


def _parse_png(path: Path, data: bytes) -> Optional[str]:
    """Perform a small PNG container check without Pillow."""
    signature = bytes((137, 80, 78, 71, 13, 10, 26, 10))
    if not data.startswith(signature):
        return "does not start with a PNG signature"
    offset = len(signature)
    saw_ihdr = False
    saw_iend = False
    try:
        while offset + 12 <= len(data):
            length = struct.unpack(">I", data[offset : offset + 4])[0]
            chunk_end = offset + 12 + length
            if chunk_end > len(data):
                return "contains a truncated PNG chunk"
            chunk_type = data[offset + 4 : offset + 8]
            if chunk_type == b"IHDR":
                saw_ihdr = True
                if length != 13:
                    return "has an invalid PNG IHDR length"
            elif chunk_type == b"IEND":
                saw_iend = True
                break
            offset = chunk_end
    except struct.error:
        return "contains an invalid PNG chunk header"
    if not saw_ihdr or not saw_iend:
        return "is missing a complete PNG IHDR/IEND sequence"
    return None


def _parse_stl(path: Path, data: bytes) -> Optional[str]:
    """Accept ordinary ASCII or binary STL containers with at least one facet."""
    if len(data) >= 84:
        triangle_count = struct.unpack("<I", data[80:84])[0]
        if triangle_count > 0 and 84 + 50 * triangle_count <= len(data):
            return None
    try:
        text = data.decode("ascii", errors="ignore").lower()
    except UnicodeError:
        text = ""
    if "facet" in text and "vertex" in text and "endsolid" in text:
        return None
    return "is not a recognizable ASCII or binary STL"


def _parse_referenced_file(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return str(exc)
    if not data:
        return "is empty"
    suffix = path.suffix.lower()
    if suffix == ".png":
        return _parse_png(path, data)
    if suffix == ".stl":
        return _parse_stl(path, data)
    return None


def _xml_reference_checks(path: Path, kind: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse an MJCF/URDF and verify every local mesh/heightfield reference."""
    checks: List[Dict[str, Any]] = []
    errors: List[str] = []
    root, parse_error = _parse_xml(path)
    checks.append({"name": f"parse_{kind}", "path": str(path), "ok": parse_error is None})
    if parse_error:
        errors.append(f"{kind.upper()} XML is not parseable ({path}): {parse_error}")
        return checks, errors

    references: List[Tuple[str, str, Path]] = []
    if kind == "mjcf":
        compiler = root.find("compiler")
        meshdir = compiler.get("meshdir", "") if compiler is not None else ""
        mesh_base = path.parent / meshdir if meshdir else path.parent
        for element in root.iter("mesh"):
            if element.get("file"):
                references.append(("mesh", element.get("file", ""), mesh_base))
        for element in root.iter("hfield"):
            if element.get("file"):
                references.append(("heightfield", element.get("file", ""), path.parent))
    else:
        for element in root.iter("mesh"):
            if element.get("filename"):
                references.append(("mesh", element.get("filename", ""), path.parent))

    seen = set()
    for ref_kind, reference, base_dir in references:
        resolved, resolve_error = _resolve_reference(base_dir, reference)
        check_name = f"{kind}_{ref_kind}:{reference}"
        if resolve_error:
            checks.append({"name": check_name, "reference": reference, "ok": False, "error": resolve_error})
            errors.append(f"{kind.upper()} {ref_kind} reference {reference!r}: {resolve_error}")
            continue
        assert resolved is not None
        key = (ref_kind, str(resolved))
        if key in seen:
            continue
        seen.add(key)
        parse_error = None if resolved.is_file() else "file does not exist"
        if parse_error is None:
            parse_error = _parse_referenced_file(resolved)
        ok = parse_error is None
        checks.append({"name": check_name, "reference": reference, "path": str(resolved), "ok": ok})
        if not ok:
            errors.append(f"{kind.upper()} {ref_kind} {reference!r} -> {resolved}: {parse_error}")
    return checks, errors


def _entrypoint_check(repo_root: Path) -> Tuple[Dict[str, Any], List[str]]:
    path = repo_root / SIM2SIM_RELATIVE
    check: Dict[str, Any] = {"name": "sim2sim_entrypoint", "path": str(path), "exists": path.is_file(), "ok": False}
    if not path.is_file():
        return check, [f"sim2sim entrypoint is missing: {path}"]
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError) as exc:
        check["error"] = str(exc)
        return check, [f"sim2sim entrypoint is not parseable ({path}): {exc}"]
    has_terrain = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(isinstance(arg, ast.Constant) and arg.value == "--terrain" for arg in node.args)
        for node in ast.walk(tree)
    )
    check["has_terrain_option"] = has_terrain
    check["ok"] = has_terrain
    if not has_terrain:
        return check, [f"sim2sim entrypoint does not expose the --terrain option: {path}"]
    return check, []




def load_config(repo_root: Path):
    path = repo_root / CONFIG_RELATIVE
    tree = ast.parse(path.read_text())
    out: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "XBotLCfg":
            out = _class_to_dict(node)
            break
    if not out:
        raise RuntimeError("could not locate XBotLCfg in config source")
    return out


def asset_paths(repo_root: Path, cfg: Dict[str, Any]):
    asset_file = cfg["asset"]["file"]
    asset_path = asset_file.replace("{LEGGED_GYM_ROOT_DIR}", str(repo_root))
    mjcf_plane = repo_root / "resources/robots/XBot/mjcf/XBot-L.xml"
    mjcf_terrain = repo_root / "resources/robots/XBot/mjcf/XBot-L-terrain.xml"
    urdf = Path(asset_path)
    terrain = repo_root / "resources/robots/XBot/terrain/uneven.png"
    return {
        "urdf": urdf,
        "mjcf_plane": mjcf_plane,
        "mjcf_terrain": mjcf_terrain,
        "terrain_png": terrain,
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate Humanoid-Gym sim2sim assets and optional TorchScript policy shape.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, help="Path to the Humanoid-Gym repository root.")
    parser.add_argument("--policy", default="", help="Optional TorchScript policy path to check.")
    parser.add_argument("--terrain", action="store_true", help="Validate the terrain MJCF choice as the intended rollout asset.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    parser.add_argument("--expected-input-dim", type=int, default=DEFAULT_POLICY_INPUT, help="Policy input width to exercise when --policy is supplied.")
    parser.add_argument("--expected-output-dim", type=int, default=DEFAULT_POLICY_OUTPUT, help="Expected policy output dimension.")
    return parser




def main():
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    result: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "selected_asset": "",
        "config": {},
        "checks": [],
        "errors": [],
    }
    errors: List[str] = result["errors"]

    try:
        cfg = load_config(repo_root)
        paths = asset_paths(repo_root, cfg)
    except (OSError, SyntaxError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        errors.append(f"could not load sim2sim configuration: {exc}")
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("ERROR: " + errors[0], file=sys.stderr)
        return 2

    selected = paths["mjcf_terrain"] if args.terrain else paths["mjcf_plane"]
    result["selected_asset"] = str(selected)
    try:
        config_values = {
            "num_observations": int(cfg["env"]["num_observations"]),
            "num_actions": int(cfg["env"]["num_actions"]),
            "frame_stack": int(cfg["env"]["frame_stack"]),
            "num_single_obs": int(cfg["env"]["num_single_obs"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"config is missing an integer observation/action value: {exc}")
        config_values = {}
    result["config"] = config_values

    if config_values:
        expected_from_stack = config_values["frame_stack"] * config_values["num_single_obs"]
        contract_errors = []
        if config_values["frame_stack"] != DEFAULT_FRAME_STACK:
            contract_errors.append(f"frame_stack must be {DEFAULT_FRAME_STACK}, got {config_values['frame_stack']}")
        if config_values["num_single_obs"] != DEFAULT_SINGLE_OBS:
            contract_errors.append(f"num_single_obs must be {DEFAULT_SINGLE_OBS}, got {config_values['num_single_obs']}")
        if config_values["num_observations"] != expected_from_stack:
            contract_errors.append(
                "num_observations must equal frame_stack * num_single_obs "
                f"({expected_from_stack}), got {config_values['num_observations']}"
            )
        if config_values["num_observations"] != DEFAULT_POLICY_INPUT:
            contract_errors.append(f"num_observations contract is {DEFAULT_POLICY_INPUT}, got {config_values['num_observations']}")
        if config_values["num_actions"] != DEFAULT_POLICY_OUTPUT:
            contract_errors.append(f"num_actions contract is {DEFAULT_POLICY_OUTPUT}, got {config_values['num_actions']}")
        result["checks"].append({"name": "observation_action_contract", "ok": not contract_errors, "errors": contract_errors})
        errors.extend("config observation/action contract: " + item for item in contract_errors)

    if args.expected_input_dim <= 0 or args.expected_output_dim <= 0:
        errors.append("expected policy dimensions must be positive integers")

    entry_check, entry_errors = _entrypoint_check(repo_root)
    result["checks"].append(entry_check)
    errors.extend(entry_errors)

    missing = []
    for label, path in paths.items():
        exists = path.is_file()
        result["checks"].append({"name": label, "path": str(path), "exists": exists, "ok": exists})
        if not exists:
            missing.append(f"{label}: {path}")
    errors.extend("missing required sim2sim asset: " + item for item in missing)

    for label, kind in (("mjcf_plane", "mjcf"), ("mjcf_terrain", "mjcf"), ("urdf", "urdf")):
        checks, check_errors = _xml_reference_checks(paths[label], kind)
        result["checks"].extend(checks)
        errors.extend(check_errors)

    terrain_parse_error = _parse_referenced_file(paths["terrain_png"]) if paths["terrain_png"].is_file() else "file does not exist"
    terrain_ok = terrain_parse_error is None
    result["checks"].append({"name": "terrain_png_parse", "path": str(paths["terrain_png"]), "ok": terrain_ok})
    if not terrain_ok:
        errors.append(f"terrain heightfield is not parseable ({paths['terrain_png']}): {terrain_parse_error}")

    policy_path = Path(args.policy).expanduser() if args.policy else None
    if policy_path is not None:
        policy_exists = policy_path.is_file()
        result["checks"].append({"name": "policy", "path": str(policy_path), "exists": policy_exists, "ok": policy_exists})
        if not policy_exists:
            errors.append(f"policy file does not exist: {policy_path}")
        else:
            try:
                import torch
                policy = torch.jit.load(str(policy_path), map_location="cpu")
                dummy = torch.zeros(1, args.expected_input_dim)
                output = policy(dummy)
                output_shape = tuple(getattr(output, "shape", ()))
                if not output_shape:
                    raise ValueError("policy output has no tensor shape")
                result["policy_shape"] = {
                    "input_dim": int(dummy.shape[-1]),
                    "output_shape": output_shape,
                    "expected_output_dim": args.expected_output_dim,
                }
                if output_shape[-1] != args.expected_output_dim:
                    errors.append(
                        "policy output dimension mismatch: expected "
                        f"{args.expected_output_dim}, got {output_shape[-1]}"
                    )
            except Exception as exc:
                errors.append(f"failed to load or run TorchScript policy: {exc}")

    if errors:
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("ERROR: sim2sim validation failed", file=sys.stderr)
            for error in errors:
                print("- " + error, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("sim2sim asset validation passed")
        print("- selected asset:", result["selected_asset"])
        print("- num_observations:", result["config"]["num_observations"])
        print("- num_actions:", result["config"]["num_actions"])
        if "policy_shape" in result:
            print("- policy input dim:", result["policy_shape"]["input_dim"])
            print("- policy output shape:", result["policy_shape"]["output_shape"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
