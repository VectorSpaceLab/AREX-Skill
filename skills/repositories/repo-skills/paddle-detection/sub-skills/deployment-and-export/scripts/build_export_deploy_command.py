#!/usr/bin/env python3
"""Build PaddleDetection export/deploy commands without executing them."""

from __future__ import annotations

import argparse
import shlex


def q(parts):
    return " ".join(shlex.quote(str(p)) for p in parts if p is not None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print PaddleDetection export or deploy command.")
    sub = parser.add_subparsers(dest="mode", required=True)

    exp = sub.add_parser("export")
    exp.add_argument("--config", required=True)
    exp.add_argument("--weights", required=True)
    exp.add_argument("--output-dir", default="output_inference")
    exp.add_argument("--gpu", action="store_true")
    exp.add_argument("--serving", action="store_true")
    exp.add_argument("--for-fd", action="store_true")
    exp.add_argument("--slim-config")
    exp.add_argument("-o", "--opt", action="append", default=[])

    inf = sub.add_parser("python-infer")
    inf.add_argument("--model-dir", required=True)
    src = inf.add_mutually_exclusive_group(required=True)
    src.add_argument("--image-file")
    src.add_argument("--image-dir")
    src.add_argument("--video-file")
    inf.add_argument("--device", default="CPU")
    inf.add_argument("--run-mode", default="paddle")
    inf.add_argument("--threshold", default="0.5")
    inf.add_argument("--output-dir", default="output")
    inf.add_argument("--benchmark", action="store_true")

    args = parser.parse_args()
    if args.mode == "export":
        opts = list(args.opt) + [f"weights={args.weights}", f"use_gpu={'true' if args.gpu else 'false'}"]
        cmd = ["python", "tools/export_model.py", "-c", args.config, "--output_dir", args.output_dir, "-o", *opts]
        if args.serving:
            cmd.extend(["--export_serving_model", "True"])
        if args.for_fd:
            cmd.append("--for_fd")
        if args.slim_config:
            cmd.extend(["--slim_config", args.slim_config])
    else:
        cmd = ["python", "deploy/python/infer.py", "--model_dir", args.model_dir, "--device", args.device, "--run_mode", args.run_mode, "--threshold", args.threshold, "--output_dir", args.output_dir]
        if args.image_file:
            cmd.extend(["--image_file", args.image_file])
        if args.image_dir:
            cmd.extend(["--image_dir", args.image_dir])
        if args.video_file:
            cmd.extend(["--video_file", args.video_file])
        if args.benchmark:
            cmd.extend(["--run_benchmark", "True"])
    print("# Run from the target PaddleDetection checkout root:")
    print(q(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
