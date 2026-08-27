#!/usr/bin/env python3
"""Build safe CLAM feature-extraction commands without touching slides or models."""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import sys
from pathlib import Path

ENCODERS = {
    "resnet50_trunc": {
        "embed_dim": 1024,
        "env_var": None,
        "requirement": "No user checkpoint environment variable is required.",
    },
    "uni_v1": {
        "embed_dim": 1024,
        "env_var": "UNI_CKPT_PATH",
        "requirement": "UNI_CKPT_PATH must point to the downloaded UNI pytorch_model.bin checkpoint.",
    },
    "conch_v1": {
        "embed_dim": 512,
        "env_var": "CONCH_CKPT_PATH",
        "requirement": "CONCH_CKPT_PATH must point to the downloaded CONCH checkpoint and the CONCH package must be installed.",
    },
}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def slide_extension(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("slide extension cannot be empty")
    if not value.startswith("."):
        raise argparse.ArgumentTypeError("slide extension must start with '.', for example .svs")
    if any(separator in value for separator in ("/", "\\")):
        raise argparse.ArgumentTypeError("slide extension must be a suffix, not a path")
    if value.strip() != value or any(character.isspace() for character in value):
        raise argparse.ArgumentTypeError("slide extension must not contain whitespace")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate safe CLAM feature-extraction options and print an "
            "extract_features_fp.py command. This helper never opens slides, "
            "loads checkpoints, imports CLAM, or downloads weights."
        )
    )
    parser.add_argument("--data_h5_dir", required=True, help="Parent directory containing patches/<slide_id>.h5 coordinate files.")
    parser.add_argument("--data_slide_dir", required=True, help="Directory containing <slide_id><slide_ext> WSI files.")
    parser.add_argument("--csv_path", required=True, help="CSV with a slide_id column.")
    parser.add_argument("--feat_dir", required=True, help="Output directory where h5_files/ and pt_files/ will be written.")
    parser.add_argument("--slide_ext", type=slide_extension, default=".svs", help="Slide filename extension, including the leading dot.")
    parser.add_argument("--model_name", choices=sorted(ENCODERS), default="resnet50_trunc", help="CLAM encoder name accepted by extract_features_fp.py.")
    parser.add_argument("--batch_size", type=positive_int, default=256, help="Patch inference batch size; reduce for CUDA memory failures.")
    parser.add_argument("--target_patch_size", type=positive_int, default=224, help="Resize target passed to CLAM transforms.")
    parser.add_argument("--no_auto_skip", action="store_true", help="Include CLAM's recompute flag instead of skipping existing .pt files.")
    parser.add_argument("--python", default="python", help="Python command to show in the generated command.")
    parser.add_argument("--cuda_visible_devices", default=None, help="Optional CUDA_VISIBLE_DEVICES value to prefix in the generated command.")
    parser.add_argument("--preview_rows", type=positive_int, default=3, help="Maximum CSV slide_id rows to preview.")
    return parser


def quote_command(parts: list[str], cuda_visible_devices: str | None) -> str:
    rendered = " ".join(shlex.quote(part) for part in parts)
    if cuda_visible_devices is None:
        return rendered
    return f"CUDA_VISIBLE_DEVICES={shlex.quote(cuda_visible_devices)} {rendered}"


def read_slide_ids(csv_path: Path, limit: int) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    slide_ids: list[str] = []

    if not csv_path.exists():
        warnings.append(f"CSV path does not exist yet: {csv_path}")
        return slide_ids, warnings
    if not csv_path.is_file():
        warnings.append(f"CSV path is not a file: {csv_path}")
        return slide_ids, warnings

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                warnings.append("CSV appears to be empty or missing a header row.")
                return slide_ids, warnings
            if "slide_id" not in reader.fieldnames:
                warnings.append("CSV is missing required slide_id column.")
                return slide_ids, warnings
            for row in reader:
                value = (row.get("slide_id") or "").strip()
                if value:
                    slide_ids.append(value)
                if len(slide_ids) >= limit:
                    break
    except UnicodeDecodeError:
        warnings.append("CSV could not be read as UTF-8 text.")
    except OSError as exc:
        warnings.append(f"CSV could not be read: {exc}")

    if not slide_ids and not warnings:
        warnings.append("CSV has a slide_id column but no non-empty preview rows were found.")
    return slide_ids, warnings


