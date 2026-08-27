#!/usr/bin/env python3
"""Summarize a DeepLabCut PyTorch config without training anything."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from ruamel.yaml import YAML
except Exception:  # pragma: no cover - optional fallback
    YAML = None


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _load_yaml(text: str) -> Any:
    if YAML is not None:
        loader = YAML(typ="safe")
        return loader.load(text)

    try:
        import yaml as pyyaml  # type: ignore
    except Exception as exc:  # pragma: no cover - fallback only
        raise RuntimeError("YAML support is unavailable") from exc

    return pyyaml.safe_load(text)


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data: Any = None

    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            data = _load_yaml(text)
        except Exception:
            data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("The configuration root must be a mapping/object.")
    return data


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        return ", ".join(_fmt(item) for item in value) if value else "[]"
    if isinstance(value, dict):
        return ", ".join(sorted(str(key) for key in value.keys())) if value else "{}"
    return str(value)


def _section_status(cfg: dict[str, Any], key: str) -> str:
    return "present" if key in cfg and cfg[key] is not None else "missing"


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def summarize(cfg: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    method = str(cfg.get("method", cfg.get("metadata", {}).get("method", ""))).lower()
    net_type = cfg.get("net_type", "-")
    device = cfg.get("device", "-")

    lines.append("DeepLabCut PyTorch configuration summary")
    lines.append(f"- method: {method or '-'}")
    lines.append(f"- net_type: {net_type}")
    lines.append(f"- device: {device}")
    lines.append(f"- top-level keys: {_fmt(sorted(cfg.keys()))}")
    lines.append("")

    lines.append("Sections")
    for section in ["model", "runner", "train_settings", "inference", "detector"]:
        status = _section_status(cfg, section)
        lines.append(f"- {section}: {status}")

    lines.append("")
    model = _as_mapping(cfg.get("model"))
    runner = _as_mapping(cfg.get("runner"))
    train_settings = _as_mapping(cfg.get("train_settings"))
    inference = _as_mapping(cfg.get("inference"))
    detector = _as_mapping(cfg.get("detector"))
    metadata = _as_mapping(cfg.get("metadata"))

    lines.append("Key settings")
    lines.append(f"- model.backbone.type: {_fmt((model.get('backbone') or {}).get('type'))}")
    lines.append(f"- model.backbone.model_name: {_fmt((model.get('backbone') or {}).get('model_name'))}")
    lines.append(f"- model.heads: {_fmt(sorted((model.get('heads') or {}).keys()))}")
    lines.append(f"- runner.type: {_fmt(runner.get('type'))}")
    lines.append(f"- runner.gpus: {_fmt(runner.get('gpus'))}")
    lines.append(f"- train_settings.batch_size: {_fmt(train_settings.get('batch_size'))}")
    lines.append(f"- train_settings.epochs: {_fmt(train_settings.get('epochs'))}")
    lines.append(f"- runner.snapshots.save_epochs: {_fmt((runner.get('snapshots') or {}).get('save_epochs'))}")
    lines.append(f"- train_settings.display_iters: {_fmt(train_settings.get('display_iters'))}")
    lines.append(f"- logger.type: {_fmt((cfg.get('logger') or {}).get('type'))}")
    lines.append(f"- inference.snapshot: {_fmt(inference.get('snapshot'))}")
    lines.append(f"- inference.conditions: {_fmt(inference.get('conditions'))}")
    lines.append(f"- inference.eval.pcutoff: {_fmt((inference.get('eval') or {}).get('pcutoff'))}")
    lines.append(f"- detector.model.type: {_fmt((detector.get('model') or {}).get('type'))}")
    lines.append(f"- detector.device: {_fmt(detector.get('device'))}")
    lines.append(f"- metadata.bodyparts: {_fmt(metadata.get('bodyparts'))}")
    lines.append(f"- metadata.individuals: {_fmt(metadata.get('individuals'))}")

    return lines


def validate(cfg: dict[str, Any]) -> int:
    issues = 0
    for section in ["model", "runner", "train_settings", "inference"]:
        value = cfg.get(section)
        if value is None:
            _warn(f"missing required section: {section}")
            issues += 1
        elif not isinstance(value, dict):
            _warn(f"section {section} exists but is not a mapping")
            issues += 1

    method = str(cfg.get("method", cfg.get("metadata", {}).get("method", ""))).lower()
    detector = cfg.get("detector")
    if detector is None:
        if method in {"td", "ctd"}:
            _warn("detector section is missing for a top-down or CTD config")
            issues += 1
        else:
            _warn("detector section is missing; that is normal for bottom-up configs")
    elif not isinstance(detector, dict):
        _warn("detector section exists but is not a mapping")
        issues += 1
    else:
        for section in ["model", "runner", "train_settings"]:
            if detector.get(section) is None:
                _warn(f"detector.{section} is missing")
                issues += 1

    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize a DeepLabCut PyTorch config (YAML or JSON) and warn about missing sections.",
    )
    parser.add_argument("config", type=Path, help="Path to a pytorch_config YAML or JSON file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except Exception as exc:
        _warn(str(exc))
        return 2

    issues = validate(cfg)
    for line in summarize(cfg):
        print(line)

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
