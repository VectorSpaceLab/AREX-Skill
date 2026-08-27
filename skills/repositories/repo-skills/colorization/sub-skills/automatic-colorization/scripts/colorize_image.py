#!/usr/bin/env python3
"""Headless automatic image colorization helper.

This helper mirrors the release-style workflow for the ECCV16 and SIGGRAPH17
colorizers:

1. load an input image,
2. preprocess the image to original and 256x256 L-channel tensors,
3. run the selected pretrained or untrained model(s),
4. postprocess the predicted ab channels back to the original resolution, and
5. save PNG outputs.

The script is designed to run from an arbitrary current directory when
`--repo-root` points at a local import root that contains the `colorizers`
package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Colorize one image with ECCV16 and/or SIGGRAPH17."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help=(
            "Optional import root that contains the colorizers package. "
            "Use this when the package is not already installed."
        ),
    )
    parser.add_argument(
        "--input-image",
        type=str,
        required=True,
        help="Path to the image to colorize.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory where PNG outputs will be written.",
    )
    parser.add_argument(
        "--save-prefix",
        type=str,
        default="saved",
        help="Filename stem used before the model suffix.",
    )
    parser.add_argument(
        "--model",
        choices=("eccv16", "siggraph17", "both"),
        default="both",
        help="Select one model or run both.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="auto",
        help="Choose the execution device.",
    )
    parser.add_argument(
        "--skip-pretrained",
        action="store_true",
        help=(
            "Construct models without pretrained weights. Useful for smoke/API "
            "checks only; not for quality colorization."
        ),
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help=(
            "Accepted for compatibility. The helper is headless and never opens "
            "a display window."
        ),
    )
    return parser


class UserFacingError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def fail(message: str, code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return code


def configure_import_path(repo_root: str | None) -> None:
    if repo_root is None:
        return

    root = Path(repo_root).expanduser()
    if not root.exists():
        raise UserFacingError(
            f"--repo-root does not exist: {repo_root}",
            code=2,
        )
    root = root.resolve()
    colorizers_dir = root / "colorizers"
    if not colorizers_dir.is_dir():
        raise UserFacingError(
            "--repo-root must point to a directory that contains colorizers/",
            code=2,
        )
    sys.path.insert(0, str(root))


def import_runtime(repo_root: str | None):
    configure_import_path(repo_root)

    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        import torch
        from colorizers import eccv16, siggraph17, load_img, postprocess_tens, preprocess_img
    except ImportError as exc:
        message = (
            f"Could not import the colorization runtime: {exc}\n"
            "Make sure the active environment has torch, numpy, matplotlib, "
            "pillow, scikit-image, and ipython installed, and pass --repo-root "
            "pointing at a local import root that contains colorizers/ if the "
            "package is not installed."
        )
        raise UserFacingError(message, code=1) from exc

    return plt, torch, eccv16, siggraph17, load_img, postprocess_tens, preprocess_img


def validate_paths(input_image: str, output_dir: str, save_prefix: str) -> tuple[Path, Path]:
    input_path = Path(input_image).expanduser()
    if not input_path.is_file():
        raise UserFacingError(f"--input-image is not a readable file: {input_image}", code=2)

    output_path = Path(output_dir).expanduser()
    if not save_prefix:
        raise UserFacingError("--save-prefix must not be empty", code=2)
    if "/" in save_prefix or "\\" in save_prefix:
        raise UserFacingError(
            "--save-prefix must be a filename stem; use --output-dir for directories",
            code=2,
        )

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UserFacingError(
            f"Could not create --output-dir {output_dir}: {exc}",
            code=2,
        ) from exc

    if not output_path.is_dir():
        raise UserFacingError(
            f"--output-dir is not a directory: {output_dir}",
            code=2,
        )

    return input_path, output_path


def choose_device(requested: str, torch):
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise UserFacingError(
                "--device cuda was requested, but PyTorch reports that CUDA is unavailable",
                code=2,
            )
        return torch.device("cuda")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_models(model_names: Iterable[str], pretrained: bool, eccv16, siggraph17, device, torch):
    factories = {
        "eccv16": eccv16,
        "siggraph17": siggraph17,
    }
    models = {}
    for name in model_names:
        factory = factories[name]
        try:
            model = factory(pretrained=pretrained).eval().to(device)
        except Exception as exc:
            if pretrained:
                message = (
                    f"Could not load pretrained weights for {name}: {exc}\n"
                    "The default pretrained path uses public model URLs and hash checking. "
                    "Retry when the network/cache is available, or use --skip-pretrained "
                    "only for smoke/API tests."
                )
            else:
                message = f"Could not initialize {name} without pretrained weights: {exc}"
            raise UserFacingError(message, code=1) from exc
        models[name] = model
    return models


def run_model(name: str, model, tens_l_orig, tens_l_rs, postprocess_tens, plt, device, torch, output_file: Path) -> None:
    try:
        with torch.no_grad():
            out_ab = model(tens_l_rs)
            out_img = postprocess_tens(tens_l_orig, out_ab.cpu())
    except RuntimeError as exc:
        hint = ""
        if device.type == "cuda":
            hint = " Try --device cpu, or confirm that your PyTorch build and GPU driver are compatible."
        raise UserFacingError(f"Colorization failed for {name}: {exc}.{hint}", code=1) from exc
    except Exception as exc:
        raise UserFacingError(f"Colorization failed for {name}: {exc}", code=1) from exc

    try:
        plt.imsave(str(output_file), out_img)
    except Exception as exc:
        raise UserFacingError(f"Could not save {output_file}: {exc}", code=1) from exc

    print(f"saved {output_file}")


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        plt, torch, eccv16, siggraph17, load_img, postprocess_tens, preprocess_img = import_runtime(args.repo_root)
        input_path, output_dir = validate_paths(args.input_image, args.output_dir, args.save_prefix)
        device = choose_device(args.device, torch)

        if args.skip_pretrained:
            print(
                "WARNING: --skip-pretrained disables learned weights; outputs are only for smoke/API checks.",
                file=sys.stderr,
            )

        model_order = ["eccv16", "siggraph17"] if args.model == "both" else [args.model]
        models = load_models(
            model_order,
            pretrained=not args.skip_pretrained,
            eccv16=eccv16,
            siggraph17=siggraph17,
            device=device,
            torch=torch,
        )

        try:
            img = load_img(str(input_path))
            tens_l_orig, tens_l_rs = preprocess_img(img, HW=(256, 256))
        except Exception as exc:
            raise UserFacingError(
                f"Could not read or preprocess --input-image {input_path}: {exc}",
                code=2,
            ) from exc

        tens_l_rs = tens_l_rs.to(device)

        outputs = {
            "eccv16": output_dir / f"{args.save_prefix}_eccv16.png",
            "siggraph17": output_dir / f"{args.save_prefix}_siggraph17.png",
        }

        for name in model_order:
            run_model(
                name=name,
                model=models[name],
                tens_l_orig=tens_l_orig,
                tens_l_rs=tens_l_rs,
                postprocess_tens=postprocess_tens,
                plt=plt,
                device=device,
                torch=torch,
                output_file=outputs[name],
            )

        return 0
    except UserFacingError as exc:
        return fail(str(exc), code=exc.code)


if __name__ == "__main__":
    raise SystemExit(main())
