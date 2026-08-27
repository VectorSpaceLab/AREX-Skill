#!/usr/bin/env python3
"""Safe DALLE2-pytorch runtime checks for generation/API workflows.

Modes:
  imports      Import the public package/classes without constructing CLIP adapters.
  tiny-forward Run tiny CPU synthetic prior and decoder forward-loss checks.
  cli-help     Invoke the installed dream CLI help.

The script uses only public package names (`dalle2-pytorch`, `dalle2_pytorch`),
does not assume repository files, and avoids network/model-weight downloads.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable


CORE_IMPORTS: tuple[str, ...] = (
    "DALLE2",
    "DiffusionPriorNetwork",
    "DiffusionPrior",
    "Unet",
    "Decoder",
    "OpenAIClipAdapter",
    "OpenClipAdapter",
    "VQGanVAE",
)


def fail(message: str, *, hint: str | None = None, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT: {hint}", file=sys.stderr)
    raise SystemExit(code)


def dist_version() -> str:
    for name in ("dalle2-pytorch", "dalle2_pytorch"):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return "unknown"


def require_attrs(module: object, names: Iterable[str]) -> None:
    missing = [name for name in names if not hasattr(module, name)]
    if missing:
        fail(
            "dalle2_pytorch imported but expected public attributes are missing: "
            + ", ".join(missing),
            hint="Check that the installed package is dalle2-pytorch version 1.15.6 or a compatible release.",
        )


def mode_imports(_: argparse.Namespace) -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        fail(
            f"PyTorch import failed: {exc}",
            hint="Install a working torch/torchvision pair for your CPU or CUDA backend before using dalle2-pytorch.",
        )

    try:
        dalle2_pytorch = importlib.import_module("dalle2_pytorch")
    except Exception as exc:
        fail(
            f"dalle2_pytorch import failed: {exc}",
            hint="Install with `python -m pip install dalle2-pytorch`, then run `python -m pip check`.",
        )

    require_attrs(dalle2_pytorch, CORE_IMPORTS)

    try:
        importlib.import_module("dalle2_pytorch.cli")
        importlib.import_module("dalle2_pytorch.tokenizer")
    except Exception as exc:
        fail(
            f"support module import failed: {exc}",
            hint="A dependency such as click, ftfy, regex, clip-anytorch, or torchvision may be missing or incompatible.",
        )

    print("OK imports")
    print(f"python={sys.version.split()[0]}")
    print(f"torch={torch.__version__}")
    print(f"dalle2-pytorch={dist_version()}")
    print("public_classes=" + ",".join(CORE_IMPORTS))
    print("note=CLIP adapters were not instantiated, so no model weights were downloaded")


def mode_tiny_forward(_: argparse.Namespace) -> None:
    try:
        import torch
        from dalle2_pytorch import Decoder, DiffusionPrior, DiffusionPriorNetwork, Unet
    except Exception as exc:
        fail(
            f"required imports for tiny-forward failed: {exc}",
            hint="Run this script with `--mode imports` first and fix any missing package dependencies.",
        )

    torch.manual_seed(0)
    device = torch.device("cpu")

    try:
        net = DiffusionPriorNetwork(
            dim=16,
            depth=1,
            dim_head=8,
            heads=2,
            num_timesteps=8,
            max_text_len=8,
        ).to(device)
        prior = DiffusionPrior(
            net=net,
            image_embed_dim=16,
            timesteps=8,
            sample_timesteps=2,
            condition_on_text_encodings=False,
        ).to(device)

        text_embed = torch.randn(2, 16, device=device)
        image_embed = torch.randn(2, 16, device=device)
        prior_loss = prior(text_embed=text_embed, image_embed=image_embed)

        unet = Unet(
            dim=16,
            image_embed_dim=16,
            cond_dim=8,
            dim_mults=(1,),
            channels=3,
        ).to(device)
        decoder = Decoder(
            unet=unet,
            image_size=16,
            timesteps=8,
            sample_timesteps=2,
            learned_variance=False,
        ).to(device)

        images = torch.rand(2, 3, 16, 16, device=device)
        decoder_loss = decoder(images, image_embed=image_embed)
    except AssertionError as exc:
        fail(
            f"tiny model assertion failed: {exc}",
            hint="If you edited the tiny dimensions, restore the defaults in this script; real checkpoints require their exact training architecture.",
        )
    except RuntimeError as exc:
        fail(
            f"tiny CPU forward failed at runtime: {exc}",
            hint="Check torch/torchvision compatibility and available CPU memory. This mode should not require GPU or network.",
        )
    except Exception as exc:
        fail(
            f"tiny CPU forward failed: {exc}",
            hint="Run `python -m pip check`; then inspect generation-and-api troubleshooting for dependency or API mismatches.",
        )

    print("OK tiny-forward")
    print(f"device={device}")
    print(f"prior_loss={float(prior_loss.detach().cpu()):.6f}")
    print(f"decoder_loss={float(decoder_loss.detach().cpu()):.6f}")
    print("note=no CLIP adapters, checkpoints, repository files, network, or GPU were used")


def dream_help_command() -> list[str]:
    dream = shutil.which("dream")
    if dream:
        return [dream, "--help"]

    sibling = Path(sys.executable).with_name("dream")
    if sibling.exists():
        return [str(sibling), "--help"]

    return [
        sys.executable,
        "-c",
        "from dalle2_pytorch.cli import dream; dream.main(args=['--help'], prog_name='dream')",
    ]


def mode_cli_help(_: argparse.Namespace) -> None:
    cmd = dream_help_command()
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except FileNotFoundError as exc:
        fail(
            f"could not execute dream help command: {exc}",
            hint="Install the console script with `python -m pip install dalle2-pytorch` in the active environment.",
        )
    except subprocess.TimeoutExpired:
        fail(
            "dream --help timed out",
            hint="CLI help should be fast and should not load model weights. Check for a broken Python environment.",
        )

    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        fail(
            f"dream help exited with status {completed.returncode}\n{output.strip()}",
            hint="The CLI import path may be broken. Run `--mode imports` and `python -m pip check`.",
        )

    required_tokens = ("--model", "--cond_scale", "TEXT")
    missing = [token for token in required_tokens if token not in output]
    if missing:
        fail(
            "dream help ran but expected options were missing: " + ", ".join(missing),
            hint="Check whether a different `dream` executable shadows the dalle2-pytorch console command on PATH.",
        )

    print("OK cli-help")
    print("command=dream --help")
    print("found_options=" + ",".join(required_tokens))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe DALLE2-pytorch generation/API runtime checks without network downloads.",
    )
    parser.add_argument(
        "--mode",
        choices=("imports", "tiny-forward", "cli-help"),
        default="imports",
        help="Which check to run. Default: imports.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mode == "imports":
        mode_imports(args)
    elif args.mode == "tiny-forward":
        mode_tiny_forward(args)
    elif args.mode == "cli-help":
        mode_cli_help(args)
    else:  # pragma: no cover - argparse prevents this
        parser.error(f"unsupported mode {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
