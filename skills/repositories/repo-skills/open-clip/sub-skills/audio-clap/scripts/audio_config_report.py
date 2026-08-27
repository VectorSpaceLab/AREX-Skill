#!/usr/bin/env python3
"""Report OpenCLIP audio dependency and CLIPAudioCfg details without loading weights."""

from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable


DEFAULT_CLIP_AUDIO_CFG: Dict[str, Any] = {
    "model_type": "HTSAT",
    "model_name": "tiny",
    "audio_length": 1024,
    "clip_samples": 480000,
    "sample_rate": 48000,
    "mel_bins": 64,
    "window_size": 1024,
    "hop_size": 480,
    "fmin": 50,
    "fmax": 14000,
    "class_num": 527,
    "enable_fusion": False,
    "fusion_type": "aff_2d",
    "pre_norm": False,
    "proj_act": "gelu",
    "training_head": False,
    "pretrained": False,
    "patch_freq": 64,
    "patch_time": 4,
    "in_chans": 1,
    "patch_pad_mode": "floor",
    "rope_type": "axial",
    "naflexvit_cfg": {},
}


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _json_default(value: Any) -> str:
    return repr(value)


def _open_clip_package_dirs() -> Iterable[Path]:
    spec = importlib.util.find_spec("open_clip")
    if spec is None:
        return []
    if spec.submodule_search_locations:
        return [Path(path) for path in spec.submodule_search_locations]
    if spec.origin:
        return [Path(spec.origin).parent]
    return []


def _load_audio_config_from_json(model_name: str) -> Dict[str, Any] | None:
    for package_dir in _open_clip_package_dirs():
        config_path = package_dir / "model_configs" / f"{model_name}.json"
        if not config_path.exists():
            continue
        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        audio_cfg = config.get("audio_cfg")
        return dict(audio_cfg) if isinstance(audio_cfg, dict) else None
    return None


def _load_audio_config(model_name: str | None) -> Dict[str, Any] | None:
    if not model_name:
        return None
    import_error = None
    try:
        from open_clip import get_model_config

        config = get_model_config(model_name)
        if config is not None:
            audio_cfg = config.get("audio_cfg")
            if audio_cfg is None:
                return {"error": f"model has no audio_cfg: {model_name}"}
            return dict(audio_cfg)
    except Exception as exc:  # pragma: no cover - depends on caller environment
        import_error = str(exc)

    audio_cfg = _load_audio_config_from_json(model_name)
    if audio_cfg is not None:
        return audio_cfg
    if import_error:
        return {"error": f"could not import open_clip.get_model_config and no JSON fallback matched: {import_error}"}
    return {"error": f"unknown model config: {model_name}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Optional OpenCLIP model name whose audio_cfg should be reported.")
    parser.add_argument(
        "--check-require-audio",
        action="store_true",
        help="Call open_clip.audio.require_audio() and include its result. Does not build a model.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    dependencies = {
        "torchaudio": _module_available("torchaudio"),
        "torchlibrosa": _module_available("torchlibrosa"),
        "whisper": _module_available("whisper"),
        "datasets": _module_available("datasets"),
    }

    report: Dict[str, Any] = {
        "dependencies": dependencies,
        "audio_available": None,
        "require_audio": None,
        "clip_audio_cfg_defaults": None,
        "model": args.model,
        "model_audio_cfg": _load_audio_config(args.model),
    }

    try:
        from open_clip.audio import AUDIO_AVAILABLE, CLIPAudioCfg, require_audio

        report["audio_available"] = bool(AUDIO_AVAILABLE)
        report["clip_audio_cfg_defaults"] = asdict(CLIPAudioCfg())
        if args.check_require_audio:
            try:
                require_audio()
            except Exception as exc:  # pragma: no cover - depends on caller environment
                report["require_audio"] = {"ok": False, "error": str(exc)}
            else:
                report["require_audio"] = {"ok": True, "error": None}
    except Exception as exc:  # pragma: no cover - depends on caller environment
        report["audio_import_error"] = str(exc)
        report["clip_audio_cfg_defaults"] = dict(DEFAULT_CLIP_AUDIO_CFG)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
        return 0

    print("OpenCLIP audio dependency report")
    print("================================")
    for name, available in dependencies.items():
        print(f"{name:12} {'available' if available else 'missing'}")
    print(f"AUDIO_AVAILABLE: {report['audio_available']}")
    if report.get("require_audio") is not None:
        req = report["require_audio"]
        print(f"require_audio: {'ok' if req['ok'] else 'failed'}")
        if req["error"]:
            print(f"  {req['error']}")
    if report.get("audio_import_error"):
        print(f"audio import error: {report['audio_import_error']}")

    print("\nCLIPAudioCfg defaults")
    print("---------------------")
    defaults = report.get("clip_audio_cfg_defaults") or {}
    for key in sorted(defaults):
        print(f"{key}: {defaults[key]!r}")

    if args.model:
        print(f"\nModel audio_cfg: {args.model}")
        print("----------------" + "-" * len(args.model))
        model_cfg = report.get("model_audio_cfg")
        if isinstance(model_cfg, dict) and "error" in model_cfg:
            print(model_cfg["error"])
        elif isinstance(model_cfg, dict):
            for key in sorted(model_cfg):
                print(f"{key}: {model_cfg[key]!r}")
        else:
            print("No audio config found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
