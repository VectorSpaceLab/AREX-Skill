#!/usr/bin/env python3
"""Safe DALLE-pytorch install/API smoke check.

This script avoids model downloads and long training. It validates import,
public signatures, a tiny CPU API path, and optional CUDA availability.
"""
import argparse
import inspect
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DALLE-pytorch import and tiny API behavior.")
    parser.add_argument("--include-cuda", action="store_true", help="Report and allocate one tiny CUDA tensor if CUDA is available.")
    parser.add_argument("--skip-smoke", action="store_true", help="Only inspect imports/signatures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines.")
    args = parser.parse_args()

    report = {"ok": False, "imports": {}, "signatures": {}, "smokes": [], "warnings": []}
    try:
        import torch
        import dalle_pytorch
        from dalle_pytorch import CLIP, DALLE, DiscreteVAE, OpenAIDiscreteVAE, VQGanVAE
        from dalle_pytorch.loader import TextImageDataset
        from dalle_pytorch.tokenizer import tokenizer
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(report, indent=2) if args.json else report["error"])
        return 1

    report["imports"] = {
        "dalle_pytorch_version": getattr(dalle_pytorch, "__version__", "unknown"),
        "torch_version": getattr(torch, "__version__", "unknown"),
        "torch_cuda": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
        "OpenAIDiscreteVAE_class_imported": OpenAIDiscreteVAE.__name__,
        "VQGanVAE_class_imported": VQGanVAE.__name__,
    }
    for obj in (DiscreteVAE, DALLE, CLIP, TextImageDataset, tokenizer.tokenize, tokenizer.decode):
        name = f"{getattr(obj, '__module__', '')}.{getattr(obj, '__name__', obj.__class__.__name__)}"
        report["signatures"][name] = str(inspect.signature(obj))

    if not args.skip_smoke:
        vae = DiscreteVAE(image_size=8, num_tokens=16, codebook_dim=8, num_layers=1, hidden_dim=8)
        images = torch.randn(2, 3, 8, 8)
        loss, recons = vae(images, return_loss=True, return_recons=True)
        assert recons.shape == images.shape
        assert torch.isfinite(loss)
        indices = vae.get_codebook_indices(images)
        assert indices.shape == (2, 16)
        report["smokes"].append("DiscreteVAE tiny CPU loss/reconstruction/codebook passed")

        dalle = DALLE(dim=32, vae=vae, num_text_tokens=32, text_seq_len=4, depth=1, heads=2, dim_head=16, rotary_emb=False)
        text = torch.randint(1, 16, (2, 4))
        dalle_loss = dalle(text, images, return_loss=True)
        assert torch.isfinite(dalle_loss)
        gen = dalle.generate_images(text[:1], filter_thres=0.9)
        assert gen.shape == (1, 3, 8, 8)
        report["smokes"].append("DALLE tiny CPU loss/generate_images passed")

        clip = CLIP(dim_text=16, dim_image=16, dim_latent=8, num_text_tokens=32, text_enc_depth=1, text_seq_len=4, text_heads=2, num_visual_tokens=16, visual_enc_depth=1, visual_heads=2, visual_image_size=8, visual_patch_size=4)
        clip_loss = clip(text, images, return_loss=True)
        assert torch.isfinite(clip_loss)
        report["smokes"].append("CLIP tiny CPU loss passed")

        toks = tokenizer.tokenize(["hello world"], 8)
        assert tuple(toks.shape) == (1, 8)
        report["smokes"].append("default tokenizer tokenize passed")

    if args.include_cuda:
        try:
            import torch
            if torch.cuda.is_available():
                x = torch.empty((1,), device="cuda")
                report["smokes"].append(f"CUDA allocation passed on {torch.cuda.get_device_name(0)}: {x.device}")
            else:
                report["warnings"].append("CUDA requested but torch.cuda.is_available() is false")
        except Exception as exc:  # pragma: no cover
            report["warnings"].append(f"CUDA smoke failed: {type(exc).__name__}: {exc}")

    report["warnings"].append("OpenAIDiscreteVAE constructor may require torch <= 1.10 and may download weights; not instantiated here.")
    report["ok"] = True
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DALLE-pytorch check passed")
        for key, value in report["imports"].items():
            print(f"{key}: {value}")
        for smoke in report["smokes"]:
            print(f"OK: {smoke}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
