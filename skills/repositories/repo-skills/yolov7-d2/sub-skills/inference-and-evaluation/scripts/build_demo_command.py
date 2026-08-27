#!/usr/bin/env python3
"""Build a YOLOv7-d2 demo command template."""
import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a YOLOv7-d2 demo command template.")
    parser.add_argument("--config", required=True, help="User config path.")
    parser.add_argument("--input", required=True, help="Image, directory, or glob handled by the user's demo launcher.")
    parser.add_argument("--weights", required=True, help="Checkpoint path or Detectron2 URL for MODEL.WEIGHTS.")
    parser.add_argument("--output", help="Output file or directory; recommended for headless runs.")
    parser.add_argument("--confidence", type=float, default=0.30)
    parser.add_argument("--nms", type=float, default=0.60)
    parser.add_argument("--cpu", action="store_true", help="Add MODEL.DEVICE cpu override.")
    parser.add_argument("--wandb-project")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--extra-opts", nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args()

    cmd = ["python", "demo.py", "--config-file", args.config, "--input", args.input, "-c", str(args.confidence), "-n", str(args.nms)]
    if args.output:
        cmd += ["--output", args.output]
    if args.wandb_project:
        cmd += ["--wandb-project", args.wandb_project]
    if args.wandb_entity:
        cmd += ["--wandb-entity", args.wandb_entity]
    opts = ["MODEL.WEIGHTS", args.weights]
    if args.cpu:
        opts += ["MODEL.DEVICE", "cpu"]
    opts += args.extra_opts
    cmd += ["--opts"] + opts
    print(" ".join(shlex.quote(x) for x in cmd))
    if not args.output:
        print("# Warning: no --output provided; source demo may try to open an OpenCV window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