def clam_slide_base(raw_slide_id: str, slide_ext: str) -> str:
    return raw_slide_id.split(slide_ext)[0]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    encoder = ENCODERS[args.model_name]

    warnings: list[str] = []
    if args.target_patch_size != 224:
        warnings.append(
            "target_patch_size is not 224; this is allowed, but keep it consistent "
            "across comparable feature sets."
        )
    if args.model_name in {"uni_v1", "conch_v1"} and args.batch_size > 256:
        warnings.append(
            f"{args.model_name} can require more GPU memory than resnet50_trunc; "
            "consider lowering batch_size if CUDA OOM occurs."
        )

    env_var = encoder["env_var"]
    env_status = "not required"
    if env_var is not None:
        env_status = "set" if os.environ.get(env_var) else "missing"
        if env_status == "missing":
            warnings.append(f"{env_var} is not set; CLAM will fail when loading {args.model_name}.")

    csv_path = Path(args.csv_path)
    preview_ids, csv_warnings = read_slide_ids(csv_path, args.preview_rows)
    warnings.extend(csv_warnings)

    command = [
        args.python,
        "extract_features_fp.py",
        "--data_h5_dir",
        args.data_h5_dir,
        "--data_slide_dir",
        args.data_slide_dir,
        "--csv_path",
        args.csv_path,
        "--feat_dir",
        args.feat_dir,
        "--slide_ext",
        args.slide_ext,
        "--model_name",
        args.model_name,
        "--batch_size",
        str(args.batch_size),
        "--target_patch_size",
        str(args.target_patch_size),
    ]
    if args.no_auto_skip:
        command.append("--no_auto_skip")

    print("CLAM feature extraction command")
    print(quote_command(command, args.cuda_visible_devices))
    print()
    print("Encoder")
    print(f"  model_name: {args.model_name}")
    print(f"  downstream embed_dim: {encoder['embed_dim']}")
    print(f"  checkpoint requirement: {encoder['requirement']}")
    print(f"  checkpoint env status: {env_status}")
    print()
    print("Expected output layout")
    print(f"  {Path(args.feat_dir) / 'h5_files' / '<slide_id>.h5'}")
    print(f"  {Path(args.feat_dir) / 'pt_files' / '<slide_id>.pt'}")

    if preview_ids:
        print()
        print("Previewed slide mapping")
        for raw_slide_id in preview_ids:
            slide_base = clam_slide_base(raw_slide_id, args.slide_ext)
            coord_path = Path(args.data_h5_dir) / "patches" / f"{slide_base}.h5"
            slide_path = Path(args.data_slide_dir) / f"{slide_base}{args.slide_ext}"
            output_pt = Path(args.feat_dir) / "pt_files" / f"{slide_base}.pt"
            print(f"  csv slide_id: {raw_slide_id}")
            print(f"    coordinate h5: {coord_path}")
            print(f"    slide file:     {slide_path}")
            print(f"    output pt:      {output_pt}")
            if raw_slide_id != slide_base and not raw_slide_id.endswith(args.slide_ext):
                warnings.append(
                    f"slide_id {raw_slide_id!r} contains {args.slide_ext!r} before the end; "
                    f"CLAM will truncate it to {slide_base!r}."
                )

    if warnings:
        print()
        print("Warnings")
        for warning in warnings:
            print(f"  - {warning}")

    print()
    print("Safety")
    print("  This helper only validates strings, reads CSV text when available, and prints paths.")
    print("  It does not open WSI/HDF5 files, load encoders or checkpoints, import CLAM, or download weights.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
