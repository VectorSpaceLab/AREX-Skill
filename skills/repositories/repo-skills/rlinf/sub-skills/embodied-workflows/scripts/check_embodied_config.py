#!/usr/bin/env python3
"""Static sanity checker for RLinf embodied/offline/SFT YAML configs.

The checker never imports RLinf and never launches training. It validates common
configuration structure and prints actionable errors/warnings. PyYAML is optional:
without it, the checker falls back to a limited text scan and exits gracefully.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

VALID_TASK_TYPES = {"embodied", "embodied_eval", "offline", "sft"}
VALID_ENV_TYPES = {
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
VALID_MODEL_TYPES = {
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
VALID_REWARD_MODELS = {"resnet", "vlm", "buffered_vlm"}
VALID_DATA_COLLECTION_FORMATS = {"pickle", "lerobot"}
PLACEHOLDER_PATTERNS = [
    re.compile(r"/path/to/", re.I),
    re.compile(r"<[^>]+>"),
    re.compile(r"\bROBOT_IP\b"),
    re.compile(r"\bTARGET_EE_POSE\b"),
    re.compile(r"\bZED_SERIAL\b"),
]


@dataclass
class Issue:
    severity: str
    path: str
    message: str


@dataclass
class Summary:
    file: str
    task_type: str | None
    env_train: str | None
    env_eval: str | None
    model_type: str | None
    adv_type: str | None
    loss_type: str | None
    errors: int
    warnings: int
    issues: list[Issue]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def load_yaml(path: Path) -> tuple[dict[str, Any], str | None]:
    text = read_text(path)
    if yaml is None:
        return {}, "PyYAML is not installed; using limited text checks only. Install PyYAML for structured YAML validation."
    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        return {}, f"YAML parse error: {exc}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return {}, "YAML root is not a mapping."
    return data, None


def get(data: Any, dotted: str) -> Any:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1", "on"}
    return bool(value)


def add(issues: list[Issue], severity: str, path: str, message: str) -> None:
    issues.append(Issue(severity=severity, path=path, message=message))


def default_mounts(data: dict[str, Any]) -> dict[str, list[str]]:
    mounts: dict[str, list[str]] = {"env.train": [], "env.eval": [], "actor.model": []}
    defaults = data.get("defaults")
    if not isinstance(defaults, list):
        return mounts
    for item in defaults:
        if isinstance(item, str):
            left = item
            target = ""
        elif isinstance(item, dict) and item:
            left, target = next(iter(item.items()))
            left = str(left)
            target = str(target)
        else:
            continue
        if "@" in left:
            preset, target = left.split("@", 1)
        else:
            preset = left
        target = target.strip()
        if target in mounts:
            mounts[target].append(preset.strip())
    return mounts


def family_from_preset(preset: str) -> str | None:
    low = preset.lower().replace("-", "_")
    mapping = [
        ("maniskill_rlt", "maniskill_rlt"),
        ("maniskill", "maniskill"),
        ("manikill", "maniskill"),
        ("robocasa365", "robocasa365"),
        ("robocasa", "robocasa"),
        ("robotwin", "robotwin"),
        ("isaaclab", "isaaclab"),
        ("metaworld", "metaworld"),
        ("behavior", "behavior"),
        ("calvin", "calvin"),
        ("realworld", "realworld"),
        ("frankasim", "frankasim"),
        ("opensora", "opensora_wm"),
        ("wan", "wan_wm"),
        ("genesis", "genesis"),
        ("gsenv", "genesis"),
        ("embodichain", "embodichain"),
        ("roboverse", "roboverse"),
        ("d4rl", "d4rl"),
        ("polaris", "polaris"),
        ("habitat", "habitat"),
        ("libero", "libero"),
        ("dosw1", "realworld"),
        ("xsquare", "realworld"),
        ("gim_arm", "realworld"),
    ]
    for token, family in mapping:
        if token in low:
            return family
    return None


def model_from_preset(preset: str) -> str | None:
    low = preset.lower().replace("-", "_")
    aliases = [
        ("openvla_oft", "openvla_oft"),
        ("openvlaoft", "openvla_oft"),
        ("openvla", "openvla"),
        ("pi0_5_rlinf", "openpi_rlinf"),
        ("pi0_rlinf", "openpi_rlinf"),
        ("openpi_rlinf", "openpi_rlinf"),
        ("pi0_5", "openpi"),
        ("pi05", "openpi"),
        ("pi0", "openpi"),
        ("openpi", "openpi"),
        ("gr00t_n1d7", "gr00t_n1d7"),
        ("gr00t_n1d6", "gr00t_n1d6"),
        ("gr00t", "gr00t"),
        ("mlp_policy", "mlp_policy"),
        ("rlt_td3_mlp_policy", "rlt_td3_mlp_policy"),
        ("rlt_mlp_policy", "rlt_mlp_policy"),
        ("cnn_policy", "cnn_policy"),
        ("flow_policy", "flow_policy"),
        ("dreamzero", "dreamzero"),
        ("starvla", "starvla"),
        ("lingbotvla", "lingbotvla"),
        ("dexbotic_pi", "dexbotic_pi"),
        ("dexbotic_dm0", "dexbotic_dm0"),
        ("abot", "abot_m0"),
        ("evo1", "evo1"),
        ("resnet", "resnet"),
    ]
    for token, model in aliases:
        if token in low:
            return model
    for model in sorted(VALID_MODEL_TYPES, key=len, reverse=True):
        if model in low:
            return model
    return None


def infer_env(data: dict[str, Any], split: str) -> tuple[str | None, bool]:
    direct = get(data, f"env.{split}.env_type")
    if direct:
        return str(direct), False
    mounts = default_mounts(data)
    presets = mounts.get(f"env.{split}", [])
    if presets:
        fam = family_from_preset(",".join(presets))
        return fam or f"preset:{','.join(presets)}", True
    return None, False


def infer_model(data: dict[str, Any]) -> tuple[str | None, bool]:
    # Prefer the actor policy model. Reward-enabled configs often contain
    # reward.model.model_type (for example resnet/buffered_vlm), but the main
    # embodied model is still the actor imported directly or through defaults.
    direct_actor = get(data, "actor.model.model_type")
    if direct_actor:
        return str(direct_actor), False
    presets = default_mounts(data).get("actor.model", [])
    if presets:
        model = model_from_preset(",".join(presets))
        return model or f"preset:{','.join(presets)}", True
    for dotted in ("rollout.model.model_type", "reward.model.model_type"):
        direct = get(data, dotted)
        if direct:
            return str(direct), False
    return None, False


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    return None


def find_data_collection_blocks(data: Any, prefix: str = "") -> list[tuple[str, dict[str, Any]]]:
    blocks: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key == "data_collection" and isinstance(value, dict):
                blocks.append((path, value))
            blocks.extend(find_data_collection_blocks(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            blocks.extend(find_data_collection_blocks(value, f"{prefix}[{idx}]"))
    return blocks


def find_video_blocks(data: Any, prefix: str = "") -> list[tuple[str, dict[str, Any]]]:
    blocks: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key == "video_cfg" and isinstance(value, dict):
                blocks.append((path, value))
            blocks.extend(find_video_blocks(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            blocks.extend(find_video_blocks(value, f"{prefix}[{idx}]"))
    return blocks


def flatten_scalars(data: Any, prefix: str = "") -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.extend(flatten_scalars(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            out.extend(flatten_scalars(value, f"{prefix}[{idx}]"))
    else:
        out.append((prefix, data))
    return out


def placement_mentions(placement: Any, component: str) -> bool:
    if placement is None:
        return False
    if isinstance(placement, dict):
        if component in placement:
            return True
        return any(component in str(key).replace(" ", "") for key in placement.keys())
    if isinstance(placement, str):
        return component in placement.replace(" ", "")
    return component in str(placement)


def check_structured(path: Path, data: dict[str, Any], parse_note: str | None) -> Summary:
    issues: list[Issue] = []
    if parse_note:
        severity = "ERROR" if parse_note.startswith("YAML parse error") or parse_note.startswith("YAML root") else "WARN"
        add(issues, severity, "$", parse_note)

    task_type = get(data, "runner.task_type")
    task_type_s = str(task_type) if task_type is not None else None
    env_train, env_train_from_preset = infer_env(data, "train")
    env_eval, env_eval_from_preset = infer_env(data, "eval")
    model_type, model_from_preset_flag = infer_model(data)
    adv_type = get(data, "algorithm.adv_type")
    loss_type = get(data, "algorithm.loss_type")

    if task_type_s is None:
        add(issues, "ERROR", "runner.task_type", "Missing runner.task_type; expected embodied, embodied_eval, offline, or sft for this sub-skill.")
    elif task_type_s not in VALID_TASK_TYPES:
        add(issues, "ERROR", "runner.task_type", f"Unsupported task type for embodied-workflows: {task_type_s!r}.")

    if get(data, "cluster.num_nodes") is None:
        add(issues, "WARN", "cluster.num_nodes", "Missing cluster.num_nodes; single-node defaults may be ambiguous.")

    if task_type_s in {"embodied", "embodied_eval"}:
        placement = get(data, "cluster.component_placement")
        if placement is None:
            add(issues, "ERROR", "cluster.component_placement", "Missing component placement for actor/rollout/env components.")
        else:
            required = ["env", "rollout"] + ([] if task_type_s == "embodied_eval" else ["actor"])
            for component in required:
                if not placement_mentions(placement, component):
                    add(issues, "WARN", "cluster.component_placement", f"Placement does not clearly mention component {component!r}.")
        if env_train is None and task_type_s == "embodied":
            add(issues, "WARN", "env.train", "No direct env.train.env_type or env train default preset found.")
        if env_eval is None:
            add(issues, "WARN", "env.eval", "No direct env.eval.env_type or env eval default preset found.")
        for env_value, split, from_preset in ((env_train, "train", env_train_from_preset), (env_eval, "eval", env_eval_from_preset)):
            if env_value and not from_preset and env_value not in VALID_ENV_TYPES:
                add(issues, "ERROR", f"env.{split}.env_type", f"Unknown env_type {env_value!r}.")
            if env_value and from_preset:
                add(issues, "WARN", f"env.{split}", f"Env type inferred from Hydra preset as {env_value!r}; compose config to confirm exact env_type before launch.")
        if model_type is None and task_type_s == "embodied":
            add(issues, "WARN", "actor.model", "No direct model_type or actor model default preset found.")
        elif model_type and not model_from_preset_flag and model_type not in VALID_MODEL_TYPES:
            add(issues, "ERROR", "actor.model.model_type", f"Unknown model_type {model_type!r}.")
        elif model_type and model_from_preset_flag:
            add(issues, "WARN", "actor.model", f"Model type inferred from Hydra preset as {model_type!r}; compose config to confirm exact model_type.")

        if task_type_s == "embodied":
            if loss_type is None:
                add(issues, "WARN", "algorithm.loss_type", "Missing algorithm.loss_type; actor worker selection may be ambiguous.")
            if adv_type is None:
                add(issues, "WARN", "algorithm.adv_type", "Missing algorithm.adv_type; advantage computation may be ambiguous.")

    if task_type_s == "offline":
        if get(data, "data.dataset_type") is None:
            add(issues, "WARN", "data.dataset_type", "Offline config should name dataset_type (for example d4rl).")
        if get(data, "algorithm.loss_type") is None:
            add(issues, "ERROR", "algorithm.loss_type", "Offline config needs an offline loss_type such as offline_iql.")
        eval_enabled = truthy(get(data, "runner.only_eval")) or (as_int(get(data, "runner.val_check_interval")) or -1) > 0
        if eval_enabled and env_eval is None:
            add(issues, "WARN", "env.eval", "Offline evaluation is enabled but no eval env/default was found.")

    if task_type_s == "sft":
        if get(data, "actor.training_backend") is None:
            add(issues, "WARN", "actor.training_backend", "SFT config should state fsdp/fsdp2/megatron backend.")
        if get(data, "data.train_data_paths") is None and get(data, "data.val_data_paths") is None:
            add(issues, "WARN", "data", "SFT config has no train_data_paths or val_data_paths; it may be eval-only or incomplete.")
        if model_type is None:
            add(issues, "WARN", "actor.model", "SFT config should expose actor.model.model_type or a model default preset.")

    # Common runner/log checks.
    if get(data, "runner.logger.log_path") is None and task_type_s in VALID_TASK_TYPES:
        add(issues, "WARN", "runner.logger.log_path", "Missing logger log_path; launch wrapper may override it, but static config is incomplete.")

    # Group-size and horizon compatibility.
    loss_s = str(loss_type) if loss_type is not None else ""
    adv_s = str(adv_type) if adv_type is not None else ""
    if adv_s == "grpo":
        group_size = as_int(get(data, "algorithm.group_size"))
        if group_size is None or group_size <= 1:
            add(issues, "ERROR", "algorithm.group_size", "GRPO configs should set algorithm.group_size > 1.")
        env_group_size = get(data, "env.train.group_size")
        if env_group_size is not None and str(env_group_size) != "${algorithm.group_size}":
            env_group_int = as_int(env_group_size)
            if group_size is not None and env_group_int is not None and env_group_int != group_size:
                add(issues, "WARN", "env.train.group_size", "GRPO env.train.group_size does not match algorithm.group_size.")
    if truthy(get(data, "runner.use_training_pipeline")) and loss_s in {"embodied_sac", "embodied_dagger", "embodied_nft", "rlt_ac", "rlt_td3"}:
        add(issues, "ERROR", "runner.use_training_pipeline", f"Training pipeline is not supported with loss_type {loss_s!r}.")

    num_chunks = as_int(get(data, "actor.model.num_action_chunks"))
    for split in ("train", "eval"):
        horizon = as_int(get(data, f"env.{split}.max_steps_per_rollout_epoch"))
        if num_chunks and horizon and horizon % num_chunks != 0:
            add(issues, "WARN", f"env.{split}.max_steps_per_rollout_epoch", f"{horizon} is not divisible by actor.model.num_action_chunks={num_chunks}.")

    # Reward checks.
    reward_enabled = truthy(get(data, "reward.use_reward_model"))
    if reward_enabled:
        if get(data, "reward.group_name") is None:
            add(issues, "ERROR", "reward.group_name", "Reward model enabled but reward.group_name is missing.")
        reward_model = get(data, "reward.model.model_type")
        worker_type = str(get(data, "reward.worker_type") or "model").lower()
        if reward_model is None:
            add(issues, "ERROR", "reward.model.model_type", "Reward model enabled but reward.model.model_type is missing.")
        elif str(reward_model) not in VALID_REWARD_MODELS:
            add(issues, "WARN", "reward.model.model_type", f"Reward model type {reward_model!r} is unusual; expected one of {sorted(VALID_REWARD_MODELS)}.")
        if worker_type == "api" and not get(data, "reward.api.api_base"):
            add(issues, "WARN", "reward.api.api_base", "API reward has no endpoint; managed server/router placement must be configured or endpoint provided.")
        if str(reward_model) == "buffered_vlm":
            if get(data, "reward.model.input_builder_name") is None:
                add(issues, "WARN", "reward.model.input_builder_name", "Buffered VLM reward should name an input builder.")
            if get(data, "reward.model.reward_parser_name") is None:
                add(issues, "WARN", "reward.model.reward_parser_name", "Buffered VLM reward should name a reward parser.")
            if get(data, "reward.model.history_buffers") is None:
                add(issues, "ERROR", "reward.model.history_buffers", "Buffered VLM reward needs history_buffers.")

    # Data collection and videos.
    for block_path, block in find_data_collection_blocks(data):
        if truthy(block.get("enabled")):
            if not block.get("save_dir"):
                add(issues, "ERROR", f"{block_path}.save_dir", "Enabled data_collection block needs save_dir.")
            fmt = block.get("export_format")
            if fmt is None:
                add(issues, "WARN", f"{block_path}.export_format", "Enabled data_collection block should set export_format: pickle or lerobot.")
            elif str(fmt) not in VALID_DATA_COLLECTION_FORMATS:
                add(issues, "ERROR", f"{block_path}.export_format", f"Unsupported export_format {fmt!r}.")
            if fmt == "pickle" and truthy(block.get("only_success")):
                add(issues, "WARN", f"{block_path}.only_success", "pickle reward-data collection with only_success=True may remove negative examples.")
    for block_path, block in find_video_blocks(data):
        if truthy(block.get("save_video")) and not block.get("video_base_dir"):
            add(issues, "ERROR", f"{block_path}.video_base_dir", "save_video=True requires video_base_dir.")

    # Placeholder checks.
    for scalar_path, value in flatten_scalars(data):
        if isinstance(value, str) and any(pattern.search(value) for pattern in PLACEHOLDER_PATTERNS):
            add(issues, "WARN", scalar_path, f"Placeholder-like value remains: {value!r}.")

    # Env-family special checks.
    families = {x for x in (env_train, env_eval) if x}
    if any(fam in {"realworld", "frankasim"} for fam in families) or "realworld" in path.name.lower():
        add(issues, "WARN", "realworld.safety", "Real-world/hardware configs require operator approval, e-stop readiness, and dummy/read-only validation before live robot motion.")
        if "realworld" in families:
            node_count = as_int(get(data, "cluster.num_nodes"))
            if node_count is not None and node_count < 2 and not truthy(get(data, "env.train.override_cfg.is_dummy")):
                add(issues, "WARN", "cluster.num_nodes", "Real-world training commonly needs a GPU node plus control node; verify single-node setup is intentional/dummy.")
    if any(fam == "behavior" for fam in families):
        add(issues, "WARN", "behavior.assets", "BEHAVIOR configs need OmniGibson/Isaac Sim data/key paths and headless env variables before Ray starts.")
    if any(fam in {"opensora_wm", "wan_wm"} for fam in families):
        text_values = "\n".join(str(v) for _, v in flatten_scalars(data) if isinstance(v, str)).lower()
        if "wm_hf_ckpt_path" not in text_values and "opensora" not in text_values and "wan" not in text_values:
            add(issues, "WARN", "env.train", "World-model env inferred but no obvious world-model checkpoint field was found.")
    if any(fam == "isaaclab" for fam in families) and get(data, "env.train.init_params.id") is None and get(data, "env.eval.init_params.id") is None:
        add(issues, "WARN", "env.*.init_params.id", "IsaacLab configs require a registered task id.")

    errors = sum(1 for issue in issues if issue.severity == "ERROR")
    warnings = sum(1 for issue in issues if issue.severity == "WARN")
    return Summary(
        file=str(path),
        task_type=task_type_s,
        env_train=env_train,
        env_eval=env_eval,
        model_type=model_type,
        adv_type=str(adv_type) if adv_type is not None else None,
        loss_type=str(loss_type) if loss_type is not None else None,
        errors=errors,
        warnings=warnings,
        issues=issues,
    )


def check_text_only(path: Path, note: str | None) -> Summary:
    text = read_text(path)
    issues: list[Issue] = []
    if note:
        add(issues, "WARN", "$", note)
    if "runner:" not in text:
        add(issues, "WARN", "runner", "No runner block found by text scan.")
    if "task_type:" not in text:
        add(issues, "WARN", "runner.task_type", "No task_type found by text scan.")
    if "cluster:" not in text:
        add(issues, "WARN", "cluster", "No cluster block found by text scan.")
    if "component_placement" not in text and "task_type: offline" not in text:
        add(issues, "WARN", "cluster.component_placement", "No component_placement found by text scan.")
    if "env/" not in text and "env_type" not in text and "task_type: sft" not in text:
        add(issues, "WARN", "env", "No env default or env_type found by text scan.")
    if "model/" not in text and "model_type" not in text:
        add(issues, "WARN", "actor.model", "No model default or model_type found by text scan.")
    if "/path/to/" in text or "ROBOT_IP" in text or "TARGET_EE_POSE" in text:
        add(issues, "WARN", "placeholders", "Placeholder-like values found by text scan.")
    return Summary(
        file=str(path),
        task_type=None,
        env_train=None,
        env_eval=None,
        model_type=None,
        adv_type=None,
        loss_type=None,
        errors=0,
        warnings=sum(1 for issue in issues if issue.severity == "WARN"),
        issues=issues,
    )


def print_summary(summary: Summary) -> None:
    print(f"File: {summary.file}")
    print(
        "Summary: "
        f"task_type={summary.task_type or '?'} "
        f"env.train={summary.env_train or '?'} "
        f"env.eval={summary.env_eval or '?'} "
        f"model={summary.model_type or '?'} "
        f"adv={summary.adv_type or '?'} "
        f"loss={summary.loss_type or '?'}"
    )
    if not summary.issues:
        print("OK: no issues found by static checks.")
        return
    for issue in summary.issues:
        print(f"{issue.severity}: {issue.path}: {issue.message}")
    print(f"Totals: {summary.errors} error(s), {summary.warnings} warning(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statically sanity-check an RLinf embodied/offline/SFT YAML config without launching training."
    )
    parser.add_argument("config", help="Path to a YAML config file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings are present.")
    args = parser.parse_args(argv)

    path = Path(args.config).expanduser()
    if not path.exists():
        print(f"error: config does not exist: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"error: config is not a file: {path}", file=sys.stderr)
        return 2

    data, note = load_yaml(path)
    if yaml is None:
        summary = check_text_only(path, note)
    else:
        summary = check_structured(path, data, note)

    if args.json:
        payload = asdict(summary)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_summary(summary)

    if summary.errors:
        return 1
    if args.strict and summary.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
