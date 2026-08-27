#!/usr/bin/env python3
"""Smoke-check align-anything serving model loading.

This bundled helper intentionally imports the installed align_anything package and
never reads the source checkout. Use --no-load for dependency/argument checks,
then run a real load with a tiny or cached target model before launching Gradio.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import traceback
from typing import Any


PRESETS: dict[str, dict[str, Any]] = {
    "text": {
        "dtype": "float16",
        "trust_remote_code": True,
        "auto_device_mapping": False,
        "modality": [],
    },
    "multi-image": {
        "dtype": "float16",
        "auto_device_mapping": True,
        "modality": ["image"],
    },
    "multi-audio": {
        "dtype": "float16",
        "auto_device_mapping": True,
        "modality": ["audio"],
    },
    "multi-video": {
        "dtype": "float16",
        "auto_device_mapping": True,
        "modality": ["video"],
    },
    "omni": {
        "dtype": "float16",
        "trust_remote_code": True,
        "auto_device_mapping": False,
        "modality": ["image", "audio"],
        "auto_model_kwargs": {"init_vision": True, "init_audio": True, "init_tts": True},
    },
    "reward": {
        "dtype": "float16",
        "is_reward_model": True,
        "auto_device_mapping": False,
        "modality": [],
    },
}


def parse_value(raw: str) -> Any:
    """Parse a CLI value as JSON/Python literal, falling back to a string."""
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(raw)
        except Exception:
            pass
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.lower() == "none" or raw.lower() == "null":
        return None
    return raw


def parse_kv(items: list[str] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"Expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise argparse.ArgumentTypeError(f"Empty key in {item!r}")
        parsed[key] = parse_value(value.strip())
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check align-anything load_pretrained_models for serving.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model-name-or-path", required=True, help="HF model id or local model path")
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Apply serving-oriented defaults")
    parser.add_argument("--cache-dir", help="Optional Transformers cache directory")
    parser.add_argument("--model-max-length", type=int, default=2048)
    parser.add_argument("--padding-side", choices=["left", "right"], default="right")
    parser.add_argument(
        "--dtype",
        choices=["auto", "bfloat16", "float16", "float32"],
        help="torch dtype to pass; omit for align-anything loader default",
    )

    trust = parser.add_mutually_exclusive_group()
    trust.add_argument("--trust-remote-code", dest="trust_remote_code", action="store_true")
    trust.add_argument("--no-trust-remote-code", dest="trust_remote_code", action="store_false")
    parser.set_defaults(trust_remote_code=None)

    adm = parser.add_mutually_exclusive_group()
    adm.add_argument("--auto-device-mapping", dest="auto_device_mapping", action="store_true")
    adm.add_argument("--no-auto-device-mapping", dest="auto_device_mapping", action="store_false")
    parser.set_defaults(auto_device_mapping=None)

    parser.add_argument("--is-reward-model", action="store_true")
    parser.add_argument(
        "--modality",
        action="append",
        choices=["text", "image", "audio", "video"],
        help="Append a modality hint; repeat for omni/remote-code models",
    )
    parser.add_argument(
        "--auto-model-kw",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra model kwarg; VALUE may be JSON/Python literal",
    )
    parser.add_argument(
        "--auto-tokenizer-kw",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra tokenizer kwarg; VALUE may be JSON/Python literal",
    )
    parser.add_argument(
        "--processor-kw",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra processor kwarg; VALUE may be JSON/Python literal",
    )
    parser.add_argument("--zero-stage", help="Set ZERO_STAGE before loading; default is 0 if unset")
    parser.add_argument("--local-rank", help="Set LOCAL_RANK before device selection")
    parser.add_argument("--force-cpu", action="store_true", help="Hide CUDA devices before importing torch")
    parser.add_argument("--no-load", action="store_true", help="Import modules and print the load plan only")
    parser.add_argument(
        "--move-to-current-device",
        action="store_true",
        help="After loading, call model.eval().to(get_current_device()); avoid with device_map='auto'",
    )
    parser.add_argument(
        "--chat-prompt",
        help="Optional text prompt for model.chat(messages=[...], tokenizer=tokenizer)",
    )
    parser.add_argument("--verbose", action="store_true", help="Print full traceback on failure")
    return parser


def apply_preset(args: argparse.Namespace) -> None:
    if not args.preset:
        return
    preset = PRESETS[args.preset]
    if args.dtype is None and "dtype" in preset:
        args.dtype = preset["dtype"]
    if args.trust_remote_code is None and "trust_remote_code" in preset:
        args.trust_remote_code = preset["trust_remote_code"]
    if args.auto_device_mapping is None and "auto_device_mapping" in preset:
        args.auto_device_mapping = preset["auto_device_mapping"]
    if not args.is_reward_model and preset.get("is_reward_model"):
        args.is_reward_model = True
    if not args.modality and "modality" in preset:
        args.modality = list(preset["modality"])


def resolve_dtype(torch_module: Any, dtype_name: str | None) -> Any:
    if dtype_name is None:
        return None
    if dtype_name == "auto":
        return None
    return {
        "bfloat16": torch_module.bfloat16,
        "float16": torch_module.float16,
        "float32": torch_module.float32,
    }[dtype_name]


def summarize_exception(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    lowered = text.lower()
    tips: list[str] = []
    if "librosa" in lowered:
        tips.append("Install/repair audio runtime dependencies; align-anything imports may need librosa.")
    if "gradio" in lowered:
        tips.append("Install/repair gradio before launching serving CLIs.")
    if "trust_remote_code" in lowered:
        tips.append("Use --trust-remote-code only for trusted model repositories.")
    if "zero_stage" in lowered:
        tips.append("Set --zero-stage 0 for ordinary MiniCPM serving checks.")
    if "cuda out of memory" in lowered or "outofmemory" in lowered:
        tips.append("Try --auto-device-mapping, a smaller model, or a lower-memory dtype.")
    if "av" in lowered or "ffmpeg" in lowered:
        tips.append("Install PyAV/FFmpeg or re-encode video media.")
    if tips:
        return text + "\nHints:\n- " + "\n- ".join(tips)
    return text


def main() -> int:
    args = build_parser().parse_args()
    apply_preset(args)

    if args.force_cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    if args.local_rank is not None:
        os.environ["LOCAL_RANK"] = str(args.local_rank)
    if args.zero_stage is not None:
        os.environ["ZERO_STAGE"] = str(args.zero_stage)
    else:
        os.environ.setdefault("ZERO_STAGE", "0")

    # Remote-code wrappers such as MiniCPM-V/O read this environment variable.
    os.environ["MODEL_NAME_OR_PATH"] = args.model_name_or_path

    auto_model_kwargs = dict(PRESETS.get(args.preset or "", {}).get("auto_model_kwargs", {}))
    auto_model_kwargs.update(parse_kv(args.auto_model_kw))
    auto_tokenizer_kwargs = parse_kv(args.auto_tokenizer_kw)
    processor_kwargs = parse_kv(args.processor_kw)

    plan = {
        "model_name_or_path": args.model_name_or_path,
        "preset": args.preset,
        "cache_dir": args.cache_dir,
        "model_max_length": args.model_max_length,
        "padding_side": args.padding_side,
        "dtype": args.dtype or "loader-default",
        "trust_remote_code": args.trust_remote_code if args.trust_remote_code is not None else "loader-default",
        "auto_device_mapping": args.auto_device_mapping if args.auto_device_mapping is not None else "loader-default",
        "is_reward_model": args.is_reward_model,
        "modality": args.modality or [],
        "auto_model_kwargs": auto_model_kwargs,
        "auto_tokenizer_kwargs": auto_tokenizer_kwargs,
        "processor_kwargs": processor_kwargs,
        "force_cpu": args.force_cpu,
    }
    print("[align-anything] load plan:")
    print(json.dumps(plan, indent=2, sort_keys=True, default=str))

    try:
        import torch
        from align_anything.models.pretrained_model import load_pretrained_models
        from align_anything.utils.device_utils import get_current_device, get_device_count
    except Exception as exc:  # pragma: no cover - depends on user env
        print("[align-anything] import check failed", file=sys.stderr)
        print(summarize_exception(exc), file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2

    print(
        "[align-anything] imports ok; torch="
        f"{getattr(torch, '__version__', 'unknown')} device={get_current_device()} "
        f"device_count={get_device_count()}"
    )

    if args.no_load:
        print("[align-anything] --no-load requested; stopping before weight download/model construction.")
        return 0

    dtype = resolve_dtype(torch, args.dtype)
    load_kwargs: dict[str, Any] = {
        "model_name_or_path": args.model_name_or_path,
        "model_max_length": args.model_max_length,
        "padding_side": args.padding_side,
        "cache_dir": args.cache_dir,
        "auto_model_kwargs": auto_model_kwargs,
        "auto_tokenizer_kwargs": auto_tokenizer_kwargs,
        "processor_kwargs": processor_kwargs,
        "is_reward_model": args.is_reward_model,
        "modality": args.modality or [],
    }
    if args.dtype is not None:
        # dtype=None is meaningful: it asks Transformers/model code to choose instead of
        # using align-anything's loader default of bfloat16.
        load_kwargs["dtype"] = dtype
    if args.trust_remote_code is not None:
        load_kwargs["trust_remote_code"] = args.trust_remote_code
    if args.auto_device_mapping is not None:
        load_kwargs["auto_device_mapping"] = args.auto_device_mapping

    try:
        model, tokenizer, processor = load_pretrained_models(**load_kwargs)
    except Exception as exc:  # pragma: no cover - depends on model/env
        print("[align-anything] model load failed", file=sys.stderr)
        print(summarize_exception(exc), file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 3

    print("[align-anything] model load ok")
    print(f"  model_class={model.__class__.__module__}.{model.__class__.__name__}")
    config = getattr(model, "config", None)
    print(f"  model_type={getattr(config, 'model_type', None)}")
    print(f"  tokenizer_class={tokenizer.__class__.__module__}.{tokenizer.__class__.__name__}")
    print(
        "  processor_class="
        + ("None" if processor is None else f"{processor.__class__.__module__}.{processor.__class__.__name__}")
    )
    print(f"  processor_available={getattr(model, 'processor_available', 'unknown')}")
    try:
        first_param = next(model.parameters())
        print(f"  first_param_device={first_param.device} first_param_dtype={first_param.dtype}")
    except Exception:
        print("  first_param_device=unavailable first_param_dtype=unavailable")

    if args.move_to_current_device:
        if args.auto_device_mapping:
            print("[align-anything] warning: moving a device_map='auto' model can break sharding")
        try:
            device = get_current_device()
            model = model.eval().to(device)
            print(f"[align-anything] moved model to {device}")
        except Exception as exc:  # pragma: no cover - depends on backend
            print("[align-anything] move-to-device failed", file=sys.stderr)
            print(summarize_exception(exc), file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
            return 4

    if args.chat_prompt:
        if not hasattr(model, "chat"):
            print("[align-anything] model has no chat(...) method; skipping prompt", file=sys.stderr)
            return 5
        messages = [{"role": "user", "content": args.chat_prompt}]
        try:
            with torch.no_grad():
                response = model.chat(messages=messages, tokenizer=tokenizer)
            print("[align-anything] chat response:")
            print(response)
        except Exception as exc:  # pragma: no cover - depends on model/env
            print("[align-anything] chat smoke failed", file=sys.stderr)
            print(summarize_exception(exc), file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
            return 6

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
