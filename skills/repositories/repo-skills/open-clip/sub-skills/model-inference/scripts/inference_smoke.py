#!/usr/bin/env python3
"""Safe OpenCLIP inference smoke helper.

Defaults are deterministic and no-download: random-initialized built-in model,
generated image, CPU fp32, and shape/finite assertions only. Passing a pretrained
tag or hf-hub model can trigger cache/network access and requires --allow-downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import nullcontext
from typing import Any

torch = None
Image = None
open_clip = None


def _pretrained_value(value: str | None) -> str | None:
    if value is None:
        return None
    if value.lower() in {"", "none", "null"}:
        return None
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, torch.Size):
        return list(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return list(value.shape)
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _is_download_prone(model_name: str, pretrained: str | None) -> bool:
    if model_name.startswith("hf-hub:"):
        return True
    if pretrained in (None, ""):
        return False
    if os.path.isfile(pretrained):
        return False
    return True


def _image_size_from_model(model: torch.nn.Module) -> int:
    visual = getattr(model, "visual", None)
    image_size = getattr(visual, "image_size", 224)
    if isinstance(image_size, (tuple, list)):
        return int(max(image_size))
    return int(image_size)


def _make_image(size: int) -> Image.Image:
    size = max(size, 16)
    image = Image.new("RGB", (size, size), color=(96, 128, 160))
    return image


def _summarize_output(output: Any) -> Any:
    if isinstance(output, dict):
        return {key: _jsonable(value) for key, value in output.items() if key in {
            "image_features", "text_features", "logit_scale", "logit_bias", "logits"
        }}
    if isinstance(output, tuple):
        names = ["image_features", "text_features", "logit_scale", "logit_bias"]
        return {names[index]: _jsonable(value) for index, value in enumerate(output[:len(names)])}
    return repr(type(output))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe OpenCLIP inference smoke check.")
    parser.add_argument("--model", default="ViT-B-32", help="Built-in, hf-hub:, or local-dir: model name.")
    parser.add_argument("--pretrained", default="none", help="Pretrained tag, local checkpoint file, or none.")
    parser.add_argument("--device", default="cpu", help="Torch device, for example cpu or cuda.")
    parser.add_argument("--precision", default="fp32", help="OpenCLIP precision, e.g. fp32, fp16, bf16.")
    parser.add_argument("--cache-dir", default=None, help="Optional cache directory for OpenCLIP/HF downloads.")
    parser.add_argument("--force-context-length", type=int, default=None, help="Override model/tokenizer context length.")
    parser.add_argument("--force-image-size", type=int, default=None, help="Override model image size.")
    parser.add_argument("--force-quick-gelu", action="store_true", help="Force QuickGELU in model config.")
    parser.add_argument("--force-custom-text", action="store_true", help="Force CustomTextCLIP when compatible.")
    parser.add_argument("--output-dict", action="store_true", help="Request named forward outputs when supported.")
    parser.add_argument("--load-weights", action="store_true", help="Load resolved weights for pretrained/local-dir sources.")
    parser.add_argument("--allow-downloads", action="store_true", help="Allow download-prone pretrained or hf-hub loading.")
    parser.add_argument("--list-models", action="store_true", help="Print model count and first model names, then exit.")
    parser.add_argument("--list-pretrained", action="store_true", help="Print pretrained count and first pairs, then exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    global torch, Image, open_clip
    import torch as torch_module
    from PIL import Image as image_module
    import open_clip as open_clip_module

    torch = torch_module
    Image = image_module
    open_clip = open_clip_module

    if args.list_models or args.list_pretrained:
        payload: dict[str, Any] = {}
        if args.list_models:
            models = open_clip.list_models()
            payload["model_count"] = len(models)
            payload["models_preview"] = models[:20]
        if args.list_pretrained:
            pretrained = open_clip.list_pretrained(as_str=True)
            payload["pretrained_count"] = len(pretrained)
            payload["pretrained_preview"] = pretrained[:20]
        print(json.dumps(payload, indent=2))
        return 0

    pretrained = _pretrained_value(args.pretrained)
    load_weights = bool(args.load_weights or pretrained is not None or args.model.startswith("hf-hub:"))

    if _is_download_prone(args.model, pretrained) and not args.allow_downloads:
        raise SystemExit(
            "Refusing a download-prone model/pretrained combination without --allow-downloads. "
            "Use --pretrained none for no-download smoke checks, or pass --allow-downloads intentionally."
        )

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("CUDA device requested, but torch.cuda.is_available() is false.")
    if args.device == "cpu" and args.precision in {"fp16", "pure_fp16"}:
        raise SystemExit("Use fp32 or bf16-compatible settings for CPU; fp16 CPU inference is not a safe smoke default.")

    torch.manual_seed(0)

    model, _, preprocess = open_clip.create_model_and_transforms(
        args.model,
        pretrained=pretrained,
        load_weights=load_weights,
        precision=args.precision,
        device=args.device,
        force_quick_gelu=args.force_quick_gelu,
        force_custom_text=args.force_custom_text,
        force_image_size=args.force_image_size,
        force_context_length=args.force_context_length,
        cache_dir=args.cache_dir,
        output_dict=args.output_dict,
    )
    model.eval()

    tokenizer = open_clip.get_tokenizer(
        args.model,
        context_length=args.force_context_length,
        cache_dir=args.cache_dir,
    )

    image_size = args.force_image_size or _image_size_from_model(model)
    image = _make_image(image_size)
    image_tensor = preprocess(image).unsqueeze(0).to(args.device)
    text_tokens = tokenizer(["a synthetic image", "a simple shape"]).to(args.device)

    autocast_context = torch.autocast("cuda") if args.device.startswith("cuda") and args.precision in {"fp16", "bf16"} else nullcontext()
    with torch.no_grad(), autocast_context:
        image_features = model.encode_image(image_tensor, normalize=True)
        text_features = model.encode_text(text_tokens, normalize=True)
        logits = image_features @ text_features.T
        forward_output = model(image=image_tensor, text=text_tokens)

    checks = {
        "image_features_shape": list(image_features.shape),
        "text_features_shape": list(text_features.shape),
        "logits_shape": list(logits.shape),
        "image_features_finite": bool(torch.isfinite(image_features).all().item()),
        "text_features_finite": bool(torch.isfinite(text_features).all().item()),
        "logits_finite": bool(torch.isfinite(logits).all().item()),
        "model_training": bool(model.training),
        "forward_summary": _summarize_output(forward_output),
    }

    assert checks["image_features_shape"][0] == 1, checks
    assert checks["text_features_shape"][0] == 2, checks
    assert checks["logits_shape"] == [1, 2], checks
    assert checks["image_features_finite"], checks
    assert checks["text_features_finite"], checks
    assert checks["logits_finite"], checks
    assert checks["model_training"] is False, checks

    payload = {
        "ok": True,
        "model": args.model,
        "pretrained": pretrained,
        "load_weights": load_weights,
        "device": args.device,
        "precision": args.precision,
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, default=_jsonable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
