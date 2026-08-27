#!/usr/bin/env python3
"""Safely inspect generative-models training configs without starting training.

The tool intentionally avoids importing sgm, PyTorch Lightning, model classes, data
modules, or checkpoint libraries. It only parses and merges YAML/OmegaConf-style
configuration, then reports structure, targets, placeholders, and launcher command
hints.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

PLACEHOLDER_RE = re.compile(
    r"^(CKPT_PATH|DATA_PATH|USER|TODO|TBD|NONE|NULL|<[^>]+>|/path/to/.*|path/to/.*)$",
    re.IGNORECASE,
)
SUSPICIOUS_KEY_RE = re.compile(r"(path|paths|url|urls|dir|root|ckpt|checkpoint|data)", re.IGNORECASE)
INSTANTIABLE_KEYS = {
    "model",
    "data",
    "logger",
    "strategy",
    "modelcheckpoint",
    "setup_callback",
    "image_logger",
    "learning_rate_logger",
    "metrics_over_trainsteps_checkpoint",
    "network_config",
    "denoiser_config",
    "first_stage_config",
    "conditioner_config",
    "sampler_config",
    "optimizer_config",
    "scheduler_config",
    "loss_fn_config",
    "loss_weighting_config",
    "sigma_sampler_config",
    "scaling_config",
    "discretization_config",
    "guider_config",
    "encoder_config",
    "decoder_config",
    "loss_config",
    "regularizer_config",
    "ckpt_engine",
}
OPTIONAL_INSTANTIABLE_KEYS = {"lightning", "trainer", "callbacks", "params"}


class ConfigLoadError(RuntimeError):
    pass


def import_parsers():
    try:
        from omegaconf import OmegaConf  # type: ignore
    except Exception:  # pragma: no cover - depends on host environment
        OmegaConf = None
    try:
        import yaml  # type: ignore
    except Exception:  # pragma: no cover - depends on host environment
        yaml = None
    return OmegaConf, yaml


def to_plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    return value


def load_yaml(path: Path, omega_conf: Any, yaml_module: Any) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigLoadError(f"Config does not exist: {path}")
    if not path.is_file():
        raise ConfigLoadError(f"Config is not a file: {path}")
    try:
        if omega_conf is not None:
            cfg = omega_conf.load(str(path))
            return to_plain(omega_conf.to_container(cfg, resolve=False)) or {}
        if yaml_module is not None:
            with path.open("r", encoding="utf-8") as handle:
                return to_plain(yaml_module.safe_load(handle)) or {}
    except Exception as exc:
        raise ConfigLoadError(f"Failed to parse {path}: {exc}") from exc
    raise ConfigLoadError("Install omegaconf or PyYAML to parse training configs")


def parse_scalar(raw: str) -> Any:
    text = raw.strip()
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "none"}:
        return None
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        try:
            import ast

            return ast.literal_eval(text)
        except Exception:
            return text
    try:
        if re.fullmatch(r"[-+]?\d+", text):
            return int(text)
        if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", text) or re.fullmatch(
            r"[-+]?\d+[eE][-+]?\d+", text
        ):
            return float(text)
    except Exception:
        return text
    return text


def dotlist_to_nested(dotlist: Sequence[str], omega_conf: Any) -> Dict[str, Any]:
    if not dotlist:
        return {}
    if omega_conf is not None:
        try:
            cfg = omega_conf.from_dotlist(list(dotlist))
            return to_plain(omega_conf.to_container(cfg, resolve=False)) or {}
        except Exception as exc:
            raise ConfigLoadError(f"Failed to parse dotlist overrides: {exc}") from exc

    root: Dict[str, Any] = {}
    for item in dotlist:
        if "=" not in item:
            raise ConfigLoadError(f"Dotlist override must use key=value syntax: {item}")
        key, raw_value = item.split("=", 1)
        if not key:
            raise ConfigLoadError(f"Dotlist override has an empty key: {item}")
        cursor: MutableMapping[str, Any] = root
        parts = key.split(".")
        for part in parts[:-1]:
            if not part:
                raise ConfigLoadError(f"Dotlist override has an empty path segment: {item}")
            next_value = cursor.get(part)
            if not isinstance(next_value, MutableMapping):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value
        cursor[parts[-1]] = parse_scalar(raw_value)
    return root


def merge_values(base: Any, override: Any) -> Any:
    if isinstance(base, Mapping) and isinstance(override, Mapping):
        result = deepcopy(dict(base))
        for key, value in override.items():
            result[key] = merge_values(result.get(key), value)
        return result
    return deepcopy(override)


def merge_all(configs: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for cfg in configs:
        merged = merge_values(merged, cfg)
    return merged


def path_join(parts: Sequence[Any]) -> str:
    if not parts:
        return "<root>"
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out = f"{out}.{part}" if out else str(part)
    return out


def walk(value: Any, path: Tuple[Any, ...] = ()) -> Iterable[Tuple[Tuple[Any, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (index,))


def find_targets(config: Mapping[str, Any]) -> List[Dict[str, str]]:
    targets = []
    for path, value in walk(config):
        if isinstance(value, Mapping) and "target" in value:
            targets.append({"path": path_join(path), "target": str(value.get("target"))})
    return targets


def find_missing_targets(config: Mapping[str, Any]) -> List[Dict[str, str]]:
    missing = []
    for path, value in walk(config):
        if not isinstance(value, Mapping) or "target" in value:
            continue
        if not path:
            continue
        key = str(path[-1])
        parent_key = str(path[-2]) if len(path) > 1 else ""
        if key in OPTIONAL_INSTANTIABLE_KEYS:
            continue
        if parent_key == "lightning" and key in {"modelcheckpoint", "logger", "strategy"}:
            continue
        if parent_key == "datapipeline" and key == "pipeline_config":
            continue
        if parent_key == "callbacks" and key in {
            "image_logger",
            "learning_rate_logger",
            "metrics_over_trainsteps_checkpoint",
            "checkpoint_callback",
            "setup_callback",
        }:
            continue
        has_config_suffix = key.endswith("_config") or key.endswith("_callback")
        has_params = "params" in value
        likely = (
            key in INSTANTIABLE_KEYS
            or has_config_suffix
            or (parent_key in {"callbacks", "logger", "modelcheckpoint", "strategy"} and has_params)
        )
        if likely:
            missing.append(
                {
                    "path": path_join(path),
                    "reason": "Looks like an instantiable config mapping but has no target key.",
                }
            )
    return missing


def find_placeholders(config: Mapping[str, Any]) -> List[Dict[str, str]]:
    placeholders = []
    for path, value in walk(config):
        if isinstance(value, str):
            key = str(path[-1]) if path else ""
            stripped = value.strip()
            if PLACEHOLDER_RE.match(stripped) or (SUSPICIOUS_KEY_RE.search(key) and stripped in {"", "..."}):
                placeholders.append({"path": path_join(path), "value": value})
    return placeholders


def scan_source_placeholders(paths: Sequence[Path]) -> List[Dict[str, str]]:
    placeholders = []
    seen = set()
    token_re = re.compile(r"\b(USER|CKPT_PATH|DATA_PATH|TODO|TBD)\b")
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            if not token_re.search(line):
                continue
            key = (str(path), number, line.strip())
            if key in seen:
                continue
            seen.add(key)
            placeholders.append(
                {
                    "path": f"{path.name}:{number}",
                    "value": line.strip(),
                    "source": str(path),
                }
            )
    return placeholders


def summarize_sections(config: Mapping[str, Any]) -> Dict[str, Any]:
    top_level = sorted(str(key) for key in config.keys())
    missing_top_level = [key for key in ["model", "data"] if key not in config]
    optional_missing = [key for key in ["lightning"] if key not in config]
    return {
        "top_level": top_level,
        "missing_required": missing_top_level,
        "missing_optional": optional_missing,
        "has_model": "model" in config,
        "has_data": "data" in config,
        "has_lightning": "lightning" in config,
    }


def get_nested(config: Mapping[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    cursor: Any = config
    for key in keys:
        if not isinstance(cursor, Mapping) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor


def summarize_data(config: Mapping[str, Any]) -> Dict[str, Any]:
    data = get_nested(config, ["data"], {})
    if not isinstance(data, Mapping):
        return {"target": None, "notes": ["data section is not a mapping"]}
    params = data.get("params", {}) if isinstance(data.get("params", {}), Mapping) else {}
    notes: List[str] = []
    target = data.get("target")
    if target == "sgm.data.dataset.StableDataModuleFromConfig":
        train = params.get("train") if isinstance(params, Mapping) else None
        if not isinstance(train, Mapping):
            notes.append("StableDataModuleFromConfig requires params.train")
        else:
            if "datapipeline" not in train:
                notes.append("params.train.datapipeline is missing")
            if "loader" not in train:
                notes.append("params.train.loader is missing")
        for split in ["validation", "test"]:
            split_cfg = params.get(split) if isinstance(params, Mapping) else None
            if split_cfg is not None and isinstance(split_cfg, Mapping):
                if "datapipeline" not in split_cfg or "loader" not in split_cfg:
                    notes.append(f"params.{split} should contain datapipeline and loader")
        if not params.get("validation") and not params.get("skip_val_loader", False):
            notes.append("No validation config supplied; launcher data module will reuse train config for validation")
    elif target in {"sgm.data.mnist.MNISTLoader", "sgm.data.cifar10.CIFAR10Loader"}:
        notes.append("Toy data loader may download dataset if instantiated; static inspection avoids that")
    elif target is None:
        notes.append("data.target is missing")
    return {
        "target": target,
        "batch_size": get_nested(data, ["params", "batch_size"])
        or get_nested(data, ["params", "train", "loader", "batch_size"]),
        "num_workers": get_nested(data, ["params", "num_workers"])
        or get_nested(data, ["params", "train", "loader", "num_workers"]),
        "notes": notes,
    }


def summarize_lightning(config: Mapping[str, Any]) -> Dict[str, Any]:
    trainer = get_nested(config, ["lightning", "trainer"], {})
    callbacks = get_nested(config, ["lightning", "callbacks"], {})
    modelcheckpoint = get_nested(config, ["lightning", "modelcheckpoint"], {})
    if not isinstance(trainer, Mapping):
        trainer = {}
    return {
        "trainer": {
            "accelerator": trainer.get("accelerator", "gpu (launcher default)"),
            "devices": trainer.get("devices", "not set"),
            "max_epochs": trainer.get("max_epochs", "not set"),
            "accumulate_grad_batches": trainer.get("accumulate_grad_batches", 1),
            "num_sanity_val_steps": trainer.get("num_sanity_val_steps", "not set"),
        },
        "callbacks": sorted(callbacks.keys()) if isinstance(callbacks, Mapping) else [],
        "has_modelcheckpoint": isinstance(modelcheckpoint, Mapping) and bool(modelcheckpoint),
    }


def summarize_conditioning(config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    emb_models = get_nested(config, ["model", "params", "conditioner_config", "params", "emb_models"], [])
    result = []
    if isinstance(emb_models, list):
        for index, embedder in enumerate(emb_models):
            if isinstance(embedder, Mapping):
                result.append(
                    {
                        "index": index,
                        "target": embedder.get("target"),
                        "input_key": embedder.get("input_key"),
                        "input_keys": embedder.get("input_keys"),
                        "is_trainable": embedder.get("is_trainable", False),
                        "ucg_rate": embedder.get("ucg_rate", 0.0),
                    }
                )
    return result


def command_template(config_paths: Sequence[Path], dotlist: Sequence[str], args: argparse.Namespace) -> str:
    pieces = ["python", "main.py"]
    if config_paths:
        pieces.append("--base")
        pieces.extend(str(path) for path in config_paths)
    if args.name:
        pieces.extend(["-n", args.name])
    if args.resume:
        pieces.extend(["--resume", args.resume])
    pieces.extend(dotlist)
    return " ".join(shlex.quote(piece) for piece in pieces)


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    omega_conf, yaml_module = import_parsers()
    config_paths = [Path(path) for path in args.config]
    configs = [load_yaml(path, omega_conf, yaml_module) for path in config_paths]
    dotlist_config = dotlist_to_nested(args.dotlist, omega_conf)
    merged = merge_all([*configs, dotlist_config])

    warnings: List[str] = []
    if args.name and args.resume:
        warnings.append("main.py rejects using -n/--name together with -r/--resume")
    if args.resume and not Path(args.resume).exists():
        warnings.append(f"Resume path does not exist: {args.resume}")
    if not config_paths and not args.resume:
        warnings.append("No config files supplied; main.py would have no model/data config unless resume adds stored configs")
    if "lightning" not in merged:
        warnings.append("No lightning section; launcher will synthesize trainer/logger/callback defaults")
    if get_nested(merged, ["model", "params", "first_stage_config", "params", "ckpt_path"]) in {"CKPT_PATH", ""}:
        warnings.append("First-stage checkpoint path is still a placeholder")

    section_summary = summarize_sections(merged)
    for key in section_summary["missing_required"]:
        warnings.append(f"Missing required top-level section: {key}")

    return {
        "parser": "OmegaConf" if omega_conf is not None else "PyYAML",
        "configs": [str(path) for path in config_paths],
        "dotlist": list(args.dotlist),
        "sections": section_summary,
        "model_target": get_nested(merged, ["model", "target"]),
        "data": summarize_data(merged),
        "lightning": summarize_lightning(merged),
        "conditioning": summarize_conditioning(merged),
        "targets": find_targets(merged),
        "missing_targets": find_missing_targets(merged),
        "placeholders": find_placeholders(merged),
        "source_placeholders": scan_source_placeholders(config_paths),
        "warnings": warnings,
        "command_template": command_template(config_paths, args.dotlist, args),
    }


def print_text(report: Mapping[str, Any]) -> None:
    print("Training config inspection")
    print("==========================")
    print(f"Parser: {report['parser']}")
    print(f"Configs: {', '.join(report['configs']) if report['configs'] else '(none)'}")
    if report["dotlist"]:
        print(f"Dotlist overrides: {' '.join(report['dotlist'])}")
    print()

    sections = report["sections"]
    print("Top-level sections:", ", ".join(sections["top_level"]) if sections["top_level"] else "(none)")
    if sections["missing_required"]:
        print("Missing required sections:", ", ".join(sections["missing_required"]))
    if sections["missing_optional"]:
        print("Optional sections absent:", ", ".join(sections["missing_optional"]))
    print(f"Model target: {report['model_target'] or '(missing)'}")
    data = report["data"]
    print(f"Data target: {data.get('target') or '(missing)'}")
    if data.get("batch_size") is not None:
        print(f"Data batch size: {data.get('batch_size')}")
    if data.get("num_workers") is not None:
        print(f"Data workers: {data.get('num_workers')}")
    for note in data.get("notes", []):
        print(f"Data note: {note}")
    print()

    lightning = report["lightning"]
    trainer = lightning["trainer"]
    print("Lightning trainer:")
    for key, value in trainer.items():
        print(f"  {key}: {value}")
    print("Callbacks:", ", ".join(lightning["callbacks"]) if lightning["callbacks"] else "(default/none in config)")
    print(f"ModelCheckpoint configured: {lightning['has_modelcheckpoint']}")
    print()

    if report["conditioning"]:
        print("Conditioning embedders:")
        for embedder in report["conditioning"]:
            key = embedder.get("input_key") or embedder.get("input_keys") or "(missing input key)"
            print(f"  [{embedder['index']}] {embedder.get('target') or '(missing target)'} <- {key}")
        print()

    print("Target paths:")
    if report["targets"]:
        for target in report["targets"]:
            print(f"  {target['path']}: {target['target']}")
    else:
        print("  (none)")
    print()

    if report["missing_targets"]:
        print("Likely missing target keys:")
        for item in report["missing_targets"]:
            print(f"  {item['path']}: {item['reason']}")
        print()

    if report["placeholders"]:
        print("Placeholders to resolve:")
        for item in report["placeholders"]:
            print(f"  {item['path']}: {item['value']}")
        print()

    if report.get("source_placeholders"):
        print("Source placeholder/comment hints:")
        for item in report["source_placeholders"]:
            print(f"  {item['path']}: {item['value']}")
        print()

    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
        print()

    print("Selected command template:")
    print(f"  {report['command_template']}")
    print()
    print("No training, imports, checkpoint loading, dataset reads, or downloads were performed.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static inspector for generative-models training configs")
    parser.add_argument(
        "--config",
        "-c",
        action="append",
        default=[],
        help="YAML config path. Repeat to mimic main.py --base left-to-right merge order.",
    )
    parser.add_argument(
        "--dotlist",
        nargs="*",
        default=[],
        help="OmegaConf-style key=value overrides merged after all configs.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--resume", default="", help="Optional resume path to check for launcher conflicts")
    parser.add_argument("--name", "-n", default="", help="Optional run name to check for resume conflicts")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = build_report(args)
    except ConfigLoadError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {"ok": True, **report}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
