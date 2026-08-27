#!/usr/bin/env python3
"""Print DragGAN/StyleGAN generation commands without running model inference."""
from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def quote(cmd):
    return " ".join(shlex.quote(str(part)) for part in cmd if part is not None)


def add_common_model_args(parser):
    parser.add_argument("--network", required=True, help="Network pickle path or URL.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument("--trunc", default=None, help="Truncation psi.")
    parser.add_argument("--noise-mode", choices=["const", "random", "none"], default=None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build copyable DragGAN/StyleGAN CLI commands.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Local DragGAN checkout used in the printed command.")
    sub = parser.add_subparsers(dest="workflow", required=True)

    gen = sub.add_parser("gen-images", help="Top-level gen_images.py command.")
    add_common_model_args(gen)
    gen.add_argument("--seeds", required=True, help="Comma/range seeds, e.g. 1,2,5-10.")
    gen.add_argument("--class-idx", help="Class label for conditional networks.")
    gen.add_argument("--translate", help="XY translation, e.g. 0.3,1.")
    gen.add_argument("--rotate", help="Rotation angle in degrees.")

    human = sub.add_parser("stylegan-human-generate", help="StyleGAN-Human generate.py command.")
    add_common_model_args(human)
    human.add_argument("--seeds", required=True)
    human.add_argument("--version", choices=["1", "2", "3"], default="2")

    interp = sub.add_parser("interpolation", help="StyleGAN-Human interpolation.py command.")
    add_common_model_args(interp)
    interp.add_argument("--seeds", required=True, help="Two seeds such as 85,100.")
    interp.add_argument("--fps", type=int)
    interp.add_argument("--num-interps", type=int)
    interp.add_argument("--save-mid-image", choices=["True", "False"])

    mix = sub.add_parser("style-mixing", help="StyleGAN-Human style_mixing.py command.")
    add_common_model_args(mix)
    mix.add_argument("--rows", required=True)
    mix.add_argument("--cols", required=True)
    mix.add_argument("--styles", default=None)

    video = sub.add_parser("stylemixing-video", help="StyleGAN-Human stylemixing_video.py command; TensorFlow-style imports may be required.")
    video.add_argument("--network", required=True)
    video.add_argument("--row-seed", required=True)
    video.add_argument("--col-seeds", required=True)
    video.add_argument("--col-styles", default=None)
    video.add_argument("--trunc", default=None)
    video.add_argument("--duration-sec", type=float)
    video.add_argument("--fps", type=int)
    video.add_argument("--outdir", required=True)

    conv = sub.add_parser("legacy-convert", help="legacy.py pickle conversion command.")
    conv.add_argument("--source", required=True)
    conv.add_argument("--dest", required=True)
    conv.add_argument("--force-fp16", choices=["True", "False"])

    args = parser.parse_args()
    repo_root = args.repo_root

    if args.workflow == "gen-images":
        cmd = ["python", str(repo_root / "gen_images.py"), "--network", args.network, "--seeds", args.seeds, "--outdir", args.outdir]
        if args.trunc: cmd += ["--trunc", args.trunc]
        if args.noise_mode: cmd += ["--noise-mode", args.noise_mode]
        if args.class_idx: cmd += ["--class", args.class_idx]
        if args.translate: cmd += ["--translate", args.translate]
        if args.rotate: cmd += ["--rotate", args.rotate]
    elif args.workflow == "stylegan-human-generate":
        cmd = ["python", str(repo_root / "stylegan_human" / "generate.py"), "--network", args.network, "--seeds", args.seeds, "--outdir", args.outdir, "--version", args.version]
        if args.trunc: cmd += ["--trunc", args.trunc]
        if args.noise_mode: cmd += ["--noise-mode", args.noise_mode]
    elif args.workflow == "interpolation":
        cmd = ["python", str(repo_root / "stylegan_human" / "interpolation.py"), "--network", args.network, "--seeds", args.seeds, "--outdir", args.outdir]
        if args.trunc: cmd += ["--trunc", args.trunc]
        if args.noise_mode: cmd += ["--noise-mode", args.noise_mode]
        if args.fps is not None: cmd += ["--fps", args.fps]
        if args.num_interps is not None: cmd += ["--num_interps", args.num_interps]
        if args.save_mid_image is not None: cmd += ["--save_mid_image", args.save_mid_image]
    elif args.workflow == "style-mixing":
        cmd = ["python", str(repo_root / "stylegan_human" / "style_mixing.py"), "--network", args.network, "--rows", args.rows, "--cols", args.cols, "--outdir", args.outdir]
        if args.styles: cmd += ["--styles", args.styles]
        if args.trunc: cmd += ["--trunc", args.trunc]
        if args.noise_mode: cmd += ["--noise-mode", args.noise_mode]
    elif args.workflow == "stylemixing-video":
        cmd = ["python", str(repo_root / "stylegan_human" / "stylemixing_video.py"), "--network", args.network, "--row-seed", args.row_seed, "--col-seeds", args.col_seeds, "--outdir", args.outdir]
        if args.col_styles: cmd += ["--col-styles", args.col_styles]
        if args.trunc: cmd += ["--trunc", args.trunc]
        if args.duration_sec is not None: cmd += ["--duration-sec", args.duration_sec]
        if args.fps is not None: cmd += ["--fps", args.fps]
    elif args.workflow == "legacy-convert":
        cmd = ["python", str(repo_root / "legacy.py"), "--source", args.source, "--dest", args.dest]
        if args.force_fp16: cmd += ["--force-fp16", args.force_fp16]
    else:  # pragma: no cover
        raise AssertionError(args.workflow)

    print(quote(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
