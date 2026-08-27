#!/usr/bin/env python3
"""Summarize a Neuralangelo YAML config without importing Neuralangelo.

The script resolves YAML parents, validates strict override paths, optionally
checks prepared-data files, and can probe generic CUDA/PyTorch packages. It is
safe for planning because it does not execute training and does not import
Neuralangelo project modules.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - depends on user environment
    yaml = None


MISSING = object()


class ConfigError(RuntimeError):
    pass


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except Exception:
        return str(path)


def require_yaml() -> None:
    if yaml is None:
        raise ConfigError("PyYAML is required to parse Neuralangelo config files; install pyyaml in this environment.")


def read_yaml_file(path: Path) -> Dict[str, Any]:
    require_yaml()
    if not path.exists():
        raise ConfigError(f"YAML file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)  # type: ignore[union-attr]
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Expected mapping at YAML root: {path}")
    return data


def recursive_merge(base: MutableMapping[str, Any], update: Mapping[str, Any]) -> MutableMapping[str, Any]:
    for key, value in update.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), MutableMapping):
            recursive_merge(base[key], value)  # type: ignore[index]
        else:
            base[key] = copy.deepcopy(value)
    return base


def resolve_config_path(raw: str, project_root: Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    root_candidate = project_root / path
    if root_candidate.exists():
        return root_candidate
    return path


def resolve_parent_path(parent_value: str, project_root: Path, child_dir: Path, notes: List[str]) -> Path:
    raw = Path(parent_value)
    if raw.is_absolute():
        return raw
    project_candidate = project_root / raw
    if project_candidate.exists():
        return project_candidate
    child_candidate = child_dir / raw
    if child_candidate.exists():
        notes.append(
            f"Parent {parent_value!r} resolved relative to child config directory; "
            "train.py normally resolves non-absolute parents from the launch working directory."
        )
        return child_candidate
    return project_candidate


def load_config_tree(path: Path, project_root: Path, seen: List[Path], notes: List[str]) -> Tuple[Dict[str, Any], List[Path]]:
    resolved = path.resolve()
    if resolved in seen:
        chain = " -> ".join(display_path(p) for p in seen + [resolved])
        raise ConfigError(f"Cyclic _parent_ chain: {chain}")
    data = read_yaml_file(path)
    loaded: List[Path] = []
    parent_value = data.pop("_parent_", None)
    if parent_value:
        parent_path = resolve_parent_path(str(parent_value), project_root, path.parent, notes)
        parent_cfg, parent_chain = load_config_tree(parent_path, project_root, seen + [resolved], notes)
        cfg: Dict[str, Any] = parent_cfg
        loaded.extend(parent_chain)
    else:
        cfg = {}
    recursive_merge(cfg, data)
    loaded.append(path)
    return cfg, loaded


def load_full_config(config_path: Path, project_root: Path, include_imaginaire_base: bool, notes: List[str]) -> Tuple[Dict[str, Any], List[Path]]:
    cfg: Dict[str, Any] = {}
    loaded: List[Path] = []
    if include_imaginaire_base:
        base_path = project_root / "imaginaire" / "config_base.yaml"
        if base_path.exists():
            base_cfg, base_chain = load_config_tree(base_path, project_root, [], notes)
            recursive_merge(cfg, base_cfg)
            loaded.extend(base_chain)
        else:
            notes.append("imaginaire/config_base.yaml was not found under --project-root; summary uses only the requested config tree.")
    requested_cfg, requested_chain = load_config_tree(config_path, project_root, [], notes)
    recursive_merge(cfg, requested_cfg)
    loaded.extend(requested_chain)
    return cfg, loaded


def get_path(cfg: Mapping[str, Any], dotted: str, default: Any = MISSING) -> Any:
    cur: Any = cfg
    for part in dotted.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            if default is MISSING:
                return MISSING
            return default
    return cur


def set_path(cfg: MutableMapping[str, Any], dotted: str, value: Any) -> bool:
    cur: Any = cfg
    parts = dotted.split(".")
    for part in parts[:-1]:
        if not isinstance(cur, MutableMapping) or part not in cur:
            return False
        cur = cur[part]
    if not isinstance(cur, MutableMapping) or parts[-1] not in cur:
        return False
    cur[parts[-1]] = value
    return True


def parse_override(raw: str) -> Tuple[str, Any]:
    text = raw.strip()
    if text.startswith("--"):
        text = text[2:]
    if not text:
        raise ConfigError("Empty override")
    if "=" in text:
        key, value_text = text.split("=", 1)
        if value_text == "":
            value = None
        elif yaml is not None:
            value = yaml.safe_load(value_text)  # type: ignore[union-attr]
        else:
            value = value_text
    else:
        if text.endswith("!"):
            key = text[:-1]
            value = False
        else:
            key = text
            value = True
    if not key or any(part == "" for part in key.split(".")):
        raise ConfigError(f"Invalid override key: {raw}")
    return key, value


def validate_and_apply_overrides(cfg: MutableMapping[str, Any], overrides: Sequence[str], apply: bool) -> Tuple[List[str], List[str]]:
    reports: List[str] = []
    warnings: List[str] = []
    for raw in overrides:
        try:
            key, value = parse_override(raw)
        except ConfigError as exc:
            warnings.append(str(exc))
            continue
        existing = get_path(cfg, key)
        if existing is MISSING:
            warnings.append(f"Override path would fail strict update: {key}")
            continue
        reports.append(f"{key}: {existing!r} -> {value!r}")
        if apply:
            set_path(cfg, key, value)
    return reports, warnings


def as_str(value: Any) -> str:
    if value is MISSING:
        return "<missing>"
    return repr(value) if isinstance(value, str) else str(value)


def section(title: str, rows: Sequence[Tuple[str, Any]]) -> List[str]:
    lines = [f"## {title}"]
    width = max((len(k) for k, _ in rows), default=0)
    for key, value in rows:
        lines.append(f"- {key.ljust(width)} : {as_str(value)}")
    lines.append("")
    return lines


def resolve_data_root(cfg: Mapping[str, Any], project_root: Path) -> Path | None:
    root = get_path(cfg, "data.root")
    if root in (MISSING, None, ""):
        return None
    root_path = Path(str(root))
    return root_path if root_path.is_absolute() else project_root / root_path


def check_data(cfg: Mapping[str, Any], project_root: Path, max_frame_checks: int) -> Tuple[List[str], List[str]]:
    lines: List[str] = []
    warnings: List[str] = []
    data_root = resolve_data_root(cfg, project_root)
    if data_root is None:
        warnings.append("data.root is missing or null.")
        return lines, warnings
    lines.append(f"data.root resolved: {display_path(data_root)}")
    if not data_root.exists():
        warnings.append(f"data.root does not exist: {display_path(data_root)}")
        return lines, warnings
    transforms = data_root / "transforms.json"
    if not transforms.exists():
        warnings.append(f"transforms.json not found under data.root: {display_path(transforms)}")
        return lines, warnings
    try:
        with transforms.open("r", encoding="utf-8") as handle:
            meta = json.load(handle)
    except Exception as exc:
        warnings.append(f"Could not parse transforms.json: {exc}")
        return lines, warnings
    frames = meta.get("frames", [])
    lines.append(f"transforms frames: {len(frames)}")
    for field in ["fl_x", "fl_y", "cx", "cy", "sphere_center", "sphere_radius"]:
        if field not in meta:
            warnings.append(f"transforms.json missing field: {field}")
    missing_images = 0
    for frame in frames[:max_frame_checks]:
        rel = frame.get("file_path") if isinstance(frame, Mapping) else None
        if not rel:
            warnings.append("A checked frame is missing file_path.")
            continue
        if not (data_root / str(rel)).exists():
            missing_images += 1
    if missing_images:
        warnings.append(f"{missing_images} of first {min(len(frames), max_frame_checks)} checked frame images were missing.")
    appear = bool(get_path(cfg, "model.appear_embed.enabled", False))
    num_images = get_path(cfg, "data.num_images", None)
    if appear:
        if num_images in (None, ""):
            warnings.append("Appearance embeddings are enabled but data.num_images is missing/null.")
        elif isinstance(num_images, int) and frames and num_images != len(frames):
            warnings.append(f"data.num_images={num_images} differs from transforms frame count {len(frames)}; confirm this is intentional.")
    return lines, warnings


def runtime_probe() -> Tuple[List[str], List[str]]:
    lines: List[str] = []
    warnings: List[str] = []
    try:
        import torch  # type: ignore
        lines.append(f"torch: {getattr(torch, '__version__', '<unknown>')}")
        lines.append(f"torch.version.cuda: {getattr(torch.version, 'cuda', None)}")
        cuda_available = bool(torch.cuda.is_available())
        lines.append(f"torch.cuda.is_available: {cuda_available}")
        lines.append(f"torch.cuda.device_count: {torch.cuda.device_count()}")
        if cuda_available and torch.cuda.device_count() > 0:
            lines.append(f"cuda device 0: {torch.cuda.get_device_name(0)}")
        else:
            warnings.append("CUDA is not available to PyTorch in this environment.")
    except Exception as exc:
        warnings.append(f"torch probe failed: {exc}")
    for module_name in ["torchvision", "tinycudann"]:
        try:
            module = __import__(module_name)
            lines.append(f"{module_name}: import ok {getattr(module, '__version__', '')}".rstrip())
        except Exception as exc:
            warnings.append(f"{module_name} import failed: {exc}")
    return lines, warnings


def heuristic_warnings(cfg: Mapping[str, Any]) -> List[str]:
    warnings: List[str] = []
    if get_path(cfg, "model.object.sdf.encoding.type") == "hashgrid":
        dict_size = get_path(cfg, "model.object.sdf.encoding.hashgrid.dict_size", None)
        dim = get_path(cfg, "model.object.sdf.encoding.hashgrid.dim", None)
        if isinstance(dict_size, int) and isinstance(dim, int) and dict_size >= 22 and dim >= 8:
            warnings.append("Default/high hash-grid capacity may need about 24 GB VRAM; use memory overrides on smaller GPUs.")
    if bool(get_path(cfg, "model.appear_embed.enabled", False)) and get_path(cfg, "data.num_images", None) in (None, ""):
        warnings.append("model.appear_embed.enabled is true but data.num_images is missing/null.")
    train_batch = get_path(cfg, "data.train.batch_size", None)
    val_batch = get_path(cfg, "data.val.batch_size", None)
    if isinstance(train_batch, int) and train_batch > 1:
        warnings.append("data.train.batch_size > 1 increases memory; Neuralangelo scene configs usually use 1.")
    if isinstance(val_batch, int) and val_batch > 1:
        warnings.append("data.val.batch_size > 1 can cause validation OOM.")
    val_size = get_path(cfg, "data.val.image_size", None)
    if isinstance(val_size, list) and len(val_size) == 2 and all(isinstance(x, int) for x in val_size):
        if val_size[0] * val_size[1] > 400 * 600:
            warnings.append("Large data.val.image_size can cause validation OOM; reduce validation size before reducing train quality.")
    if get_path(cfg, "model.background.enabled", True) is False:
        bg_samples = get_path(cfg, "model.render.num_samples.background", 0)
        if bg_samples not in (0, None):
            warnings.append("model.background.enabled is false but background samples are nonzero; consider setting model.render.num_samples.background=0.")
    return warnings


def build_summary(cfg: Mapping[str, Any], loaded: Sequence[Path], override_reports: Sequence[str], data_lines: Sequence[str], probe_lines: Sequence[str], warnings: Sequence[str], notes: Sequence[str]) -> str:
    lines: List[str] = ["# Neuralangelo config summary", ""]
    lines.append("## Loaded YAML files")
    for path in loaded:
        lines.append(f"- {display_path(path)}")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.extend(f"- {note}" for note in notes)
        lines.append("")
    if override_reports:
        lines.append("## Overrides validated")
        lines.extend(f"- {report}" for report in override_reports)
        lines.append("")

    lines.extend(section("Schedule and logging", [
        ("max_iter", get_path(cfg, "max_iter")),
        ("max_epoch", get_path(cfg, "max_epoch")),
        ("logging_iter", get_path(cfg, "logging_iter")),
        ("validation_iter", get_path(cfg, "validation_iter")),
        ("wandb_scalar_iter", get_path(cfg, "wandb_scalar_iter")),
        ("wandb_image_iter", get_path(cfg, "wandb_image_iter")),
        ("checkpoint.save_iter", get_path(cfg, "checkpoint.save_iter")),
        ("checkpoint.save_latest_iter", get_path(cfg, "checkpoint.save_latest_iter")),
        ("checkpoint.save_period", get_path(cfg, "checkpoint.save_period")),
    ]))
    lines.extend(section("Data", [
        ("data.type", get_path(cfg, "data.type")),
        ("data.root", get_path(cfg, "data.root")),
        ("data.preload", get_path(cfg, "data.preload")),
        ("data.num_workers", get_path(cfg, "data.num_workers")),
        ("data.num_images", get_path(cfg, "data.num_images")),
        ("data.train.image_size", get_path(cfg, "data.train.image_size")),
        ("data.train.batch_size", get_path(cfg, "data.train.batch_size")),
        ("data.train.subset", get_path(cfg, "data.train.subset")),
        ("data.val.image_size", get_path(cfg, "data.val.image_size")),
        ("data.val.batch_size", get_path(cfg, "data.val.batch_size")),
        ("data.val.subset", get_path(cfg, "data.val.subset")),
        ("data.val.max_viz_samples", get_path(cfg, "data.val.max_viz_samples")),
        ("data.readjust.center", get_path(cfg, "data.readjust.center")),
        ("data.readjust.scale", get_path(cfg, "data.readjust.scale")),
    ]))
    lines.extend(section("Model", [
        ("model.type", get_path(cfg, "model.type")),
        ("sdf.encoding.type", get_path(cfg, "model.object.sdf.encoding.type")),
        ("hashgrid.dict_size", get_path(cfg, "model.object.sdf.encoding.hashgrid.dict_size")),
        ("hashgrid.dim", get_path(cfg, "model.object.sdf.encoding.hashgrid.dim")),
        ("hashgrid.range", get_path(cfg, "model.object.sdf.encoding.hashgrid.range")),
        ("coarse2fine.enabled", get_path(cfg, "model.object.sdf.encoding.coarse2fine.enabled")),
        ("coarse2fine.init_active_level", get_path(cfg, "model.object.sdf.encoding.coarse2fine.init_active_level")),
        ("coarse2fine.step", get_path(cfg, "model.object.sdf.encoding.coarse2fine.step")),
        ("gradient.mode", get_path(cfg, "model.object.sdf.gradient.mode")),
        ("gradient.taps", get_path(cfg, "model.object.sdf.gradient.taps")),
        ("inside_out", get_path(cfg, "model.object.sdf.mlp.inside_out")),
        ("background.enabled", get_path(cfg, "model.background.enabled")),
        ("background.white", get_path(cfg, "model.background.white")),
        ("appear_embed.enabled", get_path(cfg, "model.appear_embed.enabled")),
        ("appear_embed.dim", get_path(cfg, "model.appear_embed.dim")),
        ("render.rand_rays", get_path(cfg, "model.render.rand_rays")),
        ("samples.coarse", get_path(cfg, "model.render.num_samples.coarse")),
        ("samples.fine", get_path(cfg, "model.render.num_samples.fine")),
        ("samples.background", get_path(cfg, "model.render.num_samples.background")),
        ("num_sample_hierarchy", get_path(cfg, "model.render.num_sample_hierarchy")),
    ]))
    lines.extend(section("Trainer and optimizer", [
        ("trainer.type", get_path(cfg, "trainer.type")),
        ("loss_weight.render", get_path(cfg, "trainer.loss_weight.render")),
        ("loss_weight.eikonal", get_path(cfg, "trainer.loss_weight.eikonal")),
        ("loss_weight.curvature", get_path(cfg, "trainer.loss_weight.curvature")),
        ("amp.enabled", get_path(cfg, "trainer.amp_config.enabled")),
        ("grad_accum_iter", get_path(cfg, "trainer.grad_accum_iter")),
        ("ema.enabled", get_path(cfg, "trainer.ema_config.enabled")),
        ("optim.type", get_path(cfg, "optim.type")),
        ("optim.params.lr", get_path(cfg, "optim.params.lr")),
        ("optim.params.weight_decay", get_path(cfg, "optim.params.weight_decay")),
        ("optim.sched.type", get_path(cfg, "optim.sched.type")),
        ("optim.sched.warm_up_end", get_path(cfg, "optim.sched.warm_up_end")),
        ("optim.sched.two_steps", get_path(cfg, "optim.sched.two_steps")),
        ("optim.sched.gamma", get_path(cfg, "optim.sched.gamma")),
    ]))

    if data_lines:
        lines.append("## Data file checks")
        lines.extend(f"- {line}" for line in data_lines)
        lines.append("")
    if probe_lines:
        lines.append("## Runtime probe")
        lines.extend(f"- {line}" for line in probe_lines)
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a Neuralangelo YAML config without source imports.")
    parser.add_argument("--config", required=True, help="Training config YAML path.")
    parser.add_argument("--project-root", default=".", help="Project root for resolving relative configs and data roots.")
    parser.add_argument("--no-imaginaire-base", action="store_true", help="Do not merge imaginaire/config_base.yaml first.")
    parser.add_argument("--override", action="append", default=[], help="Strict config override to validate and apply. Repeatable.")
    parser.add_argument("--no-apply-overrides", action="store_true", help="Validate overrides but keep summary at YAML values.")
    parser.add_argument("--check-data", action="store_true", help="Check data.root/transforms.json and a few referenced images.")
    parser.add_argument("--max-frame-checks", type=int, default=5, help="Number of frame image paths to check with --check-data.")
    parser.add_argument("--probe-runtime", action="store_true", help="Probe torch, torchvision, tinycudann, and CUDA without Neuralangelo imports.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary instead of Markdown.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).expanduser()
    project_root = project_root.resolve() if project_root.exists() else project_root
    notes: List[str] = []
    warnings: List[str] = []
    try:
        config_path = resolve_config_path(args.config, project_root)
        cfg, loaded = load_full_config(config_path, project_root, not args.no_imaginaire_base, notes)
        override_reports, override_warnings = validate_and_apply_overrides(cfg, args.override, not args.no_apply_overrides)
        warnings.extend(override_warnings)
        warnings.extend(heuristic_warnings(cfg))
        data_lines: List[str] = []
        if args.check_data:
            data_lines, data_warnings = check_data(cfg, project_root, args.max_frame_checks)
            warnings.extend(data_warnings)
        probe_lines: List[str] = []
        if args.probe_runtime:
            probe_lines, probe_warnings = runtime_probe()
            warnings.extend(probe_warnings)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "loaded": [display_path(p) for p in loaded],
            "notes": notes,
            "warnings": warnings,
            "overrides": list(override_reports),
            "summary": {
                "max_iter": get_path(cfg, "max_iter", None),
                "data_root": get_path(cfg, "data.root", None),
                "data_type": get_path(cfg, "data.type", None),
                "train_image_size": get_path(cfg, "data.train.image_size", None),
                "val_image_size": get_path(cfg, "data.val.image_size", None),
                "hashgrid_dict_size": get_path(cfg, "model.object.sdf.encoding.hashgrid.dict_size", None),
                "hashgrid_dim": get_path(cfg, "model.object.sdf.encoding.hashgrid.dim", None),
                "rand_rays": get_path(cfg, "model.render.rand_rays", None),
                "appear_embed": get_path(cfg, "model.appear_embed.enabled", None),
                "num_images": get_path(cfg, "data.num_images", None),
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(build_summary(cfg, loaded, override_reports, data_lines, probe_lines, warnings, notes), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
