#!/usr/bin/env python3
"""Validate and print a safe CLAP/NaFlexClap audio zero-shot command plan.

This helper mirrors the audio zero-shot argument surface but never loads
checkpoints, creates models, downloads datasets, or runs evaluation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_TEMPLATE = "This is a sound of {}."


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _open_clip_package_dirs() -> Iterable[Path]:
    spec = importlib.util.find_spec("open_clip")
    if spec is None:
        return []
    if spec.submodule_search_locations:
        return [Path(path) for path in spec.submodule_search_locations]
    if spec.origin:
        return [Path(spec.origin).parent]
    return []


def _get_model_audio_cfg_from_json(model_name: str) -> Dict[str, Any] | None:
    for package_dir in _open_clip_package_dirs():
        config_path = package_dir / "model_configs" / f"{model_name}.json"
        if not config_path.exists():
            continue
        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        audio_cfg = config.get("audio_cfg")
        return dict(audio_cfg) if isinstance(audio_cfg, dict) else None
    return None


def _get_model_audio_cfg(model_name: str) -> Dict[str, Any] | None:
    try:
        from open_clip import get_model_config

        config = get_model_config(model_name)
        if config:
            audio_cfg = config.get("audio_cfg")
            if isinstance(audio_cfg, dict):
                return dict(audio_cfg)
    except Exception:
        pass
    return _get_model_audio_cfg_from_json(model_name)


def _quote_command(parts: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _build_real_command(args: argparse.Namespace) -> List[str]:
    command = [
        "python",
        "-m",
        "open_clip_train.main",
        "--model",
        args.model,
        "--audio-zeroshot-dataset",
        args.audio_zeroshot_dataset,
        "--audio-zeroshot-split",
        args.audio_zeroshot_split,
        "--audio-zeroshot-audio-key",
        args.audio_zeroshot_audio_key,
        "--audio-zeroshot-target-key",
        args.audio_zeroshot_target_key,
        "--audio-zeroshot-class-key",
        args.audio_zeroshot_class_key,
        "--batch-size",
        str(args.batch_size),
        "--device",
        args.device,
        "--precision",
        args.precision,
        "--audio-zeroshot-workers",
        str(args.audio_zeroshot_workers),
        "--zeroshot-frequency",
        "1",
    ]
    if args.pretrained:
        command.extend(["--pretrained", args.pretrained])
    if args.checkpoint:
        command.extend(["--resume", args.checkpoint])
    if args.naflex_seq_lens:
        command.extend(["--naflex-seq-lens", *[str(value) for value in args.naflex_seq_lens]])
    for template in args.audio_zeroshot_templates:
        command.extend(["--audio-zeroshot-template", template])
    return command


def _validate(args: argparse.Namespace, audio_cfg: Dict[str, Any] | None) -> List[str]:
    issues: List[str] = []
    if not args.model:
        issues.append("--model is required")
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint).expanduser()
        if not checkpoint_path.exists():
            issues.append("checkpoint path does not exist yet; real evaluation will fail until it is available")
    if not args.checkpoint and not args.pretrained:
        issues.append("provide --pretrained for hosted weights or --checkpoint for a trusted local checkpoint")
    if not args.audio_zeroshot_dataset:
        issues.append("--audio-zeroshot-dataset is required")
    if args.batch_size <= 0:
        issues.append("--batch-size must be positive")
    if args.audio_zeroshot_workers < 0:
        issues.append("--audio-zeroshot-workers must be non-negative")
    if not args.naflex_seq_lens or any(value <= 0 for value in args.naflex_seq_lens):
        issues.append("--naflex-seq-lens values must be positive")
    for template in args.audio_zeroshot_templates:
        if "{}" not in template:
            issues.append(f"audio zero-shot template missing '{{}}' placeholder: {template!r}")
    if audio_cfg is None:
        issues.append("model config was not found or has no audio_cfg; confirm this is a CLAP/NaFlexClap model")
    return issues


def _plan(args: argparse.Namespace, audio_cfg: Dict[str, Any] | None, issues: List[str]) -> Dict[str, Any]:
    model_type = str((audio_cfg or {}).get("model_type", "")).lower()
    is_naflex = model_type == "naflexvit"
    deps = {
        "torchaudio": _module_available("torchaudio"),
        "torchlibrosa": _module_available("torchlibrosa"),
        "whisper": _module_available("whisper"),
        "datasets": _module_available("datasets"),
    }
    return {
        "ok": not issues,
        "issues": issues,
        "model": args.model,
        "checkpoint": args.checkpoint,
        "pretrained": args.pretrained,
        "use_ema": args.use_ema,
        "audio_cfg": audio_cfg,
        "transform_path": "AudioNaFlexTransformFactory + collate_naflex_dicts" if is_naflex else "audio_transform_v2 + _collate_audio_zero_shot",
        "dataset": {
            "id": args.audio_zeroshot_dataset,
            "split": args.audio_zeroshot_split,
            "audio_key": args.audio_zeroshot_audio_key,
            "target_key": args.audio_zeroshot_target_key,
            "class_key": args.audio_zeroshot_class_key,
            "will_download_in_real_run": True,
        },
        "templates": args.audio_zeroshot_templates,
        "runtime": {
            "batch_size": args.batch_size,
            "device": args.device,
            "precision": args.precision,
            "audio_zeroshot_workers": args.audio_zeroshot_workers,
            "audio_zeroshot_multiprocessing_context": args.audio_zeroshot_multiprocessing_context,
            "naflex_seq_lens": args.naflex_seq_lens,
        },
        "dependencies_available": deps,
        "real_command": _quote_command(_build_real_command(args)),
        "side_effects_of_this_helper": "none: no checkpoint load, no model build, no dataset download, no GPU use",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="OpenCLIP model name, e.g. CLAP-* or naflexclap_*.")
    parser.add_argument("--checkpoint", default=None, help="Optional checkpoint path for a trusted real evaluation run.")
    parser.add_argument("--pretrained", default=None, help="Optional hosted pretrained tag for python -m open_clip_train.main.")
    parser.add_argument("--use-ema", action="store_true", help="Record intent to prefer EMA weights in a custom real run if present.")
    parser.add_argument("--audio-zeroshot-dataset", required=True, help="HF dataset id, e.g. ashraq/esc50.")
    parser.add_argument("--audio-zeroshot-split", default="train")
    parser.add_argument("--audio-zeroshot-audio-key", default="audio")
    parser.add_argument("--audio-zeroshot-target-key", default="target")
    parser.add_argument("--audio-zeroshot-class-key", default="category")
    parser.add_argument(
        "--audio-zeroshot-template",
        dest="audio_zeroshot_templates",
        action="append",
        default=None,
        help="Prompt template. May be passed multiple times; every value must contain {}.",
    )
    parser.add_argument("--audio-zeroshot-workers", type=int, default=0)
    parser.add_argument(
        "--audio-zeroshot-multiprocessing-context",
        choices=["fork", "forkserver", "spawn"],
        default="forkserver",
    )
    parser.add_argument(
        "--naflex-seq-lens",
        type=int,
        nargs="+",
        default=[256],
        help="NaFlexClap audio-token cap for eval clips; ignored by fixed CLAP.",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--precision", default="amp_bf16")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()
    args.audio_zeroshot_templates = args.audio_zeroshot_templates or [DEFAULT_TEMPLATE]

    audio_cfg = _get_model_audio_cfg(args.model)
    issues = _validate(args, audio_cfg)
    plan = _plan(args, audio_cfg, issues)

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print("CLAP audio zero-shot dry-run plan")
        print("=================================")
        print(f"Status: {'ok' if plan['ok'] else 'needs attention'}")
        if issues:
            print("\nIssues:")
            for issue in issues:
                print(f"- {issue}")
        print("\nModel:")
        print(f"- name: {args.model}")
        print(f"- audio model_type: {(audio_cfg or {}).get('model_type', 'unknown')}")
        print(f"- transform path: {plan['transform_path']}")
        print("\nDataset:")
        print(f"- id/split: {args.audio_zeroshot_dataset} / {args.audio_zeroshot_split}")
        print(f"- keys: audio={args.audio_zeroshot_audio_key}, target={args.audio_zeroshot_target_key}, class={args.audio_zeroshot_class_key}")
        print("\nTemplates:")
        for template in args.audio_zeroshot_templates:
            print(f"- {template}")
        print("\nDependency probes:")
        for name, available in plan["dependencies_available"].items():
            print(f"- {name}: {'available' if available else 'missing'}")
        print("\nReal evaluation command:")
        print(plan["real_command"])
        print("\nThis helper performed no downloads, checkpoint loads, model builds, or GPU work.")

    return 0 if plan["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
