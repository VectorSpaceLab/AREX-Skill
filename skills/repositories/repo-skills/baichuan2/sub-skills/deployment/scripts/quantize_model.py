#!/usr/bin/env python3
"""Safe Baichuan2 quantization helper.

The helper mirrors the documented Baichuan2 deployment routes while making the
selected route explicit. Use --dry-run to validate choices without loading model
weights.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Tuple


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or run Baichuan2 4-bit/8-bit quantization workflows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("online", "offline-8bit", "load-prequantized-4bit"),
        default="online",
        help="Quantization/deployment route to use.",
    )
    parser.add_argument(
        "--bits",
        type=int,
        choices=(4, 8),
        default=4,
        help="Bit width for online quantization. Ignored by other modes.",
    )
    parser.add_argument(
        "--model-id",
        default="baichuan-inc/Baichuan2-7B-Chat",
        help="Local model directory or Hugging Face model id.",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Output directory for offline 8-bit saving or optional online save_pretrained.",
    )
    parser.add_argument(
        "--torch-dtype",
        choices=("float16", "bfloat16", "float32"),
        default="float16",
        help="Torch dtype for online model loading.",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Target device for online quantization after model.quantize(...).",
    )
    parser.add_argument(
        "--trust-remote-code",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pass trust_remote_code to Transformers model loading.",
    )
    parser.add_argument(
        "--use-legacy-load-in-8bit",
        action="store_true",
        help="Use load_in_8bit=True instead of BitsAndBytesConfig for offline 8-bit mode.",
    )
    parser.add_argument(
        "--skip-reload-check",
        action="store_true",
        help="After saving offline 8-bit weights, skip reload of the saved directory.",
    )
    parser.add_argument(
        "--validate-imports",
        action="store_true",
        help="Import torch, transformers, and bitsandbytes before running or as part of dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the execution plan and perform optional import checks without loading weights.",
    )
    return parser


def _package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def _import_runtime(require_bnb: bool = True) -> Tuple[Any, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on host env
        raise SystemExit(f"Torch import failed: {exc}") from exc

    try:
        from transformers import AutoModelForCausalLM
    except Exception as exc:  # pragma: no cover - depends on host env
        raise SystemExit(f"Transformers import failed: {exc}") from exc

    if require_bnb:
        try:
            import bitsandbytes  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on host env
            raise SystemExit(
                "bitsandbytes import failed. Install a CUDA-compatible "
                f"bitsandbytes build before quantizing Baichuan2: {exc}"
            ) from exc

    return torch, AutoModelForCausalLM


def _torch_dtype(torch: Any, dtype_name: str) -> Any:
    return {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[dtype_name]


def _plan(args: argparse.Namespace) -> Dict[str, Any]:
    warnings = []
    if args.mode == "online":
        warnings.append(
            "Online quantization intentionally does not pass device_map='auto'; "
            "the model is loaded on CPU, quantized, then moved to CUDA."
        )
        if args.save_dir:
            warnings.append(
                "Saving an online-quantized model is optional and may depend on "
                "the remote model implementation. Offline 8-bit mode is the "
                "documented save/reload path."
            )
    elif args.mode == "offline-8bit":
        if args.bits != 8:
            warnings.append("--bits is ignored in offline-8bit mode.")
        if not args.save_dir:
            warnings.append("offline-8bit mode requires --save-dir for a real run.")
    elif args.mode == "load-prequantized-4bit":
        if args.bits != 4:
            warnings.append("--bits is ignored in load-prequantized-4bit mode.")
        if "4bit" not in args.model_id.lower() and "4bits" not in args.model_id.lower():
            warnings.append(
                "The model id does not look like a published 4-bit checkpoint; "
                "confirm it is already quantized before using this mode."
            )

    return {
        "mode": args.mode,
        "bits": args.bits if args.mode == "online" else None,
        "model_id": args.model_id,
        "save_dir": str(args.save_dir) if args.save_dir else None,
        "torch_dtype": args.torch_dtype if args.mode == "online" else None,
        "target_device": args.device if args.mode == "online" else None,
        "trust_remote_code": args.trust_remote_code,
        "uses_device_map_auto": args.mode in {"offline-8bit", "load-prequantized-4bit"},
        "warnings": warnings,
    }


def _validate_imports_for_plan(args: argparse.Namespace) -> Dict[str, Any]:
    torch, _ = _import_runtime(require_bnb=True)
    cuda_available = bool(torch.cuda.is_available())
    cuda_device_count = int(torch.cuda.device_count()) if cuda_available else 0
    return {
        "torch": getattr(torch, "__version__", _package_version("torch")),
        "torch_cuda": getattr(torch.version, "cuda", None),
        "transformers": _package_version("transformers"),
        "bitsandbytes": _package_version("bitsandbytes"),
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_device_count,
    }


def _require_cuda(torch: Any, device: str) -> None:
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit(
            "CUDA is not available, but Baichuan2 quantization modes in this "
            "helper require CUDA. Use the CPU deployment recipe instead of "
            "BitsAndBytes quantization on this host."
        )


def _load_offline_8bit_model(
    AutoModelForCausalLM: Any, args: argparse.Namespace
) -> Any:
    kwargs: Dict[str, Any] = {
        "device_map": "auto",
        "trust_remote_code": args.trust_remote_code,
    }

    if args.use_legacy_load_in_8bit:
        kwargs["load_in_8bit"] = True
    else:
        try:
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        except Exception:
            kwargs["load_in_8bit"] = True

    return AutoModelForCausalLM.from_pretrained(args.model_id, **kwargs)


def _run_online(args: argparse.Namespace) -> None:
    torch, AutoModelForCausalLM = _import_runtime(require_bnb=True)
    _require_cuda(torch, args.device)

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=_torch_dtype(torch, args.torch_dtype),
        trust_remote_code=args.trust_remote_code,
    )
    if not hasattr(model, "quantize"):
        raise SystemExit(
            "Loaded model does not expose model.quantize(...). Confirm that "
            "trust_remote_code is enabled and that the checkpoint is a "
            "Baichuan2 implementation with the quantize method."
        )

    model = model.quantize(args.bits)
    if args.device == "cuda":
        model = model.cuda()
    else:
        model = model.to(args.device)

    print(f"Online {args.bits}-bit quantization complete on {args.device}.")
    if args.save_dir:
        args.save_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(args.save_dir)
        print(f"Saved model to {args.save_dir}")


def _run_offline_8bit(args: argparse.Namespace) -> None:
    if not args.save_dir:
        raise SystemExit("offline-8bit mode requires --save-dir.")

    torch, AutoModelForCausalLM = _import_runtime(require_bnb=True)
    _require_cuda(torch, "cuda")

    model = _load_offline_8bit_model(AutoModelForCausalLM, args)
    args.save_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.save_dir)
    print(f"Saved 8-bit quantized model to {args.save_dir}")

    if not args.skip_reload_check:
        _ = AutoModelForCausalLM.from_pretrained(
            args.save_dir,
            device_map="auto",
            trust_remote_code=args.trust_remote_code,
        )
        print("Reload check from saved 8-bit directory succeeded.")


def _run_load_prequantized_4bit(args: argparse.Namespace) -> None:
    torch, AutoModelForCausalLM = _import_runtime(require_bnb=True)
    _require_cuda(torch, "cuda")
    _ = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        device_map="auto",
        trust_remote_code=args.trust_remote_code,
    )
    print(f"Loaded pre-quantized 4-bit model: {args.model_id}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    plan = _plan(args)
    if args.validate_imports:
        plan["import_validation"] = _validate_imports_for_plan(args)

    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    for warning in plan.get("warnings", []):
        print(f"warning: {warning}", file=sys.stderr)

    if args.mode == "online":
        _run_online(args)
    elif args.mode == "offline-8bit":
        _run_offline_8bit(args)
    elif args.mode == "load-prequantized-4bit":
        _run_load_prequantized_4bit(args)
    else:  # pragma: no cover - argparse prevents this
        raise SystemExit(f"Unsupported mode: {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
