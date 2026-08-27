#!/usr/bin/env python3
"""Build a VGen text-to-video UNet and run a tiny forward smoke.

This helper is meant to replace the repo's ad-hoc model smoke path with a
self-contained script that can be called from a generated skill tree. It
focuses on the standard text-to-video family and reports optional complexity
packages separately instead of failing with a raw traceback.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a VGen text-to-video UNet and run a forward smoke.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        default="configs/t2v_train.yaml",
        help="YAML config used to build the VGen model family.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path('.'),
        help="VGen checkout root used to import the package and resolve config paths.",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda",
        help="Device used for the smoke forward.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Synthetic batch size.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=16,
        help="Synthetic frame count.",
    )
    parser.add_argument(
        "--skip-forward",
        action="store_true",
        help="Only build the model and print parameter counts; do not run the dummy forward.",
    )
    parser.add_argument(
        "--check-flops",
        action="store_true",
        help="If thop/ptflops are installed, also print a rough FLOP/parameter report.",
    )
    return parser.parse_args(argv)


def load_config(repo_root: Path, config_path: Path):
    repo_root = repo_root.resolve()
    config_path = config_path if config_path.is_absolute() else (repo_root / config_path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    from utils.config import Config

    original_argv = sys.argv[:]
    try:
        sys.argv = [original_argv[0], "--cfg", str(config_path)]
        cfg_update = Config(load=True)
    finally:
        sys.argv = original_argv
    return cfg_update, config_path


def build_cfg(cfg_update):
    from tools.modules.config import cfg as global_cfg

    for key, value in cfg_update.cfg_dict.items():
        if isinstance(value, dict) and key in global_cfg:
            global_cfg[key].update(value)
        else:
            global_cfg[key] = value
    return global_cfg


def build_model(cfg):
    from utils.registry_class import MODEL

    model = MODEL.build(cfg.UNet)
    return model


def maybe_flops(model, x, t, y, image, sims, fps):
    try:
        from thop import profile
        from ptflops import get_model_complexity_info
    except Exception as exc:
        print(f"Optional complexity packages are missing: {exc}")
        return 0

    try:
        flops, params = get_model_complexity_info(
            model,
            tuple(x.shape[1:]),
            input_constructor=lambda _: {"x": [x, t, y, image, sims, fps]},
            as_strings=True,
            print_per_layer_stat=False,
        )
        print(f"PTFLOPS: flops={flops} params={params}")
    except Exception as exc:
        print(f"ptflops complexity check failed: {exc}")

    try:
        flops, params = profile(model=model, inputs=(x, t, y, image, sims, fps), verbose=False)
        print(f"THOP: flops={flops / 1e9:.3f} GFLOPs params={params / 1e6:.3f} M")
    except Exception as exc:
        print(f"thop complexity check failed: {exc}")
    return 0


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.device == "cuda":
        try:
            import torch
        except Exception as exc:
            print(f"ERROR: torch is required for the smoke forward: {exc}", file=sys.stderr)
            return 1
        if not torch.cuda.is_available():
            print("ERROR: CUDA is not available in this environment.", file=sys.stderr)
            return 1
        device = torch.device("cuda")
    else:
        import torch
        device = torch.device("cpu")

    cfg_update, config_path = load_config(repo_root, Path(args.config))
    cfg = build_cfg(cfg_update)

    import tools  # noqa: F401 - register repo modules before building
    model = build_model(cfg)
    model = model.to(device)
    model.eval()

    param_count = sum(p.numel() for p in model.parameters())
    print(f"Loaded config: {config_path}")
    print(f"Model class: {model.__class__.__name__}")
    print(f"Parameter count: {param_count:,}")

    if args.skip_forward:
        return 0

    resolution = list(getattr(cfg, "resolution", [448, 256]))
    scale = float(getattr(cfg, "scale_factor", 0.18215))
    latent_w = max(1, int(resolution[0] / 8))
    latent_h = max(1, int(resolution[1] / 8))
    frames = max(1, int(args.frames))
    batch = max(1, int(args.batch_size))
    y_dim = int(getattr(cfg.UNet, "y_dim", 1024) if hasattr(cfg.UNet, "y_dim") else cfg.UNet.get("y_dim", 1024))
    target_fps = int(getattr(cfg, "target_fps", 8))

    x = torch.randn(batch, 4, frames, latent_h, latent_w, device=device)
    t = torch.zeros(batch, device=device, dtype=torch.long)
    sims = torch.zeros(batch, 32, device=device)
    fps = torch.full((1,), target_fps, device=device, dtype=torch.long)
    y = torch.randn(batch, 1, y_dim, device=device)
    image = torch.randn(batch, 3, resolution[1], resolution[0], device=device)

    print(f"Smoke shapes: x={tuple(x.shape)} t={tuple(t.shape)} y={tuple(y.shape)} image={tuple(image.shape)} sims={tuple(sims.shape)} fps={tuple(fps.shape)}")

    with torch.no_grad():
        try:
            output = model(x=x, t=t, y=y, ori_img=image, sims=sims, fps=fps)
        except TypeError as exc:
            print(f"ERROR: forward signature mismatch for this model family: {exc}", file=sys.stderr)
            return 1
        except RuntimeError as exc:
            print(f"ERROR: forward runtime failure: {exc}", file=sys.stderr)
            return 1

    if hasattr(output, "shape"):
        print(f"Forward output shape: {tuple(output.shape)}")
    else:
        print(f"Forward output type: {type(output).__name__}")

    if args.check_flops:
        maybe_flops(model, x, t, y, image, sims, fps)

    print("Forward smoke complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
