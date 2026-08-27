#!/usr/bin/env python3
"""Dry-run command builder for pytorch-semseg single-image inference.

This helper validates command-line choices and prints a `test.py` invocation.
It does not import pytorch-semseg, load images, load checkpoints, read datasets,
run models, download files, or write outputs.
"""

from __future__ import annotations

import argparse
import importlib.util
import shlex
import sys
from pathlib import Path


MODEL_IDS = (
    "fcn32s",
    "fcn16s",
    "fcn8s",
    "unet",
    "segnet",
    "pspnet",
    "icnet",
    "icnetBN",
    "linknet",
    "frrnA",
    "frrnB",
)

DATASETS = {
    "pascal": "Pascal VOC palette; commonly works with root=None/test_mode=True.",
    "camvid": "CamVid palette; commonly works with root=None/test_mode=True.",
    "ade20k": "ADE20K generated palette; commonly works with root=None/test_mode=True.",
    "cityscapes": "Cityscapes palette; loader may still touch dataset directories.",
    "nyuv2": "NYUv2 palette; loader may still touch dataset directories.",
    "sunrgbd": "SUNRGBD palette; loader may still touch dataset directories.",
    "vistas": "Mapillary Vistas palette from config.json; dataset-bound unless adapted.",
    "mit_sceneparsing_benchmark": "Registry key exists, but inspected loader lacks decode_segmap.",
}

DATASET_BOUND_WITH_ROOT_NONE = {
    "cityscapes",
    "nyuv2",
    "sunrgbd",
    "vistas",
    "mit_sceneparsing_benchmark",
}

ODD_SIZE_MODELS = {"pspnet", "icnet", "icnetBN"}
CHECKPOINT_SUFFIXES = {".pkl", ".pth", ".pt", ".ckpt"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def add_bool_flags(parser: argparse.ArgumentParser) -> None:
    norm = parser.add_mutually_exclusive_group()
    norm.add_argument(
        "--img_norm",
        dest="img_norm",
        action="store_true",
        help="Emit --img_norm in the test.py command (source default).",
    )
    norm.add_argument(
        "--no-img_norm",
        dest="img_norm",
        action="store_false",
        help="Emit --no-img_norm in the test.py command.",
    )

    dcrf = parser.add_mutually_exclusive_group()
    dcrf.add_argument(
        "--dcrf",
        dest="dcrf",
        action="store_true",
        help="Emit --dcrf and warn about optional pydensecrf requirements.",
    )
    dcrf.add_argument(
        "--no-dcrf",
        dest="dcrf",
        action="store_false",
        help="Emit --no-dcrf (source default).",
    )

    parser.set_defaults(img_norm=True, dcrf=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build and validate a dry-run pytorch-semseg test.py command for "
            "one-image inference. No images, checkpoints, datasets, or models are loaded."
        )
    )
    parser.add_argument(
        "--model_path",
        "--model-path",
        dest="model_path",
        required=True,
        help="Checkpoint path. Basename should be <arch>_<description>.pkl/.pth/.pt/.ckpt.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=sorted(DATASETS),
        help="Dataset key passed to test.py and used for palette decoding.",
    )
    parser.add_argument("--img_path", "--img-path", dest="img_path", required=True, help="Input image path to pass to test.py.")
    parser.add_argument("--out_path", "--out-path", dest="out_path", required=True, help="Output color mask path to pass to test.py.")
    add_bool_flags(parser)
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable to place at the front of the emitted command (default: python).",
    )
    parser.add_argument(
        "--test-script",
        default="test.py",
        help="Path to the repository test.py in the emitted command (default: test.py).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if warnings are produced.",
    )
    parser.add_argument(
        "--no-check-optional-imports",
        action="store_true",
        help="Do not check whether optional pydensecrf appears importable when --dcrf is set.",
    )
    return parser


def source_style_arch_from_basename(basename: str) -> str:
    """Match the source script's basename[:basename.find('_')] behavior."""
    return basename[: basename.find("_")]


