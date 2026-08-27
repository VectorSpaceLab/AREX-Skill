#!/usr/bin/env python3
"""Summarize XBot-L config constants without importing Isaac Gym.

This helper reads the source files with AST and optional XML inspection so
it can be used in a plain Python environment.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


def _eval_expr(node: ast.AST, env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise KeyError(f"Unknown name in config expression: {node.id}")
    if isinstance(node, ast.Attribute):
        base = _eval_expr(node.value, env)
        if isinstance(base, dict):
            return base[node.attr]
        return getattr(base, node.attr)
    if isinstance(node, ast.List):
        return [_eval_expr(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_expr(elt, env) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval_expr(key, env): _eval_expr(value, env)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.BinOp):
        left = _eval_expr(node.left, env)
        right = _eval_expr(node.right, env)
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
    if isinstance(node, ast.UnaryOp):
        value = _eval_expr(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.USub):
            return -value
    if isinstance(node, ast.Call):
        func = _eval_expr(node.func, env)
        args = [_eval_expr(arg, env) for arg in node.args]
        kwargs = {kw.arg: _eval_expr(kw.value, env) for kw in node.keywords}
        return func(*args, **kwargs)
    raise TypeError(f"Unsupported config expression: {ast.dump(node)}")


def _collect_class(node: ast.ClassDef) -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "int": int,
        "float": float,
        "len": len,
        "tuple": tuple,
        "list": list,
        "dict": dict,
    }
    data: Dict[str, Any] = {}
    for stmt in node.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            value = _eval_expr(stmt.value, env)
            env[stmt.targets[0].id] = value
            data[stmt.targets[0].id] = value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
            value = _eval_expr(stmt.value, env)
            env[stmt.target.id] = value
            data[stmt.target.id] = value
        elif isinstance(stmt, ast.ClassDef):
            nested = _collect_class(stmt)
            env[stmt.name] = nested
            data[stmt.name] = nested
    return data


def _collect_module(path: Path) -> Dict[str, Dict[str, Any]]:
    tree = ast.parse(path.read_text(), filename=str(path))
    result: Dict[str, Dict[str, Any]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            result[node.name] = _collect_class(node)
    return result


def _expr_text(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_expr_text(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        args = ", ".join(_expr_text(arg) for arg in node.args)
        return f"{_expr_text(node.func)}({args})"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ast.dump(node)


def _parse_registration(path: Path) -> List[Dict[str, str]]:
    tree = ast.parse(path.read_text(), filename=str(path))
    registrations: List[Dict[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "register":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                registrations.append(
                    {
                        "task_id": node.args[0].value,
                        "task_class": _expr_text(node.args[1]) if len(node.args) > 1 else "",
                        "env_cfg": _expr_text(node.args[2]) if len(node.args) > 2 else "",
                        "train_cfg": _expr_text(node.args[3]) if len(node.args) > 3 else "",
                    }
                )
    return registrations


def _resolve_asset_path(repo_root: Path, asset_template: str) -> Path:
    resolved = asset_template.replace("{LEGGED_GYM_ROOT_DIR}", str(repo_root))
    return Path(resolved)


def _inspect_urdf(path: Path, foot_name: str, knee_name: str, base_name: str = "base_link") -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    root = ET.parse(path).getroot()
    link_names = [elem.attrib["name"] for elem in root.findall(".//link") if "name" in elem.attrib]
    joint_names = [
        elem.attrib["name"]
        for elem in root.findall(".//joint")
        if elem.attrib.get("type") != "fixed" and "name" in elem.attrib
    ]
    return {
        "exists": True,
        "path": str(path),
        "link_names": link_names,
        "non_fixed_joint_names": joint_names,
        "foot_matches": [name for name in link_names if foot_name in name],
        "knee_matches": [name for name in link_names if knee_name in name],
        "base_matches": [name for name in link_names if base_name in name],
    }


def _missing_keys(expected: List[str], actual: List[str]) -> List[str]:
    actual_set = set(actual)
    return [key for key in expected if key not in actual_set]


def build_summary(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    base_file = repo_root / "humanoid/envs/base/legged_robot_config.py"
    custom_file = repo_root / "humanoid/envs/custom/humanoid_config.py"
    registration_file = repo_root / "humanoid/envs/__init__.py"

    base_cfg = _collect_module(base_file)
    custom_cfg = _collect_module(custom_file)
    registrations = _parse_registration(registration_file)

    xbot_env = custom_cfg["XBotLCfg"]["env"]
    xbot_asset = custom_cfg["XBotLCfg"]["asset"]
    xbot_sim = custom_cfg["XBotLCfg"]["sim"]
    xbot_control = custom_cfg["XBotLCfg"]["control"]
    xbot_rewards = custom_cfg["XBotLCfg"]["rewards"]
    xbot_runner = custom_cfg["XBotLCfgPPO"]["runner"]
    xbot_policy = custom_cfg["XBotLCfgPPO"]["policy"]
    xbot_algorithm = custom_cfg["XBotLCfgPPO"]["algorithm"]
    xbot_init = custom_cfg["XBotLCfg"]["init_state"]
    xbot_noise = custom_cfg["XBotLCfg"]["noise"]
    xbot_norm = custom_cfg["XBotLCfg"]["normalization"]
    xbot_domain = custom_cfg["XBotLCfg"]["domain_rand"]
    xbot_commands = custom_cfg["XBotLCfg"]["commands"]
    xbot_terrain = custom_cfg["XBotLCfg"]["terrain"]

    asset_path = _resolve_asset_path(repo_root, xbot_asset["file"])
    urdf_info = _inspect_urdf(asset_path, xbot_asset["foot_name"], xbot_asset["knee_name"], "base_link")
    default_joint_keys = sorted(xbot_init["default_joint_angles"].keys())
    non_fixed_joint_names = urdf_info.get("non_fixed_joint_names", [])

    derived = {
        "policy_dt": round(float(xbot_sim["dt"]) * float(xbot_control["decimation"]), 6),
        "actor_stack": int(xbot_env["frame_stack"]) * int(xbot_env["num_single_obs"]),
        "critic_stack": int(xbot_env["c_frame_stack"]) * int(xbot_env["single_num_privileged_obs"]),
        "default_joint_angle_missing": _missing_keys(non_fixed_joint_names, default_joint_keys),
        "default_joint_angle_extra": [key for key in default_joint_keys if key not in set(non_fixed_joint_names)],
    }

    return {
        "repo_root": str(repo_root),
        "registration": registrations,
        "base_cfg": base_cfg,
        "xbot_cfg": custom_cfg,
        "derived": derived,
        "asset_check": {
            "asset_path": str(asset_path),
            "exists": asset_path.exists(),
            "foot_name": xbot_asset["foot_name"],
            "knee_name": xbot_asset["knee_name"],
            "base_contact_name": "base_link",
        },
        "urdf_check": urdf_info,
        "selected": {
            "env": xbot_env,
            "asset": xbot_asset,
            "terrain": xbot_terrain,
            "control": xbot_control,
            "sim": xbot_sim,
            "domain_rand": xbot_domain,
            "commands": xbot_commands,
            "rewards": xbot_rewards,
            "normalization": xbot_norm,
            "noise": xbot_noise,
            "init_state": xbot_init,
            "policy": xbot_policy,
            "algorithm": xbot_algorithm,
            "runner": xbot_runner,
        },
    }


def render_text(summary: Dict[str, Any]) -> str:
    selected = summary["selected"]
    env = selected["env"]
    asset = selected["asset"]
    sim = selected["sim"]
    control = selected["control"]
    runner = selected["runner"]
    policy = selected["policy"]
    algorithm = selected["algorithm"]
    asset_check = summary["asset_check"]
    urdf_check = summary["urdf_check"]
    derived = summary["derived"]
    registrations = summary["registration"]

    lines: List[str] = []
    lines.append("Registration:")
    if registrations:
        for reg in registrations:
            lines.append(
                f"  {reg['task_id']} -> {reg['task_class']}({reg['env_cfg']}, {reg['train_cfg']})"
            )
    else:
        lines.append("  <no registration found>")
    lines.append("")
    lines.append("XBot-L summary:")
    lines.append(
        f"  env: stack={env['frame_stack']}x{env['num_single_obs']}={env['num_observations']}, "
        f"critic={env['c_frame_stack']}x{env['single_num_privileged_obs']}={env['num_privileged_obs']}, "
        f"actions={env['num_actions']}, episode={env['episode_length_s']}s, ref_actions={env['use_ref_actions']}"
    )
    lines.append(
        f"  sim/control: dt={sim['dt']}, decimation={control['decimation']}, action_scale={control['action_scale']}, policy_dt={derived['policy_dt']}"
    )
    lines.append(
        f"  terrain: mesh_type={selected['terrain']['mesh_type']}, curriculum={selected['terrain']['curriculum']}, measure_heights={selected['terrain']['measure_heights']}"
    )
    lines.append(
        f"  asset: file={asset['file']}, exists={asset_check['exists']}, foot_name={asset_check['foot_name']}, knee_name={asset_check['knee_name']}"
    )
    lines.append(
        f"  URDF joints: {len(urdf_check.get('non_fixed_joint_names', []))} non-fixed joints; matches foot={len(urdf_check.get('foot_matches', []))}, knee={len(urdf_check.get('knee_matches', []))}, base={len(urdf_check.get('base_matches', []))}"
    )
    if urdf_check.get("foot_matches"):
        lines.append(f"  foot matches: {', '.join(urdf_check['foot_matches'])}")
    if urdf_check.get("knee_matches"):
        lines.append(f"  knee matches: {', '.join(urdf_check['knee_matches'])}")
    if urdf_check.get("base_matches"):
        lines.append(f"  base matches: {', '.join(urdf_check['base_matches'])}")
    if urdf_check.get("non_fixed_joint_names"):
        lines.append(f"  joint names: {', '.join(urdf_check['non_fixed_joint_names'])}")
    if derived["default_joint_angle_missing"]:
        lines.append(f"  missing default_joint_angles keys: {', '.join(derived['default_joint_angle_missing'])}")
    lines.append("")
    lines.append("Key motion terms:")
    lines.append(
        f"  commands: heading_command={selected['commands']['heading_command']}, resampling_time={selected['commands']['resampling_time']}, ranges={selected['commands']['ranges']}"
    )
    lines.append(
        f"  gait: cycle_time={selected['rewards']['cycle_time']}, target_joint_pos_scale={selected['rewards']['target_joint_pos_scale']}, target_feet_height={selected['rewards']['target_feet_height']}"
    )
    lines.append("")
    lines.append("Runner/policy summary:")
    lines.append(
        f"  runner: experiment_name={runner['experiment_name']}, num_steps_per_env={runner['num_steps_per_env']}, max_iterations={runner['max_iterations']}"
    )
    lines.append(
        f"  policy: actor_hidden_dims={policy['actor_hidden_dims']}, critic_hidden_dims={policy['critic_hidden_dims']}"
    )
    lines.append(
        f"  algorithm: learning_rate={algorithm['learning_rate']}, entropy_coef={algorithm['entropy_coef']}, gamma={algorithm['gamma']}, lam={algorithm['lam']}"
    )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize XBot-L config constants without Isaac Gym.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Path to the humanoid-gym repository root")
    parser.add_argument("--json", action="store_true", help="Print the full parsed summary as JSON")
    args = parser.parse_args(argv)

    summary = build_summary(args.repo_root)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
