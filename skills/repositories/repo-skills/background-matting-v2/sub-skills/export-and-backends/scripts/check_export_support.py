#!/usr/bin/env python3
"""Smoke-test BackgroundMattingV2 export support with tiny random inputs.

Safe by default:
- requires an explicit --repo-root
- uses a tiny random model and random tensors
- optionally skips ONNX loading with --skip-onnx

Example:
    python sub-skills/export-and-backends/scripts/check_export_support.py \
      --repo-root /path/to/BackgroundMattingV2 --device cpu
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BackgroundMattingV2 export support smoke")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--model-type", choices=["mattingbase", "mattingrefine"], default="mattingrefine")
    p.add_argument("--backbone", choices=["resnet101", "resnet50", "mobilenetv2"], default="mobilenetv2")
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--height", type=int, default=64)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--opset", type=int, default=12)
    p.add_argument("--skip-onnx", action="store_true")
    p.add_argument("--keep-artifact", action="store_true")
    return p.parse_args()


def build_model(model_type: str, backbone: str):
    from model import MattingBase, MattingRefine

    if model_type == "mattingbase":
        return MattingBase(backbone)

    return MattingRefine(
        backbone,
        backbone_scale=0.25,
        refine_mode="sampling",
        refine_sample_pixels=16,
        refine_patch_crop_method="roi_align",
        refine_patch_replace_method="scatter_element",
    )


def run_smoke(args: argparse.Namespace, tmp: Path) -> int:
    import torch

    device = torch.device(args.device)
    dtype = torch.float32
    model = build_model(args.model_type, args.backbone).eval().to(device=device, dtype=dtype)
    src = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)
    bgr = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)

    try:
        with torch.no_grad():
            scripted = torch.jit.script(model)
            scripted_out = scripted(src, bgr)
    except Exception as exc:
        print(f"TorchScript smoke failed: {exc}", file=sys.stderr)
        return 5

    print(f"torch={torch.__version__}")
    print(f"scripted_output_shapes={[tuple(x.shape) for x in scripted_out]}")

    ts_path = tmp / "model.ts.pt"
    scripted.save(str(ts_path))
    reloaded = torch.jit.load(str(ts_path), map_location=device)
    with torch.no_grad():
        reloaded_out = reloaded(src, bgr)
    print(f"reloaded_output_shapes={[tuple(x.shape) for x in reloaded_out]}")

    if not args.skip_onnx:
        onnx_path = tmp / "model.onnx"
        output_names = ["pha", "fgr", "err", "hid"] if args.model_type == "mattingbase" else ["pha", "fgr", "pha_sm", "fgr_sm", "err_sm", "ref_sm"]
        input_names = ["src", "bgr"]
        try:
            torch.onnx.export(
                model,
                (src, bgr),
                str(onnx_path),
                opset_version=args.opset,
                input_names=input_names,
                output_names=output_names,
                dynamic_axes={name: {0: "batch", 2: "height", 3: "width"} for name in [*input_names, *output_names]},
            )
        except Exception as exc:
            print(f"ONNX export failed: {exc}", file=sys.stderr)
            return 6

        try:
            import onnxruntime as ort
        except Exception as exc:
            print(f"onnxruntime import failed: {exc}", file=sys.stderr)
            return 7

        try:
            sess = ort.InferenceSession(str(onnx_path))
            out = sess.run(None, {"src": src.cpu().numpy(), "bgr": bgr.cpu().numpy()})
        except Exception as exc:
            print(f"ONNX Runtime load/run failed: {exc}", file=sys.stderr)
            return 8

        print(f"onnx_output_shapes={[tuple(o.shape) for o in out]}")

    print("export support smoke passed")
    return 0


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(repo_root))

    try:
        import torch
        from model import MattingBase, MattingRefine
    except Exception as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 3

    if args.device == "cuda" and not torch.cuda.is_available():
        print("requested CUDA but torch.cuda.is_available() is false", file=sys.stderr)
        return 4

    print(f"python={sys.executable}")
    if args.keep_artifact:
        tmp = Path(tempfile.mkdtemp(prefix="bgm-v2-export-"))
        return run_smoke(args, tmp)

    with tempfile.TemporaryDirectory(prefix="bgm-v2-export-") as tmpdir:
        return run_smoke(args, Path(tmpdir))


if __name__ == "__main__":
    raise SystemExit(main())
