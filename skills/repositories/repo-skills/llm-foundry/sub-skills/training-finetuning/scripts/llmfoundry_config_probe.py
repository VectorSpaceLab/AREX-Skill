#!/usr/bin/env python3
"""Static LLM Foundry training YAML probe.

This script parses a training YAML and optional OmegaConf-style override strings
without launching training. It does not import llmfoundry, initialize
distributed state, download tokenizers/models/data, or write checkpoints.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

REQUIRED_TRAIN_CONFIG_KEYS = [
    "model",
    "tokenizer",
    "optimizer",
    "scheduler",
    "train_loader",
    "device_train_batch_size",
    "device_eval_batch_size",
    "max_duration",
    "max_seq_len",
]

KNOWN_OPTIONAL_KEYS = {
    "seed",
    "precision",
    "code_paths",
    "max_split_size_mb",
    "expandable_segments",
    "cuda_load_lazy",
    "dist_timeout",
    "fsdp_config",
    "tp_config",
    "accumulate_train_batch_on_tokens",
    "eval_interval",
    "eval_loader",
    "eval_loaders",
    "icl_tasks",
    "icl_tasks_str",
    "eval_gauntlet",
    "eval_gauntlet_str",
    "icl_subset_num_batches",
    "icl_seq_len",
    "loggers",
    "progress_bar",
    "log_to_console",
    "python_log_level",
    "console_log_interval",
    "log_config",
    "callbacks",
    "algorithms",
    "save_folder",
    "save_latest_filename",
    "save_overwrite",
    "save_weights_only",
    "save_filename",
    "save_interval",
    "save_num_checkpoints_to_keep",
    "load_path",
    "load_weights_only",
    "load_strict_model_weights",
    "load_ignore_keys",
    "save_ignore_keys",
    "only_hf_checkpoint",
    "only_composer_checkpoint",
    "train_subset_num_batches",
    "device_train_microbatch_size",
    "global_train_batch_size",
    "spin_dataloaders",
    "eval_subset_num_batches",
    "eval_first",
    "compile_config",
    "metadata",
    "flatten_metadata",
    "run_name",
    "autoresume",
    "profiler",
    "variables",
    "n_gpus",
    "device_train_grad_accum",
}
KNOWN_TOP_LEVEL_KEYS = set(REQUIRED_TRAIN_CONFIG_KEYS) | KNOWN_OPTIONAL_KEYS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw = list(sys.argv[1:] if argv is None else argv)
    # argparse.REMAINDER intentionally captures OmegaConf override strings after
    # the YAML path. Pull this helper's own flags out first so both
    # `probe.py --json config.yaml` and `probe.py config.yaml --json` work.
    forced_json = False
    forced_strict = False
    normalized: list[str] = []
    for item in raw:
        if item == "--json":
            forced_json = True
        elif item == "--strict":
            forced_strict = True
        else:
            normalized.append(item)

    parser = argparse.ArgumentParser(
        description=(
            "Statically inspect an LLM Foundry training YAML and optional "
            "OmegaConf dotlist overrides without launching training."
        ),
    )
    parser.add_argument("yaml_path", help="Path to a training YAML file.")
    parser.add_argument(
        "overrides",
        nargs=argparse.REMAINDER,
        help="Optional override strings, e.g. max_duration=2ba variables.data_local=<data-local>.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text. May appear before or after the YAML path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if errors are detected. May appear before or after the YAML path; warnings alone do not fail.",
    )
    ns = parser.parse_args(normalized)
    ns.json = bool(ns.json or forced_json)
    ns.strict = bool(ns.strict or forced_strict)
    return ns


def load_with_omegaconf(path: Path, overrides: list[str]) -> tuple[dict[str, Any] | None, list[str]]:
    notes: list[str] = []
    try:
        from omegaconf import OmegaConf as om  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        notes.append(f"OmegaConf unavailable ({type(exc).__name__}: {exc}); trying PyYAML.")
        return None, notes

    try:
        cfg = om.load(path)
        if overrides:
            try:
                cli_cfg = om.from_cli(overrides)
                cfg = om.merge(cfg, cli_cfg)
                notes.append("Merged overrides with OmegaConf.from_cli.")
            except Exception as exc:
                notes.append(f"Could not merge overrides with OmegaConf ({type(exc).__name__}: {exc}); inspected YAML only.")
        data = om.to_container(cfg, resolve=False)
        if not isinstance(data, dict):
            raise TypeError(f"top-level YAML must be a mapping, got {type(data).__name__}")
        return data, notes
    except Exception as exc:
        notes.append(f"OmegaConf load failed ({type(exc).__name__}: {exc}); trying PyYAML.")
        return None, notes


def load_with_pyyaml(path: Path) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            f"Neither OmegaConf nor PyYAML is available; install one to parse YAML. Last error: {exc}",
        ) from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError(f"top-level YAML must be a mapping, got {type(data).__name__}")
    notes.append("Loaded YAML with PyYAML; overrides were listed but not merged.")
    return data, notes


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def get_path(data: Any, dotted: str, default: Any = None) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def is_blank(value: Any) -> bool:
    return value is None or value == "" or value == "null"


def stringify(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def maybe_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return stripped.startswith("<") and stripped.endswith(">")


def collect_override_keys(overrides: Iterable[str]) -> list[str]:
    keys: list[str] = []
    for item in overrides:
        if not item or item == "--":
            continue
        if "=" in item:
            keys.append(item.split("=", 1)[0])
        else:
            keys.append(item)
    return keys


def contains_flash(model: dict[str, Any]) -> bool:
    values = [
        get_path(model, "attn_config.attn_impl"),
        get_path(model, "config_overrides.attn_config.attn_impl"),
        model.get("attn_implementation"),
    ]
    return any("flash" in str(v).lower() for v in values if v is not None) or bool(model.get("use_flash_attention_2"))


def contains_te_or_fp8(cfg: dict[str, Any], model: dict[str, Any]) -> bool:
    precision = str(cfg.get("precision", ""))
    ffn_type = str(get_path(model, "ffn_config.ffn_type", ""))
    return "fp8" in precision or model.get("fc_type") == "te" or "te" in ffn_type


def contains_moe(model: dict[str, Any]) -> bool:
    ffn_type = str(get_path(model, "ffn_config.ffn_type", ""))
    return "moe" in ffn_type.lower() or "megablocks" in ffn_type.lower() or "mb_" in ffn_type.lower()


def inspect_loader(prefix: str, loader: Any, warnings: list[str], info: list[str]) -> None:
    if loader is None:
        return
    if isinstance(loader, list):
        for idx, item in enumerate(loader):
            if not isinstance(item, dict):
                warnings.append(f"{prefix}[{idx}] is not a mapping.")
                continue
            if "label" not in item:
                warnings.append(f"{prefix}[{idx}] is missing label; multiple eval loaders require labels.")
            inspect_loader(f"{prefix}[{idx}]", item, warnings, info)
        return
    if not isinstance(loader, dict):
        warnings.append(f"{prefix} is not a mapping.")
        return

    name = loader.get("name")
    dataset = as_dict(loader.get("dataset"))
    if not name:
        warnings.append(f"{prefix}.name is missing.")
        return
    info.append(f"{prefix}.name={name}")
    if not dataset:
        warnings.append(f"{prefix}.dataset is missing or empty.")
        return

    if name == "text":
        local = dataset.get("local")
        remote = dataset.get("remote")
        split = dataset.get("split")
        streams = dataset.get("streams")
        if streams:
            info.append(f"{prefix}.dataset uses streams.")
        else:
            if is_blank(local) and is_blank(remote):
                warnings.append(f"{prefix}.dataset needs local and/or remote MDS path for text loader.")
            if is_blank(split):
                warnings.append(f"{prefix}.dataset.split is missing for text loader.")
        if "max_seq_len" not in dataset:
            warnings.append(f"{prefix}.dataset.max_seq_len is missing for text loader.")
    elif name == "finetuning":
        has_hf = "hf_name" in dataset
        has_streams = "streams" in dataset
        has_local_remote = "local" in dataset or "remote" in dataset
        if not (has_hf or has_streams or has_local_remote):
            warnings.append(f"{prefix}.dataset should define hf_name, streams, local, or remote for finetuning.")
        if dataset.get("hf_name") == "json" and not get_path(dataset, "hf_kwargs.data_dir") and not get_path(dataset, "hf_kwargs.data_files"):
            warnings.append(f"{prefix}.dataset.hf_name=json usually needs hf_kwargs.data_dir or hf_kwargs.data_files.")
        if "split" not in dataset and not has_streams:
            warnings.append(f"{prefix}.dataset.split is missing for finetuning loader.")
        if "max_seq_len" not in dataset:
            warnings.append(f"{prefix}.dataset.max_seq_len is missing for finetuning loader.")
        if not dataset.get("decoder_only_format") and name == "finetuning":
            warnings.append(f"{prefix}.dataset.decoder_only_format is not set; confirm encoder/decoder policy.")
    else:
        warnings.append(f"{prefix}.name={name!r} is not one of common training loaders: text, finetuning.")


def analyze(cfg: dict[str, Any], overrides: list[str], path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    missing_actual = [key for key in REQUIRED_TRAIN_CONFIG_KEYS if key not in cfg]
    batch_source = "device_train_batch_size" if "device_train_batch_size" in cfg else "global_train_batch_size" if "global_train_batch_size" in cfg else None
    if "device_train_batch_size" in missing_actual and batch_source == "global_train_batch_size":
        info.append("device_train_batch_size is not in YAML; global_train_batch_size is present and LLM Foundry normally derives it during config transforms.")
        missing_effective = [key for key in missing_actual if key != "device_train_batch_size"]
    else:
        missing_effective = missing_actual
    if missing_effective:
        errors.append("Missing required/effective TrainConfig keys: " + ", ".join(missing_effective))
    if batch_source is None:
        errors.append("Missing batch-size source: provide global_train_batch_size or device_train_batch_size.")

    unknown = sorted(k for k in cfg.keys() if k not in KNOWN_TOP_LEVEL_KEYS)
    if unknown:
        warnings.append(
            "Unknown top-level keys may be rejected unless a config transform consumes them; prefer variables.* for custom constants: "
            + ", ".join(unknown),
        )

    model = as_dict(cfg.get("model"))
    tokenizer = as_dict(cfg.get("tokenizer"))
    optimizer = as_dict(cfg.get("optimizer"))
    scheduler = as_dict(cfg.get("scheduler"))

    for section, mapping in [
        ("model", model),
        ("tokenizer", tokenizer),
        ("optimizer", optimizer),
        ("scheduler", scheduler),
    ]:
        if mapping and not mapping.get("name"):
            errors.append(f"{section}.name is missing.")

    inspect_loader("train_loader", cfg.get("train_loader"), warnings, info)
    if "eval_loader" in cfg:
        inspect_loader("eval_loader", cfg.get("eval_loader"), warnings, info)
    if "eval_loaders" in cfg:
        inspect_loader("eval_loaders", cfg.get("eval_loaders"), warnings, info)

    max_seq_len = cfg.get("max_seq_len")
    tokenizer_len = get_path(tokenizer, "kwargs.model_max_length")
    train_len = get_path(cfg, "train_loader.dataset.max_seq_len")
    model_len = model.get("max_seq_len", get_path(model, "config_overrides.max_seq_len"))
    seq_values = {
        "max_seq_len": max_seq_len,
        "tokenizer.kwargs.model_max_length": tokenizer_len,
        "train_loader.dataset.max_seq_len": train_len,
        "model max/config override": model_len,
    }
    concrete_seq = {k: v for k, v in seq_values.items() if v is not None}
    if len({stringify(v) for v in concrete_seq.values()}) > 1:
        warnings.append("Sequence length fields differ or use different interpolation strings: " + json.dumps(concrete_seq, sort_keys=True))

    if model.get("name") == "hf_t5" and ("icl_tasks" in cfg or "icl_tasks_str" in cfg):
        errors.append("ICL evaluation is not supported for hf_t5 training configs.")

    if model.get("load_in_8bit"):
        errors.append("model.load_in_8bit is rejected for training; use it only for evaluation/inference workflows.")

    if contains_flash(model):
        warnings.append("Flash attention is requested; verify CUDA/PyTorch/flash-attn support or use torch attention for CPU smoke runs.")
    if contains_te_or_fp8(cfg, model):
        warnings.append("TransformerEngine/fp8 settings detected; verify TE installation and compatible GPU hardware.")
    if contains_moe(model):
        warnings.append("MoE/MegaBlocks-like FFN settings detected; verify optional dependencies and FSDP use_orig_params constraints.")

    init_device = model.get("init_device")
    fsdp = cfg.get("fsdp_config")
    tp = as_dict(cfg.get("tp_config"))
    if init_device == "meta" and not fsdp:
        warnings.append("model.init_device=meta without fsdp_config will be reverted to cpu by LLM Foundry.")
    if init_device == "mixed" and not fsdp:
        errors.append("model.init_device=mixed requires fsdp_config.")
    if tp and ("strategy" not in tp or "tensor_parallel_degree" not in tp):
        errors.append("tp_config requires both strategy and tensor_parallel_degree.")
    if tp and contains_moe(model):
        errors.append("Tensor parallelism is not supported for MoE models in the inspected training logic.")

    gbs = cfg.get("global_train_batch_size")
    micro = cfg.get("device_train_microbatch_size")
    if gbs is not None:
        info.append(f"global_train_batch_size={gbs}; verify divisibility by world size at launch time.")
    if isinstance(gbs, (int, float)) and isinstance(micro, (int, float)) and micro > gbs:
        warnings.append("device_train_microbatch_size exceeds global_train_batch_size; it will not be useful and may be reduced.")
    if micro == "auto":
        warnings.append("device_train_microbatch_size=auto can help fit memory but should follow a fixed-microbatch smoke test.")

    run_name = cfg.get("run_name") or os.environ.get("RUN_NAME") or os.environ.get("COMPOSER_RUN_NAME")
    save_folder = cfg.get("save_folder")
    if save_folder is not None:
        if is_blank(save_folder):
            info.append("save_folder is blank/null; no ordinary checkpoint destination configured.")
        elif maybe_placeholder(save_folder):
            warnings.append("save_folder is still a placeholder.")
        elif str(save_folder).startswith(("s3://", "gs://", "oci://", "hf://")):
            warnings.append("Remote save_folder detected; verify credentials and write permissions on every worker.")
    if run_name and save_folder and not cfg.get("save_overwrite", False) and not cfg.get("save_weights_only", False) and not cfg.get("autoresume", False):
        warnings.append("run_name and save_folder are set; LLM Foundry may default autoresume behavior to true.")

    load_path = cfg.get("load_path")
    if load_path:
        if maybe_placeholder(load_path):
            warnings.append("load_path is still a placeholder.")
        if str(load_path).startswith(("s3://", "gs://", "oci://", "hf://")):
            warnings.append("Remote load_path detected; verify credentials and read permissions on every worker.")
        if not cfg.get("load_weights_only", False):
            warnings.append("load_path is set with load_weights_only=false/default; this resumes full state rather than just fine-tuning weights.")

    if cfg.get("only_hf_checkpoint"):
        callbacks = as_dict(cfg.get("callbacks"))
        hf_count = sum(1 for name in callbacks if name == "hf_checkpointer")
        if hf_count != 1:
            errors.append("only_hf_checkpoint=true requires exactly one callbacks.hf_checkpointer entry.")

    tokenizer_name = tokenizer.get("name")
    model_name_or_path = model.get("pretrained_model_name_or_path")
    if any("meta-llama" in str(v).lower() for v in [tokenizer_name, model_name_or_path]) or model.get("use_auth_token"):
        warnings.append("Gated or authenticated model/tokenizer likely; verify HF_TOKEN or equivalent access before launch.")

    if cfg.get("max_duration") in (None, ""):
        errors.append("max_duration is blank; set an explicit bounded duration.")
    elif str(cfg.get("max_duration")).lower() in {"1ep", "2ep"}:
        warnings.append("Epoch-based duration can be large depending on dataset size; use ba-based limits for smoke tests.")

    override_keys = collect_override_keys(overrides)
    if overrides:
        info.append("Override strings received: " + ", ".join(overrides))
        info.append("Override keys: " + ", ".join(override_keys))

    return {
        "path": str(path),
        "required_train_config_keys": REQUIRED_TRAIN_CONFIG_KEYS,
        "missing_actual_required_keys": missing_actual,
        "missing_effective_required_keys": missing_effective,
        "batch_size_source": batch_source,
        "top_level_keys": sorted(str(k) for k in cfg.keys()),
        "override_strings": overrides,
        "override_keys": override_keys,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }


def print_text(report: dict[str, Any], load_notes: list[str]) -> None:
    print("LLM Foundry training config probe")
    print(f"YAML: {report['path']}")
    if load_notes:
        print("\nLoad notes:")
        for note in load_notes:
            print(f"  - {note}")
    print("\nRequired TrainConfig keys:")
    for key in report["required_train_config_keys"]:
        print(f"  - {key}")
    print(f"\nTop-level keys ({len(report['top_level_keys'])}): {', '.join(report['top_level_keys'])}")
    print(f"Batch-size source: {report['batch_size_source'] or 'MISSING'}")
    if report["override_strings"]:
        print("\nOverride strings:")
        for item in report["override_strings"]:
            print(f"  - {item}")
    for label in ["errors", "warnings", "info"]:
        items = report[label]
        print(f"\n{label.upper()} ({len(items)}):")
        if items:
            for item in items:
                print(f"  - {item}")
        else:
            print("  - none")


def main() -> int:
    ns = parse_args()
    yaml_path = Path(ns.yaml_path).expanduser()
    if not yaml_path.exists():
        print(f"ERROR: YAML path does not exist: {yaml_path}", file=sys.stderr)
        return 2
    if not yaml_path.is_file():
        print(f"ERROR: YAML path is not a file: {yaml_path}", file=sys.stderr)
        return 2

    load_notes: list[str] = []
    cfg, notes = load_with_omegaconf(yaml_path, ns.overrides)
    load_notes.extend(notes)
    if cfg is None:
        try:
            cfg, notes = load_with_pyyaml(yaml_path)
            load_notes.extend(notes)
        except Exception as exc:
            print(f"ERROR: could not parse YAML: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2

    report = analyze(cfg, ns.overrides, yaml_path)
    if ns.json:
        print(json.dumps({"load_notes": load_notes, **report}, indent=2, sort_keys=True))
    else:
        print_text(report, load_notes)

    if report["errors"] and ns.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
