#!/usr/bin/env python3
"""Export YOLOP to ONNX with explicit paths and the source export wrapper.

Example:
  python export_onnx_model.py --repo-root /path/to/YOLOP \
    --checkpoint /path/to/YOLOP/weights/End-to-end.pth \
    --output /tmp/yolop-640-640.onnx --height 640 --width 640 --simplify --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export YOLOP checkpoint to ONNX")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout")
    parser.add_argument("--checkpoint", help="YOLOP .pth checkpoint; omit only with --random-init")
    parser.add_argument("--output", required=True, help="ONNX output path")
    parser.add_argument("--height", type=int, default=640, help="Input height")
    parser.add_argument("--width", type=int, default=640, help="Input width")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, ...")
    parser.add_argument("--random-init", action="store_true", help="Export randomly initialized weights for dependency smoke")
    parser.add_argument("--simplify", action="store_true", help="Run onnxsim.simplify after export")
    parser.add_argument("--check", action="store_true", help="Run onnx checker and ONNXRuntime session inspection")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "export_onnx.py").is_file():
        print(f"ERROR: not a YOLOP checkout with export_onnx.py: {repo_root}", file=sys.stderr)
        return 2
    if args.height <= 0 or args.width <= 0 or args.height % 32 != 0 or args.width % 32 != 0:
        print("ERROR: --height and --width must be positive multiples of 32", file=sys.stderr)
        return 3
    if not args.random_init and not args.checkpoint:
        print("ERROR: pass --checkpoint or --random-init", file=sys.stderr)
        return 4
    sys.path.insert(0, str(repo_root))

    import torch
    import onnx
    from export_onnx import MCnet, YOLOP

    if args.device != "cpu" and args.device.startswith("cuda") and not torch.cuda.is_available():
        print("ERROR: CUDA requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 5
    device = torch.device(args.device)
    model = MCnet(YOLOP).to(device).eval()

    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint).expanduser().resolve()
        if not checkpoint_path.is_file():
            print(f"ERROR: checkpoint not found: {checkpoint_path}", file=sys.stderr)
            return 6
        checkpoint = torch.load(str(checkpoint_path), map_location=device)
        state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
        model.load_state_dict(state_dict)

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    inputs = torch.randn(1, 3, args.height, args.width, device=device)
    torch.onnx.export(
        model,
        inputs,
        str(output_path),
        verbose=False,
        opset_version=args.opset,
        input_names=["images"],
        output_names=["det_out", "drive_area_seg", "lane_line_seg"],
    )
    print(f"exported={output_path}")

    model_onnx = onnx.load(str(output_path))
    if args.check:
        onnx.checker.check_model(model_onnx)
        print("onnx_checker=passed")
    if args.simplify:
        import onnxsim

        model_onnx, ok = onnxsim.simplify(model_onnx, check_n=1)
        if not ok:
            print("ERROR: onnxsim.simplify returned false", file=sys.stderr)
            return 7
        onnx.save(model_onnx, str(output_path))
        print("onnx_simplify=passed")
    if args.check:
        import onnxruntime as ort

        sess = ort.InferenceSession(str(output_path), providers=["CPUExecutionProvider"])
        outputs = [(o.name, o.shape) for o in sess.get_outputs()]
        print(f"onnx_inputs={[(i.name, i.shape) for i in sess.get_inputs()]}")
        print(f"onnx_outputs={outputs}")
        expected = ["det_out", "drive_area_seg", "lane_line_seg"]
        names = [name for name, _ in outputs]
        if names[:3] != expected:
            print(f"ERROR: first outputs are {names[:3]}, expected {expected}", file=sys.stderr)
            return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
