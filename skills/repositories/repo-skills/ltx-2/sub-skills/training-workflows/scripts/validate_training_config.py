#!/usr/bin/env python3
"""Safely validate an LTX Trainer YAML config without launching training.

The default mode performs strict schema and path checks. Use --relaxed-paths
while editing placeholder configs: the script still validates schema and core
semantics by substituting temporary local files/directories for model/data
paths, but it reports that real path existence was not verified.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


CONDITION_TYPES = {"first_frame", "prefix", "suffix", "spatial_crop", "mask", "reference"}
AUDIO_FORBIDDEN_CONDITIONS = {"first_frame", "spatial_crop"}
VALIDATION_PATH_FIELDS = {
    "first_frame": ["image_or_video"],
    "prefix": ["video", "audio"],
    "suffix": ["video", "audio"],
    "spatial_crop": ["video"],
    "mask": ["video", "audio", "mask"],
    "reference": ["video", "audio"],
    "video_to_audio": ["video"],
    "audio_to_video": ["audio"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to an LTX Trainer YAML config")
    parser.add_argument(
        "--relaxed-paths",
        action="store_true",
        help="Validate schema/semantics while allowing placeholder model/data/media paths",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of human-readable text")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Config file does not exist: {path}")
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"PyYAML is required to read YAML configs: {exc}") from exc
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping at top level")
    return data


def strategy_sources(raw: dict[str, Any]) -> set[str]:
    strategy = raw.get("training_strategy") or {}
    if not isinstance(strategy, dict):
        return {"conditions"}
    name = strategy.get("name", "text_to_video")
    sources: set[str] = {"conditions"}

    if name == "flexible":
        for modality_name in ("video", "audio"):
            modality = strategy.get(modality_name)
            if not isinstance(modality, dict):
                continue
            latents_dir = modality.get("latents_dir")
            if isinstance(latents_dir, str) and latents_dir:
                sources.add(latents_dir)
            for cond in modality.get("conditions") or []:
                if not isinstance(cond, dict):
                    continue
                cond_type = cond.get("type")
                if cond_type == "reference" and isinstance(cond.get("latents_dir"), str):
                    sources.add(cond["latents_dir"])
                if cond_type == "mask" and isinstance(cond.get("mask_dir"), str):
                    sources.add(cond["mask_dir"])
        return sources

    if name == "text_to_video":
        sources.add("latents")
        if strategy.get("with_audio"):
            sources.add(strategy.get("audio_latents_dir") or "audio_latents")
        return sources

    if name == "video_to_video":
        sources.update({"latents", strategy.get("reference_latents_dir") or "reference_latents"})
        return sources

    return sources


def static_checks(raw: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    model = raw.get("model")
    if not isinstance(model, dict):
        errors.append("Missing or invalid 'model' section")
    else:
        model_path = model.get("model_path")
        if isinstance(model_path, str) and model_path.startswith(("http://", "https://")):
            errors.append("model.model_path must be a local path, not a URL")
        if model.get("training_mode", "lora") == "lora" and raw.get("lora") is None:
            errors.append("lora section is required when model.training_mode is 'lora'")
        split_hint = isinstance(model_path, str) and ("diffusion_models" in model_path or "transformer" in model_path)
        if split_hint and not model.get("video_vae_path"):
            warnings.append("model.model_path looks like a split transformer; video_vae_path is usually required")
        strategy = raw.get("training_strategy") or {}
        touches_audio = isinstance(strategy, dict) and isinstance(strategy.get("audio"), dict)
        validation = raw.get("validation") or {}
        if isinstance(validation, dict) and validation.get("generate_audio") is True:
            touches_audio = True
        if split_hint and touches_audio and not model.get("audio_vae_path"):
            warnings.append("split-pack audio/joint runs usually require model.audio_vae_path")

    strategy = raw.get("training_strategy")
    if not isinstance(strategy, dict):
        errors.append("Missing or invalid 'training_strategy' section")
    else:
        name = strategy.get("name", "text_to_video")
        if name != "flexible":
            warnings.append(f"training_strategy.name is {name!r}; new configs should prefer 'flexible'")
        if name == "flexible":
            generated = []
            for modality_name in ("video", "audio"):
                modality = strategy.get(modality_name)
                if not isinstance(modality, dict):
                    continue
                if modality.get("is_generated") is True:
                    generated.append(modality_name)
                if not isinstance(modality.get("latents_dir"), str) or not modality.get("latents_dir"):
                    errors.append(f"training_strategy.{modality_name}.latents_dir must be a non-empty string")
                conditions = modality.get("conditions") or []
                if not isinstance(conditions, list):
                    errors.append(f"training_strategy.{modality_name}.conditions must be a list")
                    continue
                for idx, cond in enumerate(conditions):
                    if not isinstance(cond, dict):
                        errors.append(f"training_strategy.{modality_name}.conditions[{idx}] must be a mapping")
                        continue
                    cond_type = cond.get("type")
                    if cond_type not in CONDITION_TYPES:
                        errors.append(f"Unsupported condition type at {modality_name}.conditions[{idx}]: {cond_type!r}")
                    if modality_name == "audio" and cond_type in AUDIO_FORBIDDEN_CONDITIONS:
                        errors.append(f"Audio modality cannot use condition type {cond_type!r}")
            if not generated:
                errors.append("At least one flexible modality must set is_generated: true")

    validation = raw.get("validation")
    if isinstance(validation, dict):
        dims = validation.get("video_dims")
        if dims is not None:
            if not (isinstance(dims, (list, tuple)) and len(dims) == 3 and all(isinstance(x, int) for x in dims)):
                errors.append("validation.video_dims must be [width, height, frames]")
            else:
                width, height, frames = dims
                if width % 32 != 0 or height % 32 != 0:
                    errors.append("validation.video_dims width and height should be divisible by 32 for the default VAE")
                if frames % 8 != 1:
                    warnings.append("validation.video_dims frame count does not satisfy frames % 8 == 1 for the default VAE")
        has_samples = bool(validation.get("samples") or validation.get("prompts"))
        if has_samples and validation.get("generate_video") is False and validation.get("generate_audio") is False:
            errors.append("Validation samples require at least one of generate_video/generate_audio")

    hub = raw.get("hub")
    if isinstance(hub, dict) and hub.get("push_to_hub") and not hub.get("hub_model_id"):
        errors.append("hub.hub_model_id is required when hub.push_to_hub is true")

    return errors, warnings


def validation_media_paths(raw: dict[str, Any]) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    validation = raw.get("validation") or {}
    if not isinstance(validation, dict):
        return result
    for key in ("images", "reference_videos"):
        value = validation.get(key)
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str):
                    result.append((f"validation.{key}[{i}]", Path(item).expanduser()))
    samples = validation.get("samples") or []
    if isinstance(samples, list):
        for sample_i, sample in enumerate(samples):
            if not isinstance(sample, dict):
                continue
            for cond_i, cond in enumerate(sample.get("conditions") or []):
                if not isinstance(cond, dict):
                    continue
                for field in VALIDATION_PATH_FIELDS.get(cond.get("type"), []):
                    value = cond.get(field)
                    if isinstance(value, str):
                        result.append((f"validation.samples[{sample_i}].conditions[{cond_i}].{field}", Path(value).expanduser()))
    return result


def check_paths(raw: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    model = raw.get("model") or {}
    if isinstance(model, dict):
        for field in ("model_path", "video_vae_path", "audio_vae_path"):
            value = model.get(field)
            if value is None:
                continue
            path = Path(str(value)).expanduser()
            if field == "model_path" and not path.is_file():
                errors.append(f"model.{field} does not exist as a file: {path}")
            elif field in {"video_vae_path", "audio_vae_path"} and not path.is_file():
                errors.append(f"model.{field} does not exist as a file: {path}")
        text_encoder_path = model.get("text_encoder_path")
        if text_encoder_path is not None:
            path = Path(str(text_encoder_path)).expanduser()
            if not path.exists():
                errors.append(f"model.text_encoder_path does not exist: {path}")
        load_checkpoint = model.get("load_checkpoint")
        if load_checkpoint:
            path = Path(str(load_checkpoint)).expanduser()
            if not path.exists():
                errors.append(f"model.load_checkpoint does not exist: {path}")

    data = raw.get("data") or {}
    if isinstance(data, dict):
        data_root_value = data.get("preprocessed_data_root")
        if data_root_value:
            data_root = Path(str(data_root_value)).expanduser()
            if not data_root.is_dir():
                errors.append(f"data.preprocessed_data_root does not exist as a directory: {data_root}")
            else:
                for source in sorted(strategy_sources(raw)):
                    if not (data_root / source).is_dir():
                        errors.append(f"Required strategy data directory is missing: {data_root / source}")
        else:
            errors.append("data.preprocessed_data_root is required")

    for label, path in validation_media_paths(raw):
        if not path.exists():
            warnings.append(f"Validation media path not found ({label}): {path}")

    return errors, warnings


def relaxed_copy(raw: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    cfg = copy.deepcopy(raw)
    model = cfg.setdefault("model", {})
    if isinstance(model, dict):
        fake_model = temp_root / "model.safetensors"
        fake_model.write_bytes(b"placeholder")
        model["model_path"] = str(fake_model)
        if model.get("text_encoder_path") is not None:
            fake_text_encoder = temp_root / "text_encoder"
            fake_text_encoder.mkdir(exist_ok=True)
            model["text_encoder_path"] = str(fake_text_encoder)
        for field in ("video_vae_path", "audio_vae_path"):
            if model.get(field) is not None:
                fake_component = temp_root / f"{field}.safetensors"
                fake_component.write_bytes(b"placeholder")
                model[field] = str(fake_component)
        if model.get("load_checkpoint"):
            ckpt = temp_root / "checkpoints" / "lora_weights_step_00001.safetensors"
            ckpt.parent.mkdir(parents=True, exist_ok=True)
            ckpt.write_bytes(b"placeholder")
            model["load_checkpoint"] = str(ckpt)

    data = cfg.setdefault("data", {})
    if isinstance(data, dict):
        data_root = temp_root / "preprocessed"
        data_root.mkdir(parents=True, exist_ok=True)
        for source in strategy_sources(raw):
            (data_root / source).mkdir(parents=True, exist_ok=True)
        data["preprocessed_data_root"] = str(data_root)

    validation = cfg.get("validation")
    if isinstance(validation, dict):
        media = temp_root / "media"
        media.mkdir(exist_ok=True)
        fake_media = media / "placeholder.media"
        fake_media.write_bytes(b"placeholder")
        for key in ("images", "reference_videos"):
            if isinstance(validation.get(key), list):
                validation[key] = [str(fake_media) for _ in validation[key]]
    return cfg


def pydantic_validate(raw: dict[str, Any], relaxed_paths: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        from ltx_trainer.config import LtxTrainerConfig
    except Exception as exc:
        return [f"Could not import ltx_trainer.config.LtxTrainerConfig: {exc}"], warnings

    if relaxed_paths:
        with tempfile.TemporaryDirectory(prefix="ltx-trainer-config-") as tmp:
            cfg = relaxed_copy(raw, Path(tmp))
            try:
                LtxTrainerConfig(**cfg)
            except Exception as exc:  # pydantic reports detailed paths
                errors.append(f"Pydantic validation failed: {exc}")
    else:
        try:
            LtxTrainerConfig(**raw)
        except Exception as exc:
            errors.append(f"Pydantic validation failed: {exc}")
    return errors, warnings


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {"config": str(args.config), "relaxed_paths": args.relaxed_paths}
    try:
        raw = load_yaml(args.config)
    except Exception as exc:
        report.update({"ok": False, "errors": [str(exc)], "warnings": []})
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors, warnings = static_checks(raw)
    p_errors, p_warnings = pydantic_validate(raw, args.relaxed_paths)
    errors.extend(p_errors)
    warnings.extend(p_warnings)
    if args.relaxed_paths:
        warnings.append("relaxed path mode: real model/data/checkpoint path existence was not verified")
    else:
        path_errors, path_warnings = check_paths(raw)
        errors.extend(path_errors)
        warnings.extend(path_warnings)

    report.update(
        {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "required_data_dirs": sorted(strategy_sources(raw)),
        }
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "OK" if not errors else "FAILED"
        print(f"LTX Trainer config validation: {status}")
        print(f"Config: {args.config}")
        print("Required data dirs:", ", ".join(report["required_data_dirs"]) or "(unknown)")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"- {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