def validate_checkpoint(path_text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    path = Path(path_text).expanduser()
    basename = path.name

    if not basename:
        warnings.append("Checkpoint path has no basename; test.py cannot parse the architecture id.")
        return "", warnings

    parsed_arch = source_style_arch_from_basename(basename)

    if "_" not in basename:
        warnings.append(
            "Checkpoint basename contains no underscore. Source test.py uses "
            "basename[:basename.find('_')], so it will parse {!r} rather than the intended model id.".format(
                parsed_arch
            )
        )
    elif basename.startswith("_"):
        warnings.append("Checkpoint basename starts with '_' so the parsed architecture id is empty.")
    elif not parsed_arch:
        warnings.append("Checkpoint basename did not yield a non-empty architecture id.")

    if parsed_arch and parsed_arch not in MODEL_IDS:
        warnings.append(
            "Parsed architecture {!r} is not one of the known pytorch-semseg model ids: {}.".format(
                parsed_arch, ", ".join(MODEL_IDS)
            )
        )

    if path.suffix and path.suffix.lower() not in CHECKPOINT_SUFFIXES:
        warnings.append(
            "Checkpoint suffix {!r} is unusual. test.py uses torch.load, but common repo checkpoints use {}.".format(
                path.suffix, ", ".join(sorted(CHECKPOINT_SUFFIXES))
            )
        )
    elif not path.suffix:
        warnings.append("Checkpoint has no file suffix; this is allowed only if torch.load can read it.")

    if path.exists():
        if not path.is_file():
            warnings.append("Checkpoint path exists but is not a regular file.")
    else:
        warnings.append("Checkpoint path does not exist; create or correct it before running real inference.")

    return parsed_arch, warnings


def validate_image(path_text: str) -> list[str]:
    warnings: list[str] = []
    path = Path(path_text).expanduser()
    if path.exists():
        if not path.is_file():
            warnings.append("Input image path exists but is not a regular file.")
    else:
        warnings.append("Input image path does not exist; create or correct it before running real inference.")

    if path.suffix and path.suffix.lower() not in IMAGE_SUFFIXES:
        warnings.append(
            "Input image suffix {!r} is unusual for the legacy image reader.".format(path.suffix)
        )
    elif not path.suffix:
        warnings.append("Input image has no suffix; legacy image readers may not infer the format.")
    return warnings


def validate_output(path_text: str) -> list[str]:
    warnings: list[str] = []
    path = Path(path_text).expanduser()
    parent = path.parent if str(path.parent) else Path(".")

    if path.exists() and path.is_dir():
        warnings.append("Output path is an existing directory; provide a file path instead.")

    if parent and not parent.exists():
        warnings.append("Output parent directory does not exist; create it before running real inference.")
    elif parent and not parent.is_dir():
        warnings.append("Output parent exists but is not a directory.")

    if path.suffix.lower() != ".png":
        warnings.append(
            "Prefer a .png output path. DenseCRF derives its extra output as out_path[:-4] + '_drf.png'."
        )
    return warnings


def validate_test_script(path_text: str) -> list[str]:
    warnings: list[str] = []
    path = Path(path_text).expanduser()
    if not path.exists():
        warnings.append(
            "test.py path does not exist relative to the current directory. "
            "Run the emitted command from the repository root or pass --test-script."
        )
    elif not path.is_file():
        warnings.append("test.py path exists but is not a regular file.")
    return warnings


def validate_dataset(dataset: str) -> list[str]:
    warnings: list[str] = []
    if dataset == "mit_sceneparsing_benchmark":
        warnings.append(
            "The inspected MIT Scene Parsing loader lacks decode_segmap, so unmodified test.py is not expected to save a decoded mask for this key."
        )
    elif dataset in DATASET_BOUND_WITH_ROOT_NONE:
        warnings.append(
            "The selected dataset loader may touch dataset directories/config files even though test.py passes root=None and test_mode=True; "
            "patch a palette-only/test-mode path if loader construction fails."
        )
    return warnings


def validate_dcrf(enabled: bool, skip_import_check: bool) -> list[str]:
    warnings: list[str] = []
    if not enabled:
        return warnings

    warnings.append(
        "DenseCRF is optional and assumes pydensecrf plus probability-like positive model outputs for -log(outputs)."
    )
    if not skip_import_check and importlib.util.find_spec("pydensecrf") is None:
        warnings.append(
            "pydensecrf does not appear importable in this Python environment; a real --dcrf run will fail unless it is installed."
        )
    return warnings


def command_for(args: argparse.Namespace) -> list[str]:
    return [
        args.python,
        args.test_script,
        "--model_path",
        args.model_path,
        "--dataset",
        args.dataset,
        "--img_norm" if args.img_norm else "--no-img_norm",
        "--dcrf" if args.dcrf else "--no-dcrf",
        "--img_path",
        args.img_path,
        "--out_path",
        args.out_path,
    ]


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    warnings: list[str] = []
    arch, checkpoint_warnings = validate_checkpoint(args.model_path)
    warnings.extend(checkpoint_warnings)
    warnings.extend(validate_dataset(args.dataset))
    warnings.extend(validate_image(args.img_path))
    warnings.extend(validate_output(args.out_path))
    warnings.extend(validate_test_script(args.test_script))
    warnings.extend(validate_dcrf(args.dcrf, args.no_check_optional_imports))

    if arch in ODD_SIZE_MODELS:
        warnings.append(
            "Architecture {!r} uses the PSPNet/ICNet path: test.py resizes the input to odd dimensions before inference and resizes predictions back.".format(
                arch
            )
        )

    if not args.img_norm:
        warnings.append(
            "--no-img_norm changes preprocessing. Use it only if the checkpoint was trained without [0, 1] image normalization."
        )

    print("Parsed checkpoint architecture: {}".format(arch or "<empty>"))
    print("Dataset: {} - {}".format(args.dataset, DATASETS[args.dataset]))
    print("Image normalization: {}".format("enabled" if args.img_norm else "disabled"))
    print("DenseCRF: {}".format("enabled" if args.dcrf else "disabled"))
    print("\nCommand:")
    print(quote_command(command_for(args)))

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print("- " + item)
    else:
        print("\nValidation: no warnings.")

    if args.strict and warnings:
        print("\nStrict mode: warnings treated as errors.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
