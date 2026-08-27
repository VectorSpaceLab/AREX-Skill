#!/usr/bin/env python3
"""Optimize an image toward a reference image with LPIPS loss.

This is a bounded, headless-friendly replacement for the stock demo. It saves
initial and final images and prints the loss trend instead of opening a GUI.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import torch

from lpips_common import image_to_tensor, make_lpips_model, resolve_example_path, save_tensor_image


DEFAULT_REF = resolve_example_path("ex_ref.png")
DEFAULT_PRED = resolve_example_path("ex_p1.png")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--ref_path", type=Path, default=DEFAULT_REF, help="Reference image path.")
    parser.add_argument("--pred_path", type=Path, default=DEFAULT_PRED, help="Initial image path.")
    parser.add_argument("--out_dir", type=Path, default=Path("lpips_optimization"), help="Directory for saved optimization artifacts.")
    parser.add_argument("--steps", type=int, default=50, help="Number of optimization steps to run.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate.")
    parser.add_argument("--net", choices=["squeeze", "alex", "vgg"], default="alex", help="LPIPS backbone used for the loss.")
    parser.add_argument("--version", default="0.1", help="LPIPS weight version.")
    parser.add_argument("--use_gpu", action="store_true", help="Use CUDA when available.")
    parser.add_argument("--from_scratch", action="store_true", help="Use a random LPIPS trunk instead of pretrained trunk weights.")
    parser.add_argument("--train_trunk", action="store_true", help="Allow tuning the LPIPS trunk when constructing the model.")
    parser.add_argument("--save_every", type=int, default=10, help="Save intermediate predictions every N steps; 0 disables intermediate saves.")
    args = parser.parse_args(argv)

    model, device = make_lpips_model(
        model="lpips",
        net=args.net,
        version=args.version,
        use_gpu=args.use_gpu,
        pnet_rand=args.from_scratch,
        pnet_tune=args.train_trunk,
        spatial=False,
        verbose=False,
    )

    ref = image_to_tensor(args.ref_path).to(device)
    pred = image_to_tensor(args.pred_path).to(device)
    pred = torch.nn.Parameter(pred.clone())

    args.out_dir.mkdir(parents=True, exist_ok=True)
    save_tensor_image(ref, args.out_dir / "reference.png")
    save_tensor_image(pred.detach(), args.out_dir / "initial.png")

    optimizer = torch.optim.Adam([pred], lr=args.lr, betas=(0.9, 0.999))
    history = []

    for step in range(args.steps):
        loss = model(pred, ref)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            pred.clamp_(-1.0, 1.0)
        value = float(loss.detach().cpu().view(-1)[0].item())
        history.append(value)
        if step % max(1, args.save_every) == 0:
            print(f"step {step:04d}: lpips={value:.6f}")
            if args.save_every > 0:
                save_tensor_image(pred.detach(), args.out_dir / f"step_{step:04d}.png")

    save_tensor_image(pred.detach(), args.out_dir / "final.png")
    (args.out_dir / "loss.txt").write_text("\n".join(f"{value:.8f}" for value in history) + "\n", encoding="utf-8")
    print(f"saved final result to {args.out_dir / 'final.png'}")
    print(f"final loss: {history[-1]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
