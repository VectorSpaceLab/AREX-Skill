#!/usr/bin/env python3
"""Build a safe esm-extract command without loading ESM model weights."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

INCLUDE_CHOICES = ("mean", "per_tok", "bos", "contacts")
MSA_MODEL_MARKERS = ("esm_msa", "msa1", "msa_transformer", "msa-transformer")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def layer_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"representation layer must be an integer, got {value!r}") from exc


def existing_fasta(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"FASTA file does not exist: {path}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"FASTA path is not a file: {path}")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate options and build an esm-extract command. The default "
            "--print-only mode does not import esm or download model weights."
        )
    )
    parser.add_argument("model_location", help="Pretrained model name or local .pt checkpoint path")
    parser.add_argument("fasta_file", type=existing_fasta, help="Existing FASTA file to embed")
    parser.add_argument("output_dir", type=Path, help="Directory where esm-extract should write .pt files")
    parser.add_argument(
        "--repr-layers",
        "--repr_layers",
        dest="repr_layers",
        nargs="+",
        type=layer_int,
        default=[-1],
        help="Representation layer indices to request; -1 means final layer in esm-extract",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        choices=INCLUDE_CHOICES,
        default=["mean"],
        help="Outputs to include in each .pt file",
    )
    parser.add_argument(
        "--toks-per-batch",
        "--toks_per_batch",
        dest="toks_per_batch",
        type=positive_int,
        default=4096,
        help="Maximum approximate tokens per batch",
    )
    parser.add_argument(
        "--truncation-seq-length",
        "--truncation_seq_length",
        dest="truncation_seq_length",
        type=positive_int,
        default=1022,
        help="Maximum residues retained per sequence",
    )
    parser.add_argument("--nogpu", action="store_true", help="Force esm-extract to run on CPU")
    parser.add_argument(
        "--runner",
        choices=("esm-extract", "python-script"),
        default="esm-extract",
        help="Use the console entry point or run a provided extract.py script",
    )
    parser.add_argument(
        "--script-path",
        type=Path,
        help="Path to extract.py when --runner python-script is selected",
    )
    parser.add_argument(
        "--print-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print the command instead of executing it; defaults to true",
    )
    return parser


def is_msa_model(model_location: str) -> bool:
    lowered = model_location.lower()
    return any(marker in lowered for marker in MSA_MODEL_MARKERS)


def command_parts(args: argparse.Namespace) -> List[str]:
    if args.runner == "python-script":
        if args.script_path is None:
            raise SystemExit("--script-path is required when --runner python-script is used")
        script_path = args.script_path.expanduser()
        if not script_path.exists() or not script_path.is_file():
            raise SystemExit(f"extract.py script path does not exist or is not a file: {script_path}")
        parts = [sys.executable, str(script_path)]
    else:
        parts = ["esm-extract"]

    parts.extend([args.model_location, str(args.fasta_file), str(args.output_dir)])
    parts.append("--repr_layers")
    parts.extend(str(layer) for layer in args.repr_layers)
    parts.append("--include")
    parts.extend(args.include)
    parts.extend(["--toks_per_batch", str(args.toks_per_batch)])
    parts.extend(["--truncation_seq_length", str(args.truncation_seq_length)])
    if args.nogpu:
        parts.append("--nogpu")
    return parts


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if is_msa_model(args.model_location):
        parser.exit(
            2,
            "error: MSA Transformer models are not supported by esm-extract; "
            "use the Python MSABatchConverter workflow instead.\n",
        )

    if "contacts" in args.include and "bos" in args.include:
        print(
            "warning: --include bos is available, but upstream docs caution that BOS embeddings "
            "were not trained for supervised interpretation.",
            file=sys.stderr,
        )

    parts = command_parts(args)
    print(quote_command(parts))

    if args.print_only:
        return 0

    completed = subprocess.run(parts, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
