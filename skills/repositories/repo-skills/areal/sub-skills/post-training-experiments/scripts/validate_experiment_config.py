#!/usr/bin/env python3
"""Safely validate an AReaL experiment config without launching training.

This helper imports AReaL, composes the supplied YAML with Hydra-style overrides,
instantiates the requested config dataclass, and checks high-value experiment-family
invariants. It does not create schedulers, workers, inference services, datasets,
models, downloads, or training loops.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings as warnings_module
from pathlib import Path
from typing import Any


_KIND_ALIASES = {
    "grpo": "grpo",
    "ppo": "ppo",
    "sft": "sft",
    "dpo": "dpo",
    "rw": "rw",
    "rm": "rw",
    "reward-model": "rw",
    "reward_model": "rw",
}

_TRAIN_BACKENDS = {"fsdp", "megatron", "archon"}
_ROLLOUT_BACKENDS = {"sglang", "vllm"}
_VALID_SCHEDULERS = {"local", "ray", "slurm"}
_RECOVER_ENABLED = {"on", "auto"}


class Finding:
    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint

    def as_dict(self) -> dict[str, str]:
        result = {"message": self.message}
        if self.hint:
            result["hint"] = self.hint
        return result


def _normalize_kind(kind: str) -> str:
    normalized = _KIND_ALIASES.get(kind.lower())
    if normalized is None:
        valid = ", ".join(sorted(_KIND_ALIASES))
        raise argparse.ArgumentTypeError(f"unknown kind {kind!r}; choose one of: {valid}")
    return normalized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an AReaL GRPO/PPO/SFT/DPO/RW config and overrides without "
            "starting workers, services, downloads, or training."
        )
    )
    parser.add_argument(
        "--kind",
        required=True,
        type=_normalize_kind,
        help="Experiment family: grpo, ppo, sft, dpo, rw/rm/reward-model.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML config consumed by the AReaL entrypoint.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures.",
    )
    parser.add_argument(
        "--no-gpu-budget-check",
        action="store_true",
        help="Skip physical GPU budget checks derived from backend strings.",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Print raw model/dataset/fileroot paths in the summary. Defaults to redacted.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print the fully merged config as YAML. May contain user paths and secrets.",
    )
    parser.add_argument(
        "overrides",
        nargs=argparse.REMAINDER,
        help=(
            "Hydra-style overrides to pass after --config, e.g. "
            "scheduler.type=local actor.path=Qwen/Qwen3-1.7B "
            "+sglang.attention_backend=triton. If needed, insert -- before overrides."
        ),
    )
    return parser


def _strip_separator(overrides: list[str]) -> list[str]:
    if overrides and overrides[0] == "--":
        return overrides[1:]
    return overrides


def _is_config_warning(item: warnings_module.WarningMessage) -> bool:
    """Keep AReaL config warnings, suppress import-time deprecation noise."""

    message = str(item.message)
    if issubclass(item.category, DeprecationWarning):
        return False
    noisy_prefixes = (
        "uvloop.install() is deprecated",
        "register_new_resolver() is deprecated",
    )
    return not message.startswith(noisy_prefixes)


def _load_areal_config(kind: str, config_path: str, overrides: list[str]):
    try:
        from omegaconf import OmegaConf

        from areal.api.cli_args import (
            DPOConfig,
            GRPOConfig,
            PPOConfig,
            RWConfig,
            SFTConfig,
            parse_cli_args,
            to_structured_cfg,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Could not import AReaL config APIs. Activate an environment where the "
            "AReaL package and its config dependencies are installed."
        ) from exc

    class_map = {
        "grpo": GRPOConfig,
        "ppo": PPOConfig,
        "sft": SFTConfig,
        "dpo": DPOConfig,
        "rw": RWConfig,
    }
    config_cls = class_map[kind]
    argv = ["--config", config_path, *overrides]
    cfg, resolved_config_path = parse_cli_args(argv)
    structured = to_structured_cfg(cfg, config_cls=config_cls)
    obj = OmegaConf.to_object(structured)
    if not isinstance(obj, config_cls):
        raise TypeError(
            f"Merged config became {type(obj).__name__}, expected {config_cls.__name__}."
        )
    return obj, str(resolved_config_path), config_cls.__name__, structured


def _as_text(value: Any) -> str:
    if value is None:
        return "null"
    return str(value)


def _path_value(value: Any, show_paths: bool) -> str:
    if value in (None, ""):
        return "<empty>"
    return str(value) if show_paths else "<set>"


def _strategy_type(role_cfg: Any) -> str:
    strategy = getattr(role_cfg, "scheduling_strategy", None)
    return str(getattr(strategy, "type", "separation"))


def _is_colocated(role_cfg: Any) -> bool:
    return _strategy_type(role_cfg) == "colocation"


def _target(role_cfg: Any) -> str | None:
    strategy = getattr(role_cfg, "scheduling_strategy", None)
    target = getattr(strategy, "target", None)
    return None if target in (None, "") else str(target)


def _parse_allocation(role: str, role_cfg: Any, issues: list[Finding]):
    try:
        from areal.api.alloc_mode import ModelAllocation
    except Exception as exc:  # noqa: BLE001
        issues.append(
            Finding(
                "Could not import AReaL allocation parser.",
                "Check that areal.api.alloc_mode imports in the active environment.",
            )
        )
        return None

    backend_spec = getattr(role_cfg, "backend", None)
    if not backend_spec:
        issues.append(Finding(f"{role}.backend is required but empty."))
        return None
    try:
        return ModelAllocation.from_str(
            str(backend_spec),
            name=role,
            scheduling_strategy=getattr(role_cfg, "scheduling_strategy", None),
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(
            Finding(
                f"{role}.backend={backend_spec!r} could not be parsed: {exc}",
                "Use one explicit per-role backend string such as fsdp:d4, megatron:d4t2, archon:d8, sglang:d4, or vllm:d2t4.",
            )
        )
        return None


def _role_summary(role: str, role_type: str, role_cfg: Any, alloc: Any | None) -> dict[str, Any]:
    return {
        "role": role,
        "type": role_type,
        "backend": getattr(role_cfg, "backend", None),
        "parsed_backend": getattr(alloc, "backend", None) if alloc is not None else None,
        "parallel": str(getattr(alloc, "parallel", "")) if alloc is not None else None,
        "world_size": getattr(getattr(alloc, "parallel", None), "world_size", None),
        "physical_world_size": getattr(alloc, "world_size", None) if alloc is not None else None,
        "scheduling_strategy": _strategy_type(role_cfg),
        "target": _target(role_cfg),
    }


def _iter_roles(kind: str, config: Any) -> list[tuple[str, str, Any]]:
    roles: list[tuple[str, str, Any]] = []

    if kind in {"grpo", "ppo"}:
        roles.append(("rollout", "rollout", config.rollout))
        roles.append(("actor", "train", config.actor))
        if getattr(config, "critic", None) is not None:
            roles.append(("critic", "train", config.critic))
        # PPOTrainer creates a ref only when KL control is active.
        if getattr(config, "ref", None) is not None and getattr(config.actor, "kl_ctl", 0) > 0:
            roles.append(("ref", "train", config.ref))
        teacher = getattr(config, "teacher", None)
        if teacher is not None:
            if getattr(teacher, "engine_type", "rollout") == "rollout" and teacher.rollout is not None:
                roles.append(("teacher.rollout", "rollout", teacher.rollout))
            elif getattr(teacher, "engine_type", "rollout") == "train" and teacher.train is not None:
                roles.append(("teacher.train", "train", teacher.train))
    elif kind == "sft":
        roles.append(("actor", "train", config.actor))
    elif kind == "dpo":
        roles.append(("actor", "train", config.actor))
        roles.append(("ref", "train", config.ref))
    elif kind == "rw":
        roles.append(("actor", "train", config.actor))
    return roles


def _dataset_summary(config: Any, show_paths: bool) -> dict[str, Any]:
    def one(ds: Any | None) -> dict[str, Any] | None:
        if ds is None:
            return None
        return {
            "type": getattr(ds, "type", None),
            "path": _path_value(getattr(ds, "path", None), show_paths),
            "split": getattr(ds, "split", None),
            "batch_size": getattr(ds, "batch_size", None),
            "max_length": getattr(ds, "max_length", None),
            "num_workers": getattr(ds, "num_workers", None),
            "drop_last": getattr(ds, "drop_last", None),
        }

    return {"train": one(getattr(config, "train_dataset", None)), "valid": one(getattr(config, "valid_dataset", None))}


def _check_dataset_types(kind: str, config: Any, issues: list[Finding], warn: list[Finding]) -> None:
    expected = {"grpo": "rl", "ppo": "rl", "sft": "sft", "dpo": "dpo", "rw": "rw"}[kind]
    for name in ("train_dataset", "valid_dataset"):
        ds = getattr(config, name, None)
        if ds is None:
            if name == "train_dataset" and kind != "grpo":
                issues.append(Finding(f"{name} is required for {kind.upper()} planning."))
            continue
        ds_type = getattr(ds, "type", None)
        if ds_type != expected:
            severity_list = issues if name == "train_dataset" else warn
            severity_list.append(
                Finding(
                    f"{name}.type is {ds_type!r}, expected {expected!r} for {kind.upper()}.",
                    "Use the matching built-in dataset type, or route custom data preprocessing to the custom data/reward/workflow skill.",
                )
            )


def _check_common(kind: str, config: Any, issues: list[Finding], warn: list[Finding]) -> None:
    scheduler_type = getattr(getattr(config, "scheduler", None), "type", None)
    if scheduler_type not in _VALID_SCHEDULERS:
        issues.append(
            Finding(
                f"scheduler.type is {scheduler_type!r}; launch-time scheduler must be one of {sorted(_VALID_SCHEDULERS)}.",
                "Add scheduler.type=local, scheduler.type=ray, or scheduler.type=slurm to the overrides.",
            )
        )
    elif scheduler_type in {"ray", "slurm"} and getattr(config.cluster, "n_nodes", 1) <= 1:
        warn.append(
            Finding(
                f"scheduler.type={scheduler_type!r} with cluster.n_nodes<=1.",
                "This can work only in special setups; most Ray/Slurm experiments are multi-node and need shared storage.",
            )
        )

    for attr_name in ("experiment_name", "trial_name"):
        value = getattr(config, attr_name, "")
        if not value:
            issues.append(Finding(f"{attr_name} is required."))
        elif "/" in str(value):
            issues.append(Finding(f"{attr_name} must not contain '/': {value!r}."))

    if getattr(config, "total_train_epochs", 1) <= 0:
        issues.append(Finding("total_train_epochs must be positive."))

    if scheduler_type in {"ray", "slurm"}:
        fileroot = str(getattr(config.cluster, "fileroot", ""))
        nfs_root = str(getattr(getattr(config.cluster, "name_resolve", None), "nfs_record_root", ""))
        if fileroot.startswith("/tmp") or nfs_root.startswith("/tmp"):
            warn.append(
                Finding(
                    "Ray/Slurm plan uses /tmp-like fileroot or name-resolution root.",
                    "Use storage shared by every node for cluster.fileroot and cluster.name_resolve.nfs_record_root.",
                )
            )

    _check_dataset_types(kind, config, issues, warn)


def _check_train_engine(role: str, role_cfg: Any, alloc: Any | None, issues: list[Finding], warn: list[Finding]) -> None:
    if alloc is not None and alloc.backend not in _TRAIN_BACKENDS:
        issues.append(
            Finding(
                f"{role}.backend uses {alloc.backend!r}; training roles require one of {sorted(_TRAIN_BACKENDS)}."
            )
        )
    if getattr(role_cfg, "logprobs_chunk_size", 1024) <= 0:
        issues.append(Finding(f"{role}.logprobs_chunk_size must be positive."))
    if getattr(role_cfg, "init_from_scratch", False) and getattr(getattr(role_cfg, "fsdp", None), "memory_efficient_load", False):
        issues.append(
            Finding(
                f"{role}.fsdp.memory_efficient_load cannot be combined with {role}.init_from_scratch=true."
            )
        )
    if not getattr(role_cfg, "init_from_scratch", False) and not getattr(role_cfg, "path", ""):
        warn.append(
            Finding(
                f"{role}.path is empty while init_from_scratch=false.",
                "Set a Hugging Face model id or local checkpoint before launch.",
            )
        )
    opt = getattr(role_cfg, "optimizer", None)
    if role in {"ref", "teacher.train"} and opt is not None:
        warn.append(Finding(f"{role}.optimizer is not null; reference/teacher train roles are usually frozen."))


def _check_rollout(role: str, role_cfg: Any, alloc: Any | None, issues: list[Finding], warn: list[Finding]) -> None:
    if alloc is not None and alloc.backend not in _ROLLOUT_BACKENDS:
        issues.append(
            Finding(
                f"{role}.backend uses {alloc.backend!r}; rollout roles require one of {sorted(_ROLLOUT_BACKENDS)}."
            )
        )
    if getattr(role_cfg, "return_routed_experts", False) and alloc is not None and alloc.backend == "vllm":
        issues.append(
            Finding(
                f"{role}.return_routed_experts is SGLang-only and cannot be used with vLLM."
            )
        )
    if getattr(role_cfg, "consumer_batch_size", None) != getattr(getattr(role_cfg, "agent", None), "consumer_batch_size", getattr(role_cfg, "consumer_batch_size", None)):
        # Reserved for future agent-specific checks; kept intentionally no-op for current AReaL versions.
        pass


def _check_grpo_ppo(kind: str, config: Any, allocations: dict[str, Any], issues: list[Finding], warn: list[Finding]) -> None:
    has_critic = getattr(config, "critic", None) is not None
    if kind == "grpo" and has_critic:
        warn.append(Finding("GRPOConfig has a critic section; that makes the run PPO-like."))
    if kind == "ppo" and not has_critic:
        issues.append(Finding("PPO experiments require a critic section."))

    actor = config.actor
    rollout = config.rollout
    actor_alloc = allocations.get("actor")
    rollout_alloc = allocations.get("rollout")

    if getattr(actor, "_version", "v1") != getattr(rollout, "_version", "v1"):
        issues.append(
            Finding(
                f"actor._version={getattr(actor, '_version', None)!r} and rollout._version={getattr(rollout, '_version', None)!r} must match."
            )
        )

    if getattr(actor, "use_sapo_loss", False) and getattr(actor, "use_decoupled_loss", False):
        issues.append(Finding("SAPO is not compatible with actor.use_decoupled_loss=true."))

    if getattr(actor, "use_cispo_loss", False):
        if getattr(actor, "eps_clip_higher", None) is None or getattr(actor, "eps_clip_higher", 0) <= 0:
            issues.append(Finding("CISPO requires a positive actor.eps_clip_higher."))
        if getattr(actor, "importance_sampling_level", "token") != "token":
            issues.append(Finding("CISPO requires actor.importance_sampling_level=token."))

    if getattr(actor, "use_decoupled_loss", False) and getattr(actor, "rejection_sampling", None) is None:
        warn.append(
            Finding(
                "actor.use_decoupled_loss=true but actor.rejection_sampling is null.",
                "Staleness filtering is disabled. Add token mask ratio filtering unless that is intentional.",
            )
        )

    reward_norm = getattr(actor, "reward_norm", None)
    if reward_norm is not None and getattr(reward_norm, "mean_level", None) == "group" and getattr(reward_norm, "group_size", 1) == 1:
        warn.append(
            Finding(
                "actor.reward_norm uses group mean centering with group_size=1.",
                "This erases singleton task rewards; use group_size>=2 or mean_level=null.",
            )
        )

    if getattr(getattr(config, "gconfig", None), "reward_normalization", False) and reward_norm is not None:
        issues.append(
            Finding(
                "gconfig.reward_normalization and actor.reward_norm are both enabled.",
                "Enable only rollout-time or training-time reward normalization.",
            )
        )

    actor_rollout_colocated = (
        _is_colocated(actor) and _target(actor) == "rollout"
    ) or (_is_colocated(rollout) and _target(rollout) == "actor")
    any_train_offload = any(
        bool(getattr(role, "offload", False))
        for role in (actor, getattr(config, "critic", None), getattr(config, "ref", None))
        if role is not None
    )
    if (actor_rollout_colocated or any_train_offload) and not getattr(config, "enable_offload", False):
        issues.append(
            Finding(
                "enable_offload must be true when actor-rollout colocation or train-engine offload is enabled."
            )
        )
    if actor_rollout_colocated and getattr(actor, "weight_update_mode", "xccl") not in {"disk", "awex"}:
        issues.append(
            Finding(
                "actor-rollout colocation requires actor.weight_update_mode to be disk or awex."
            )
        )

    if getattr(actor, "weight_update_mode", None) == "awex":
        if actor_alloc is not None and actor_alloc.backend != "megatron":
            issues.append(Finding("actor.weight_update_mode=awex requires a Megatron actor backend."))
        if rollout_alloc is not None and rollout_alloc.backend != "sglang":
            issues.append(Finding("actor.weight_update_mode=awex requires an SGLang rollout backend."))

    if getattr(actor, "use_lora", False):
        if actor_alloc is not None and actor_alloc.backend != "fsdp":
            issues.append(Finding("actor.use_lora is supported for FSDP actors; switch actor.backend to fsdp or disable LoRA."))
        if not getattr(rollout, "use_lora", False):
            warn.append(Finding("actor.use_lora=true but rollout.use_lora=false; rollout may not serve the adapter."))
        if getattr(getattr(config, "gconfig", None), "lora_name", "") == "":
            warn.append(Finding("LoRA is enabled but gconfig.lora_name is empty; set a stable adapter name."))

    if actor_alloc is not None and rollout_alloc is not None:
        if actor_alloc.backend == "megatron" and getattr(actor, "use_lora", False) and rollout_alloc.backend == "sglang":
            issues.append(
                Finding(
                    "Megatron actor with LoRA is not supported with SGLang rollout in PPOTrainer.",
                    "Use vLLM rollout, disable LoRA, or switch actor backend to FSDP.",
                )
            )

    if getattr(config, "ref", None) is not None and getattr(actor, "kl_ctl", 0) <= 0:
        warn.append(Finding("ref is configured but actor.kl_ctl<=0, so PPOTrainer will not create the reference role."))

    train_bs = getattr(getattr(config, "train_dataset", None), "batch_size", None)
    consumer_bs = getattr(rollout, "consumer_batch_size", None)
    if train_bs is not None and consumer_bs is not None and train_bs != consumer_bs:
        warn.append(
            Finding(
                f"rollout.consumer_batch_size={consumer_bs} differs from train_dataset.batch_size={train_bs}.",
                "Most examples set rollout.consumer_batch_size to the train batch size.",
            )
        )


def _check_sft(config: Any, issues: list[Finding], warn: list[Finding]) -> None:
    if getattr(config, "recover", None) is not None and getattr(config.recover, "mode", "disabled") in _RECOVER_ENABLED:
        if getattr(config.actor, "_version", "v1") == "v2":
            issues.append(Finding("Recovery is not supported with actor._version=v2 train controllers."))


def _check_dpo(config: Any, issues: list[Finding], warn: list[Finding]) -> None:
    if getattr(config.actor, "is_critic", False):
        issues.append(Finding("DPO requires actor.is_critic=false."))
    if not getattr(config.actor, "disable_dropout", False):
        warn.append(Finding("DPO should set actor.disable_dropout=true for stable log-prob comparisons."))
    if getattr(getattr(config.actor, "mb_spec", None), "granularity", None) != 2:
        issues.append(Finding("DPO requires actor.mb_spec.granularity=2 to keep chosen/rejected pairs together."))
    if getattr(config.actor, "loss_type", "sigmoid") not in {"sigmoid", "ipo"}:
        issues.append(Finding("DPO actor.loss_type must be sigmoid or ipo."))
    if getattr(config.ref, "optimizer", None) is not None:
        issues.append(Finding("DPO ref.optimizer must be null so the reference model stays frozen."))
    if getattr(config.recover, "mode", "disabled") in _RECOVER_ENABLED and getattr(config.actor, "_version", "v1") == "v2":
        issues.append(Finding("Recovery is not supported with actor._version=v2 train controllers."))


def _check_rw(config: Any, issues: list[Finding], warn: list[Finding]) -> None:
    if not getattr(config.actor, "is_critic", False):
        issues.append(Finding("RW requires actor.is_critic=true."))
    if getattr(config.recover, "mode", "disabled") in _RECOVER_ENABLED and getattr(config.actor, "_version", "v1") == "v2":
        issues.append(Finding("Recovery is not supported with actor._version=v2 train controllers."))


def _check_gpu_budget(
    config: Any,
    role_summaries: list[dict[str, Any]],
    issues: list[Finding],
    warn: list[Finding],
) -> None:
    cluster = getattr(config, "cluster", None)
    if cluster is None:
        return
    n_nodes = getattr(cluster, "n_nodes", None)
    gpus_per_node = getattr(cluster, "n_gpus_per_node", None)
    if n_nodes is None or gpus_per_node is None:
        return
    try:
        physical_budget = int(n_nodes) * int(gpus_per_node)
    except Exception:  # noqa: BLE001
        warn.append(Finding("Could not compute cluster GPU budget from n_nodes and n_gpus_per_node."))
        return

    required = 0
    for summary in role_summaries:
        value = summary.get("physical_world_size")
        if value is not None:
            required += int(value)
    if required > physical_budget:
        issues.append(
            Finding(
                f"Backend plan requires {required} physical GPUs but cluster budget is {physical_budget}.",
                "Adjust backend strings, colocation, cluster.n_nodes, or cluster.n_gpus_per_node before launch.",
            )
        )
    elif required < physical_budget:
        warn.append(
            Finding(
                f"Backend plan accounts for {required} physical GPUs while cluster budget is {physical_budget}.",
                "This may be intentional underutilization; otherwise adjust backend strings or cluster fields.",
            )
        )


def _validate(kind: str, config: Any, *, check_gpu_budget: bool, show_paths: bool) -> dict[str, Any]:
    issues: list[Finding] = []
    warn: list[Finding] = []

    _check_common(kind, config, issues, warn)

    roles = _iter_roles(kind, config)
    allocations: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    for role, role_type, role_cfg in roles:
        alloc = _parse_allocation(role, role_cfg, issues)
        allocations[role] = alloc
        summaries.append(_role_summary(role, role_type, role_cfg, alloc))
        if role_type == "train":
            _check_train_engine(role, role_cfg, alloc, issues, warn)
        else:
            _check_rollout(role, role_cfg, alloc, issues, warn)

    if kind in {"grpo", "ppo"}:
        _check_grpo_ppo(kind, config, allocations, issues, warn)
    elif kind == "sft":
        _check_sft(config, issues, warn)
    elif kind == "dpo":
        _check_dpo(config, issues, warn)
    elif kind == "rw":
        _check_rw(config, issues, warn)

    if check_gpu_budget:
        _check_gpu_budget(config, summaries, issues, warn)

    summary = {
        "kind": kind,
        "experiment_name": getattr(config, "experiment_name", None),
        "trial_name": getattr(config, "trial_name", None),
        "scheduler_type": getattr(getattr(config, "scheduler", None), "type", None),
        "cluster": {
            "n_nodes": getattr(getattr(config, "cluster", None), "n_nodes", None),
            "n_gpus_per_node": getattr(getattr(config, "cluster", None), "n_gpus_per_node", None),
            "fileroot": _path_value(getattr(getattr(config, "cluster", None), "fileroot", None), show_paths),
        },
        "datasets": _dataset_summary(config, show_paths),
        "roles": summaries,
        "logging": {
            "wandb_mode": getattr(getattr(getattr(config, "stats_logger", None), "wandb", None), "mode", None),
            "swanlab_mode": getattr(getattr(getattr(config, "stats_logger", None), "swanlab", None), "mode", None),
            "trackio_mode": getattr(getattr(getattr(config, "stats_logger", None), "trackio", None), "mode", None),
            "tensorboard_path": _path_value(getattr(getattr(getattr(config, "stats_logger", None), "tensorboard", None), "path", None), show_paths),
        },
        "recovery": {
            "mode": getattr(getattr(config, "recover", None), "mode", None),
            "retries": getattr(getattr(config, "recover", None), "retries", None),
            "freq_epochs": getattr(getattr(config, "recover", None), "freq_epochs", None),
            "freq_steps": getattr(getattr(config, "recover", None), "freq_steps", None),
            "freq_secs": getattr(getattr(config, "recover", None), "freq_secs", None),
        },
    }

    return {
        "summary": summary,
        "issues": [item.as_dict() for item in issues],
        "warnings": [item.as_dict() for item in warn],
    }


def _print_human(report: dict[str, Any], *, strict: bool, config_class: str, config_path: str, captured_warnings: list[str]) -> None:
    summary = report["summary"]
    issues = report["issues"]
    warn = report["warnings"]

    print("AReaL experiment config validation")
    print(f"  config: {config_path}")
    print(f"  kind: {summary['kind']} ({config_class})")
    print(f"  experiment/trial: {summary['experiment_name']} / {summary['trial_name']}")
    print(f"  scheduler: {summary['scheduler_type']}")
    cluster = summary["cluster"]
    print(
        "  cluster: "
        f"nodes={cluster['n_nodes']} gpus_per_node={cluster['n_gpus_per_node']} "
        f"fileroot={cluster['fileroot']}"
    )

    print("\nDatasets:")
    for name, ds in summary["datasets"].items():
        if ds is None:
            print(f"  {name}: null")
            continue
        print(
            f"  {name}: type={ds['type']} path={ds['path']} split={ds['split']} "
            f"batch_size={ds['batch_size']} max_length={ds['max_length']}"
        )

    print("\nRoles:")
    if not summary["roles"]:
        print("  <none>")
    for role in summary["roles"]:
        print(
            f"  {role['role']}: type={role['type']} backend={role['backend']} "
            f"parallel={role['parallel']} world={role['world_size']} "
            f"physical={role['physical_world_size']} scheduling={role['scheduling_strategy']}"
            + (f" target={role['target']}" if role.get("target") else "")
        )

    print("\nLogging:")
    logging = summary["logging"]
    print(
        f"  wandb={logging['wandb_mode']} swanlab={logging['swanlab_mode']} "
        f"trackio={logging['trackio_mode']} tensorboard_path={logging['tensorboard_path']}"
    )

    print("\nRecovery:")
    recovery = summary["recovery"]
    print(
        f"  mode={recovery['mode']} retries={recovery['retries']} "
        f"freq_epochs={recovery['freq_epochs']} freq_steps={recovery['freq_steps']} "
        f"freq_secs={recovery['freq_secs']}"
    )

    if captured_warnings:
        print("\nAReaL/dataclass warnings:")
        for item in captured_warnings:
            print(f"  - {item}")

    print("\nValidation issues:")
    if not issues:
        print("  none")
    for item in issues:
        print(f"  - {item['message']}")
        if item.get("hint"):
            print(f"    hint: {item['hint']}")

    print("\nWarnings:")
    if not warn:
        print("  none")
    for item in warn:
        print(f"  - {item['message']}")
        if item.get("hint"):
            print(f"    hint: {item['hint']}")

    ok = not issues and (not strict or not warn and not captured_warnings)
    print("\nResult: " + ("PASS" if ok else "FAIL"))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    overrides = _strip_separator(args.overrides)
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        message = f"Config file does not exist: {config_path}"
        if args.json:
            print(json.dumps({"status": "failed", "error": message}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2

    captured_warnings: list[str] = []
    try:
        with warnings_module.catch_warnings(record=True) as caught:
            warnings_module.simplefilter("always")
            config, resolved_config_path, config_class, structured = _load_areal_config(
                args.kind, str(config_path), overrides
            )
            captured_warnings = [str(item.message) for item in caught if _is_config_warning(item)]
    except Exception as exc:  # noqa: BLE001
        hint = (
            "Config composition or dataclass construction failed. Check removed keys, "
            "unknown override paths, missing mandatory fields, invalid enum choices, and "
            "backend-specific config validation errors."
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "stage": "compose",
                        "error": str(exc),
                        "hint": hint,
                    },
                    indent=2,
                )
            )
        else:
            print("AReaL experiment config validation", file=sys.stderr)
            print(f"  config: {config_path}", file=sys.stderr)
            print(f"  kind: {args.kind}", file=sys.stderr)
            print("\nERROR during config composition:", file=sys.stderr)
            print(f"  {exc}", file=sys.stderr)
            print(f"\nHint: {hint}", file=sys.stderr)
        return 2

    report = _validate(
        args.kind,
        config,
        check_gpu_budget=not args.no_gpu_budget_check,
        show_paths=args.show_paths,
    )
    report["arealWarnings"] = captured_warnings
    report["configClass"] = config_class
    report["configPath"] = resolved_config_path

    if args.print_config:
        try:
            from omegaconf import OmegaConf

            report["mergedConfigYaml"] = OmegaConf.to_yaml(structured, resolve=True)
        except Exception as exc:  # noqa: BLE001
            report["mergedConfigYamlError"] = str(exc)

    failed = bool(report["issues"]) or (
        args.strict and (bool(report["warnings"]) or bool(captured_warnings))
    )
    report["status"] = "failed" if failed else "ok"

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(
            report,
            strict=args.strict,
            config_class=config_class,
            config_path=resolved_config_path,
            captured_warnings=captured_warnings,
        )
        if args.print_config and "mergedConfigYaml" in report:
            print("\nMerged config YAML:")
            print(report["mergedConfigYaml"])

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
