#!/usr/bin/env python3
"""List and classify RLinf embodied/offline/SFT YAML configs.

This script is intentionally static and non-mutating. It can be run from any
working directory and does not import RLinf or launch training.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:  # Graceful optional dependency.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - behavior tested manually without PyYAML.
    yaml = None  # type: ignore

ENV_TYPES = {
    "maniskill",
    "maniskill_rlt",
    "libero",
    "robotwin",
    "isaaclab",
    "metaworld",
    "behavior",
    "calvin",
    "robocasa",
    "robocasa365",
    "realworld",
    "frankasim",
    "habitat",
    "opensora_wm",
    "wan_wm",
    "genesis",
    "embodichain",
    "roboverse",
    "d4rl",
    "polaris",
}

MODEL_TYPES = {
    "qwen2.5",
    "qwen2.5_vl",
    "qwen3",
    "qwen3_vl",
    "qwen3_moe",
    "openvla",
    "openvla_oft",
    "molmoact2",
    "openpi",
    "openpi_rlinf",
    "starvla",
    "mlp_policy",
    "rlt_mlp_policy",
    "rlt_td3_mlp_policy",
    "gr00t",
    "dexbotic_pi",
    "dexbotic_dm0",
    "dreamzero",
    "cnn_policy",
    "flow_policy",
    "cma",
    "lingbotvla",
    "abot_m0",
    "resnet",
    "cfg_model",
    "recap_value_model",
    "steam_value_model",
    "qwen3_vl_moe",
    "deepseek_v3",
    "gr00t_n1d6",
    "gr00t_n1d7",
    "evo1",
}

TASK_TYPES = {"embodied", "embodied_eval", "offline", "sft"}

FAMILY_TOKENS = [
    "maniskill_rlt",
    "maniskill",
    "libero",
    "robotwin",
    "robocasa365",
    "robocasa",
    "behavior",
    "calvin",
    "metaworld",
    "isaaclab",
    "realworld",
    "frankasim",
    "opensora",
    "wan",
    "genesis",
    "embodichain",
    "roboverse",
    "d4rl",
    "polaris",
    "habitat",
    "dosw1",
    "xsquare",
    "gim_arm",
]

MODEL_TOKENS = sorted(MODEL_TYPES | {"openvlaoft", "pi0", "pi05", "gr00t_n1d6", "gr00t_n1d7"}, key=len, reverse=True)
ALGO_TOKENS = [
    "decoupled_actor_critic",
    "actor_critic",
    "embodied_sac",
    "embodied_dagger",
    "embodied_nft",
    "offline_iql",
    "rlt_td3",
    "rlt_ac",
    "grpo",
    "ppo",
    "sac",
    "dagger",
    "iql",
    "nft",
    "opd",
    "dsrl",
]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def _load_yaml(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _get(data: Any, dotted: str) -> Any:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)


def _default_mounts(data: dict[str, Any]) -> dict[str, list[str]]:
    mounts: dict[str, list[str]] = {"env.train": [], "env.eval": [], "actor.model": []}
    defaults = data.get("defaults")
    if not isinstance(defaults, list):
        return mounts
    for item in defaults:
        if isinstance(item, str):
            left = item
            target = ""
        elif isinstance(item, dict):
            if not item:
                continue
            left, target = next(iter(item.items()))
            left = str(left)
            target = str(target)
        else:
            continue
        if "@" in left:
            preset, target = left.split("@", 1)
        else:
            preset = left
        preset = preset.strip()
        target = target.strip()
        if target in mounts:
            mounts[target].append(preset)
    return mounts


def _infer_from_defaults(data: dict[str, Any], target: str) -> str:
    mounts = _default_mounts(data)
    values = mounts.get(target, [])
    if not values:
        return ""
    return ",".join(values)


def _infer_env_from_text(text: str, path: Path, data: dict[str, Any], split: str) -> str:
    direct = _get(data, f"env.{split}.env_type")
    if direct:
        return str(direct)
    preset = _infer_from_defaults(data, f"env.{split}")
    if preset:
        for env in sorted(ENV_TYPES, key=len, reverse=True):
            if env in preset:
                return env
        if "opensora" in preset:
            return "opensora_wm"
        if "wan" in preset:
            return "wan_wm"
        return f"preset:{preset}"
    match = re.search(rf"env[./_-]([A-Za-z0-9_.-]+).*@env\.{split}", text)
    if match:
        return f"preset:env/{match.group(1)}"
    family = _infer_family_from_name(path.name)
    return family if family in ENV_TYPES else ""


def _infer_model(text: str, path: Path, data: dict[str, Any]) -> str:
    # Prefer the trainable actor model. Reward-model configs may also contain a
    # reward.model.model_type (for example resnet) that should not hide the
    # policy model imported through Hydra defaults.
    direct_actor = _get(data, "actor.model.model_type")
    if direct_actor:
        return str(direct_actor)
    preset = _infer_from_defaults(data, "actor.model")
    if preset:
        normalized = preset.replace("-", "_")
        aliases = {"openvlaoft": "openvla_oft", "pi0": "openpi", "pi0_5": "openpi", "pi05": "openpi"}
        for model in sorted(MODEL_TYPES, key=len, reverse=True):
            if model in normalized:
                return model
        for alias, canonical in aliases.items():
            if alias in normalized:
                return canonical
        return f"preset:{preset}"
    for dotted in ("rollout.model.model_type", "reward.model.model_type"):
        direct = _get(data, dotted)
        if direct:
            return str(direct)
    hay = f"{path.stem}\n{text[:4000]}".lower().replace("-", "_")
    for token in MODEL_TOKENS:
        normalized = token.replace("-", "_")
        if normalized in hay:
            if normalized in {"openvlaoft"}:
                return "openvla_oft"
            if normalized in {"pi0", "pi05"}:
                return "openpi"
            return normalized
    return ""


def _infer_family_from_name(name: str) -> str:
    lower = name.lower().replace("-", "_")
    for token in FAMILY_TOKENS:
        if token in lower:
            if token == "opensora":
                return "opensora_wm"
            if token == "wan":
                return "wan_wm"
            return token
    return ""


def _infer_algorithm(text: str, path: Path, data: dict[str, Any]) -> tuple[str, str]:
    adv = _get(data, "algorithm.adv_type")
    loss = _get(data, "algorithm.loss_type")
    if adv or loss:
        return _stringify(adv), _stringify(loss)
    hay = f"{path.stem}\n{text[:4000]}".lower().replace("-", "_")
    for token in ALGO_TOKENS:
        if token in hay:
            if token == "ppo":
                return "gae", "actor_critic"
            if token == "grpo":
                return "grpo", "actor"
            if token == "sac":
                return "embodied_sac", "embodied_sac"
            if token == "iql":
                return "", "offline_iql"
            return token, token
    return "", ""


def _infer_task_type(text: str, path: Path, data: dict[str, Any]) -> str:
    direct = _get(data, "runner.task_type")
    if direct:
        return str(direct)
    lower = f"{path.as_posix()}\n{text[:4000]}".lower()
    if "offline_rl" in lower or "offline_iql" in lower or "d4rl" in lower:
        return "offline"
    if "/sft/" in lower or "_sft" in path.stem:
        return "sft"
    if "eval" in path.stem and "embodied" in lower:
        return "embodied_eval"
    if any(tok in lower for tok in FAMILY_TOKENS):
        return "embodied"
    return ""


def _flag_summary(data: dict[str, Any], text: str) -> str:
    flags: list[str] = []
    if _get(data, "reward.use_reward_model") is True or re.search(r"use_reward_model\s*:\s*true", text, re.I):
        flags.append("reward")
    if "data_collection" in text and re.search(r"enabled\s*:\s*true", text, re.I):
        flags.append("collect")
    if _get(data, "runner.use_training_pipeline") is True:
        flags.append("pipeline")
    if _get(data, "runner.enable_decoupled_mode") is True:
        flags.append("decoupled")
    if _get(data, "runner.rtc.enabled") is True or "rtc" in Path(str(_get(data, "runner.logger.experiment_name") or "")).name.lower():
        flags.append("rtc")
    if "/path/to/" in text or "ROBOT_IP" in text or "TARGET_EE_POSE" in text:
        flags.append("placeholders")
    return ",".join(flags)


def _is_interesting(record: dict[str, Any], include_all: bool) -> bool:
    if include_all:
        return True
    if record["task_type"] in TASK_TYPES:
        return True
    if record["family"] or record["env_train"] or record["env_eval"] or record["model"]:
        return True
    return False


def classify(path: Path, root: Path) -> dict[str, Any]:
    text = _read_text(path)
    data = _load_yaml(path)
    task_type = _infer_task_type(text, path, data)
    family = _infer_family_from_name(path.name)
    env_train = _infer_env_from_text(text, path, data, "train")
    env_eval = _infer_env_from_text(text, path, data, "eval")
    model = _infer_model(text, path, data)
    adv, loss = _infer_algorithm(text, path, data)
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        rel = path.as_posix()
    return {
        "path": rel,
        "task_type": task_type,
        "family": family,
        "env_train": env_train,
        "env_eval": env_eval,
        "model": model,
        "adv_type": adv,
        "loss_type": loss,
        "flags": _flag_summary(data, text),
    }


def iter_yaml_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in {".yaml", ".yml"} else []
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "venv", "node_modules"}]
        for filename in filenames:
            if filename.lower().endswith((".yaml", ".yml")):
                files.append(Path(dirpath) / filename)
    return sorted(files)


def print_table(records: list[dict[str, Any]]) -> None:
    columns = ["path", "task_type", "family", "env_train", "env_eval", "model", "adv_type", "loss_type", "flags"]
    widths: dict[str, int] = {}
    for col in columns:
        max_value = max([len(str(r.get(col, ""))) for r in records] + [len(col)])
        widths[col] = min(max_value, 42 if col == "path" else 24)

    def trim(value: Any, width: int) -> str:
        text = str(value or "")
        if len(text) <= width:
            return text
        return text[: max(0, width - 1)] + "…"

    header = "  ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("  ".join("-" * widths[col] for col in columns))
    for record in records:
        print("  ".join(trim(record.get(col, ""), widths[col]).ljust(widths[col]) for col in columns))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely scan YAML files and classify RLinf embodied/offline/SFT configs without launching anything."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Config file, config directory, repo root, or current directory (default: .).",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a table.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include every YAML file, even if it does not look embodied/offline/SFT related.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Maximum records to print (0 means no limit).")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser()
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2

    records = [classify(path, root if root.is_dir() else root.parent) for path in iter_yaml_files(root)]
    records = [record for record in records if _is_interesting(record, args.all)]
    records.sort(key=lambda r: (r["task_type"] != "embodied", r["path"]))
    if args.limit > 0:
        records = records[: args.limit]

    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    elif not records:
        print("No embodied/offline/SFT-looking YAML configs found.")
    else:
        print_table(records)
        if yaml is None:
            print("\nNote: PyYAML is not installed; classification used filename/text heuristics only.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
