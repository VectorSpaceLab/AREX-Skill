#!/usr/bin/env python3
"""Safely inspect an OpenPrompt training/generation config.

This helper parses and summarizes runner selection, config choices, backend
expectations, checkpoint/logging behavior, and common path requirements. It does
not load datasets, load pretrained models, construct dataloaders, or start
training.
"""

import argparse
import json
import os
import sys
import warnings as py_warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


def cfg_to_plain(value: Any) -> Any:
    """Convert yacs CfgNode / mappings / containers into JSON-friendly values."""
    if isinstance(value, Mapping):
        return {str(k): cfg_to_plain(v) for k, v in value.items()}
    if hasattr(value, "items") and callable(value.items):
        try:
            return {str(k): cfg_to_plain(v) for k, v in value.items()}
        except Exception:
            pass
    if isinstance(value, (list, tuple)):
        return [cfg_to_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def deep_get(cfg: Mapping[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = cfg
    for part in dotted.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def coalesce(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value is not None:
            return value
    return default


def parse_yaml_only(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("PyYAML/yacs is required for raw YAML parsing") from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, Mapping):
        raise ValueError(f"Expected a mapping at top level of {path}")
    return cfg_to_plain(data)


def load_config(config_path: Path, repo_root: Path, use_openprompt_merge: bool) -> Tuple[Dict[str, Any], str, List[str]]:
    warnings: List[str] = []
    if use_openprompt_merge:
        sys.path.insert(0, str(repo_root))
        try:
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("ignore")
                from openprompt.config import get_user_config  # type: ignore

                cfg = get_user_config(str(config_path))
            return cfg_to_plain(cfg), "openprompt.config.get_user_config", warnings
        except Exception as exc:
            warnings.append(
                "OpenPrompt config merge failed; falling back to raw YAML. "
                f"Merged defaults/conditional nodes may be incomplete. Error: {exc}"
            )
    return parse_yaml_only(config_path), "raw YAML only", warnings


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def detect_runner(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    task = deep_get(cfg, "task", "classification")
    classification = deep_get(cfg, "classification", {}) or {}
    auto_t = normalize_bool(deep_get(classification, "auto_t", False)) if isinstance(classification, Mapping) else False
    auto_v = normalize_bool(deep_get(classification, "auto_v", False)) if isinstance(classification, Mapping) else False
    verbalizer = deep_get(cfg, "verbalizer")

    if task == "classification":
        if auto_t or auto_v:
            runner = "LMBFFClassificationRunner"
            reason = "task=classification and classification.auto_t/auto_v is enabled"
        elif verbalizer == "proto_verbalizer":
            runner = "ProtoVerbClassificationRunner"
            reason = "task=classification and verbalizer=proto_verbalizer"
        else:
            runner = "ClassificationRunner"
            reason = "task=classification with no LM-BFF or ProtoVerb selector"
    elif task == "generation":
        runner = "GenerationRunner"
        reason = "task=generation"
    else:
        runner = "unsupported"
        reason = f"experiments/cli.py does not implement task={task!r}"

    learning_setting = deep_get(cfg, "learning_setting")
    if learning_setting == "full":
        learning_flow = "single full-data trainer() call"
    elif learning_setting == "few_shot":
        learning_flow = "FewShotSampler over sampling_from_train.seed, one child run per seed"
    elif learning_setting == "zero_shot":
        learning_flow = "construct model/dataloaders and call runner.test() without fit()"
    else:
        learning_flow = "not one of experiments/cli.py branches"

    return {
        "task": task,
        "runner": runner,
        "reason": reason,
        "learning_setting": learning_setting,
        "learning_flow": learning_flow,
        "auto_t": auto_t,
        "auto_v": auto_v,
        "verbalizer": verbalizer,
        "template": deep_get(cfg, "template"),
    }


def summarize_backend(cfg: Mapping[str, Any], probe_torch: bool) -> Dict[str, Any]:
    env = deep_get(cfg, "environment", {}) or {}
    num_gpus = int(coalesce(deep_get(env, "num_gpus"), 1)) if isinstance(env, Mapping) else 1
    cuda_visible_devices = deep_get(env, "cuda_visible_devices") if isinstance(env, Mapping) else None
    local_rank = int(coalesce(deep_get(env, "local_rank"), 0)) if isinstance(env, Mapping) else 0
    model_parallel = normalize_bool(deep_get(env, "model_parallel", False)) if isinstance(env, Mapping) else False
    device_map = deep_get(env, "device_map") if isinstance(env, Mapping) else None

    if model_parallel:
        placement = "model.parallelize(device_map) if provided, otherwise model.parallelize()"
    elif num_gpus > 1:
        placement = f"model.to('cuda:{local_rank}') then torch.nn.DataParallel(output_device='cuda:{local_rank}')"
    elif num_gpus > 0:
        placement = "model.cuda()"
    else:
        placement = "CPU; model is not moved to CUDA"

    torch_probe: Dict[str, Any] = {"enabled": False}
    warnings: List[str] = []
    if probe_torch:
        torch_probe["enabled"] = True
        try:
            import torch  # type: ignore

            torch_probe.update(
                {
                    "torch_version": getattr(torch, "__version__", "unknown"),
                    "cuda_available": bool(torch.cuda.is_available()),
                    "cuda_device_count": int(torch.cuda.device_count()),
                }
            )
            if num_gpus > 0 and not torch.cuda.is_available():
                warnings.append("Config requests CUDA but torch.cuda.is_available() is false.")
            if num_gpus > torch.cuda.device_count() and torch.cuda.is_available():
                warnings.append("Config requests more GPUs than torch reports as available.")
        except Exception as exc:
            torch_probe.update({"error": str(exc)})
            warnings.append("Torch probe failed; cannot verify CUDA availability.")

    if isinstance(cuda_visible_devices, list) and cuda_visible_devices and local_rank >= len(cuda_visible_devices):
        warnings.append("environment.local_rank is outside cuda_visible_devices list length.")
    if num_gpus > 0 and cuda_visible_devices in ([], ""):
        warnings.append("num_gpus > 0 but cuda_visible_devices is empty; model.cuda() may use the shell default device set.")
    if model_parallel and num_gpus > 1:
        warnings.append("model_parallel is checked before DataParallel; OpenPrompt will not combine both paths.")

    return {
        "environment": {
            "num_gpus": num_gpus,
            "cuda_visible_devices": cuda_visible_devices,
            "local_rank": local_rank,
            "model_parallel": model_parallel,
            "device_map": device_map,
            "shell_CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
        "model_to_device_action": placement,
        "torch_probe": torch_probe,
        "warnings": warnings,
    }


def active_prompt_config(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    template_name = deep_get(cfg, "template")
    verbalizer_name = deep_get(cfg, "verbalizer")
    template_cfg = deep_get(cfg, str(template_name), {}) if template_name else {}
    verbalizer_cfg = deep_get(cfg, str(verbalizer_name), {}) if verbalizer_name else {}
    return {
        "template": template_name,
        "template_config": template_cfg if isinstance(template_cfg, Mapping) else {},
        "verbalizer": verbalizer_name,
        "verbalizer_config": verbalizer_cfg if isinstance(verbalizer_cfg, Mapping) else {},
    }


def path_status(repo_root: Path, label: str, value: Any) -> Optional[Dict[str, Any]]:
    if value in (None, ""):
        return None
    if isinstance(value, (list, tuple)):
        return None
    raw = str(value)
    candidate = Path(raw)
    resolved = candidate if candidate.is_absolute() else repo_root / candidate
    return {
        "label": label,
        "path": raw,
        "exists": resolved.exists(),
        "kind": "dir" if resolved.is_dir() else "file" if resolved.is_file() else "missing",
    }


def collect_paths(cfg: Mapping[str, Any], repo_root: Path) -> List[Dict[str, Any]]:
    prompt = active_prompt_config(cfg)
    items = [
        path_status(repo_root, "dataset.path", deep_get(cfg, "dataset.path")),
        path_status(repo_root, "active_template.file_path", deep_get(prompt["template_config"], "file_path") if isinstance(prompt["template_config"], Mapping) else None),
        path_status(repo_root, "active_verbalizer.file_path", deep_get(prompt["verbalizer_config"], "file_path") if isinstance(prompt["verbalizer_config"], Mapping) else None),
        path_status(repo_root, "template_generator.template.file_path", deep_get(cfg, "template_generator.template.file_path")),
    ]
    return [item for item in items if item is not None]


def summarize_training(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    train = deep_get(cfg, "train", {}) or {}
    dev = deep_get(cfg, "dev", {}) or {}
    test = deep_get(cfg, "test", {}) or {}
    checkpoint = deep_get(cfg, "checkpoint", {}) or {}
    logging = deep_get(cfg, "logging", {}) or {}
    clean = normalize_bool(deep_get(train, "clean", False)) if isinstance(train, Mapping) else False
    return {
        "train": {
            "num_epochs": deep_get(train, "num_epochs"),
            "num_training_steps": deep_get(train, "num_training_steps"),
            "batch_size": deep_get(train, "batch_size"),
            "teacher_forcing": deep_get(train, "teacher_forcing"),
            "gradient_accumulation_steps": deep_get(train, "gradient_accumulation_steps"),
            "max_grad_norm": deep_get(train, "max_grad_norm"),
            "clean": clean,
            "train_verblizer": deep_get(train, "train_verblizer"),
        },
        "dev": {"batch_size": deep_get(dev, "batch_size"), "shuffle_data": deep_get(dev, "shuffle_data")},
        "test": {"batch_size": deep_get(test, "batch_size"), "shuffle_data": deep_get(test, "shuffle_data")},
        "logging": {
            "path": deep_get(logging, "path"),
            "path_base": deep_get(logging, "path_base"),
            "unique_string": deep_get(logging, "unique_string"),
            "note": "experiments/cli.py resolves logging.path for new runs; BaseRunner writes tensorboard/checkpoints below it unless train.clean is true.",
        },
        "checkpoint": {
            "higher_better": deep_get(checkpoint, "higher_better"),
            "save_latest_declared": deep_get(checkpoint, "save_latest"),
            "save_best_declared": deep_get(checkpoint, "save_best"),
            "native_behavior": "BaseRunner writes last.ckpt and best.ckpt when train.clean is false; save_latest/save_best are not enforced.",
        },
    }


def summarize_generation(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    generation = deep_get(cfg, "generation", {}) or {}
    dataloader = deep_get(cfg, "dataloader", {}) or {}
    return {
        "generation": generation if isinstance(generation, Mapping) else {},
        "dataloader": {
            "max_seq_length": deep_get(dataloader, "max_seq_length"),
            "decoder_max_length": deep_get(dataloader, "decoder_max_length"),
            "truncate_method": deep_get(dataloader, "truncate_method"),
        },
        "caveats": [
            "PromptForGeneration training needs tgt_text and loss_ids from the tokenizer wrapper.",
            "Use teacher_forcing=True for generation training dataloaders.",
            "Use predict_eos_token=True when the template/wrapper needs an explicit EOS for generation stopping.",
            "generation.max_length includes prompt/input tokens in native transformers behavior.",
        ],
    }


def collect_warnings(cfg: Mapping[str, Any], runner: Mapping[str, Any], paths: Iterable[Mapping[str, Any]]) -> List[str]:
    warnings: List[str] = []
    if runner["runner"] == "unsupported":
        warnings.append(str(runner["reason"]))
    if runner.get("learning_setting") == "few_shot" and deep_get(cfg, "few_shot.few_shot_sampling") is None:
        warnings.append("learning_setting=few_shot but few_shot.few_shot_sampling is not set.")
    if runner.get("learning_setting") == "zero-shot":
        warnings.append("Use learning_setting=zero_shot; experiments/cli.py does not match zero-shot with a hyphen.")
    if runner["runner"] == "LMBFFClassificationRunner":
        if runner.get("auto_t") and deep_get(cfg, "verbalizer") is None:
            warnings.append("LM-BFF auto_t requires an input verbalizer.")
        if runner.get("auto_v") and deep_get(cfg, "template") is None:
            warnings.append("LM-BFF auto_v requires an input template.")
    if runner["runner"] == "ProtoVerbClassificationRunner" and deep_get(cfg, "train.train_verblizer") is None:
        warnings.append("ProtoVerb selected; train.train_verblizer is unset, so native non-post pretraining behavior applies.")
    missing = [p for p in paths if not p.get("exists")]
    for item in missing:
        warnings.append(f"Referenced path missing: {item.get('label')} -> {item.get('path')}")
    return warnings


def print_markdown(report: Mapping[str, Any]) -> None:
    print("# OpenPrompt Training Config Dry-Run")
    print()
    print(f"Config: `{report['config_path']}`")
    print(f"Load method: {report['load_method']}")
    print("Training started: **no**")
    print()

    runner = report["runner_selection"]
    print("## Runner selection")
    print(f"- Task: `{runner['task']}`")
    print(f"- Runner: `{runner['runner']}`")
    print(f"- Reason: {runner['reason']}")
    print(f"- Learning setting: `{runner['learning_setting']}` — {runner['learning_flow']}")
    print(f"- Template: `{runner['template']}`")
    print(f"- Verbalizer: `{runner['verbalizer']}`")
    print()

    backend = report["backend"]
    print("## Backend expectation")
    for key, value in backend["environment"].items():
        print(f"- {key}: `{value}`")
    print(f"- model_to_device action: {backend['model_to_device_action']}")
    if backend["torch_probe"].get("enabled"):
        print(f"- torch probe: `{backend['torch_probe']}`")
    print()

    training = report["training"]
    print("## Training/checkpoint/logging")
    for key, value in training["train"].items():
        print(f"- train.{key}: `{value}`")
    print(f"- logging.path: `{training['logging']['path']}`")
    print(f"- logging.path_base: `{training['logging']['path_base']}`")
    print(f"- checkpoint behavior: {training['checkpoint']['native_behavior']}")
    print()

    print("## Paths")
    if report["paths"]:
        for item in report["paths"]:
            status = "ok" if item["exists"] else "missing"
            print(f"- {item['label']}: `{item['path']}` ({status}, {item['kind']})")
    else:
        print("- No dataset/template/verbalizer file paths found in active config nodes.")
    print()

    if runner["task"] == "generation":
        print("## Generation caveats")
        for caveat in report["generation"]["caveats"]:
            print(f"- {caveat}")
        print()

    print("## Warnings")
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- None from static dry-run checks.")


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config_yaml)
    if not config_path.is_absolute():
        candidate = (Path.cwd() / config_path).resolve()
        config_path = candidate if candidate.exists() else (repo_root / config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config YAML not found: {config_path}")

    cfg, load_method, load_warnings = load_config(config_path, repo_root, not args.no_openprompt_merge)
    runner = detect_runner(cfg)
    backend = summarize_backend(cfg, args.probe_torch)
    paths = collect_paths(cfg, repo_root)
    warnings = []
    warnings.extend(load_warnings)
    warnings.extend(backend.get("warnings", []))
    warnings.extend(collect_warnings(cfg, runner, paths))

    return {
        "schemaVersion": 1,
        "training_started": False,
        "repo_root": str(repo_root),
        "config_path": str(config_path),
        "load_method": load_method,
        "runner_selection": runner,
        "plm": deep_get(cfg, "plm", {}) or {},
        "active_prompt": active_prompt_config(cfg),
        "training": summarize_training(cfg),
        "backend": backend,
        "generation": summarize_generation(cfg),
        "paths": paths,
        "warnings": warnings,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-yaml", required=True, help="OpenPrompt experiment YAML to inspect.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for relative path checks (default: cwd).")
    parser.add_argument("--no-openprompt-merge", action="store_true", help="Parse raw YAML only; do not import openprompt.config/get_user_config.")
    parser.add_argument("--probe-torch", action="store_true", help="Import torch and report CUDA availability; still does not load models or datasets.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit 2 if static warnings are present.")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_markdown(report)
    return 2 if args.fail_on_warning and report["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
