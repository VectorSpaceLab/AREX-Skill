#!/usr/bin/env python3
"""Self-contained ESM-IF1 command helper for sampling and scoring.

The helper validates local inputs and prints a dry-run command by default. Use
--execute only when the environment is ready for ESM-IF1 model loading, optional
torch hub downloads, and CPU/GPU inference.
"""

from __future__ import annotations

import argparse
import csv
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

AMINO_ACID_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYBXZUOJ\-*\.]+$", re.IGNORECASE)
SUPPORTED_STRUCTURE_SUFFIXES = {".pdb", ".cif"}
SUPPORTED_FASTA_SUFFIXES = {".fa", ".faa", ".fasta", ".txt"}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct or execute ESM-IF1 inverse-folding sampling/scoring commands. "
            "Dry-run is the default and never loads the model."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the requested mode instead of printing a dry-run command.",
    )
    parser.add_argument(
        "--nogpu",
        action="store_true",
        help="Do not move the model to GPU even if CUDA is available.",
    )
    parser.add_argument(
        "--strict-fasta",
        action="store_true",
        help="Reject FASTA records with non-amino-acid characters during validation.",
    )
    parser.add_argument(
        "--repeat-threshold",
        type=int,
        default=8,
        help="Warn when sampled or input sequences contain homopolymer runs of at least this length.",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    sample_parser = subparsers.add_parser("sample", help="Sample sequences for a structure.")
    add_structure_args(sample_parser)
    sample_parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Sampling temperature; lower values increase native-like recovery.",
    )
    sample_parser.add_argument(
        "--num-samples",
        type=int,
        default=1,
        help="Number of sampled sequences to write.",
    )
    sample_parser.add_argument(
        "--outpath",
        required=True,
        help="Output FASTA path for sampled sequences.",
    )

    score_parser = subparsers.add_parser("score", help="Score FASTA sequences for a structure.")
    add_structure_args(score_parser)
    score_parser.add_argument(
        "seqfile",
        help="Input FASTA path containing target-chain sequences to score.",
    )
    score_parser.add_argument(
        "--outpath",
        required=True,
        help="Output CSV path for sequence log-likelihoods.",
    )

    return parser.parse_args(argv)


def add_structure_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("pdbfile", help="Input structure path ending in .pdb or .cif.")
    parser.add_argument(
        "--chain",
        default="A",
        help="Target chain ID for sampling/scoring. Defaults to A.",
    )
    parser.set_defaults(multichain_backbone=False)
    parser.add_argument(
        "--multichain-backbone",
        action="store_true",
        help="Condition on all parsed chains while sampling/scoring the target chain.",
    )
    parser.add_argument(
        "--singlechain-backbone",
        dest="multichain_backbone",
        action="store_false",
        help="Condition only on the target-chain backbone.",
    )


def validate_args(args: argparse.Namespace) -> None:
    structure_path = Path(args.pdbfile)
    if structure_path.suffix.lower() not in SUPPORTED_STRUCTURE_SUFFIXES:
        raise SystemExit(
            f"Structure must end in one of {sorted(SUPPORTED_STRUCTURE_SUFFIXES)}: {structure_path}"
        )
    if not args.chain:
        raise SystemExit("--chain must be a non-empty chain ID")
    if args.mode == "sample":
        if args.temperature <= 0:
            raise SystemExit("--temperature must be positive")
        if args.num_samples < 1:
            raise SystemExit("--num-samples must be at least 1")
        validate_output_path(Path(args.outpath), expected_suffixes={".fa", ".faa", ".fasta"})
    elif args.mode == "score":
        seq_path = Path(args.seqfile)
        if seq_path.suffix.lower() not in SUPPORTED_FASTA_SUFFIXES:
            print(
                f"warning: FASTA path has uncommon suffix {seq_path.suffix!r}; expected one of {sorted(SUPPORTED_FASTA_SUFFIXES)}",
                file=sys.stderr,
            )
        if args.execute and not seq_path.exists():
            raise SystemExit(f"FASTA file does not exist: {seq_path}")
        if seq_path.exists():
            records = read_fasta(seq_path)
            validate_fasta_records(records, strict=args.strict_fasta, repeat_threshold=args.repeat_threshold)
        validate_output_path(Path(args.outpath), expected_suffixes={".csv"})


def validate_output_path(path: Path, expected_suffixes: Set[str]) -> None:
    if path.suffix.lower() not in expected_suffixes:
        print(
            f"warning: output path {path} does not use expected suffix {sorted(expected_suffixes)}",
            file=sys.stderr,
        )
    if path.exists() and path.is_dir():
        raise SystemExit(f"Output path is a directory: {path}")


def read_fasta(path: Path) -> List[Tuple[str, str]]:
    records: List[Tuple[str, str]] = []
    header: Optional[str] = None
    chunks: List[str] = []
    with path.open() as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(chunks)))
                header = line[1:].strip() or f"record_{len(records) + 1}"
                chunks = []
            else:
                if header is None:
                    raise SystemExit(f"FASTA sequence before first header at {path}:{line_number}")
                chunks.append(line)
    if header is not None:
        records.append((header, "".join(chunks)))
    if not records:
        raise SystemExit(f"No FASTA records found in {path}")
    return records


def validate_fasta_records(
    records: Iterable[Tuple[str, str]], *, strict: bool, repeat_threshold: int
) -> None:
    for header, sequence in records:
        if not sequence:
            raise SystemExit(f"FASTA record {header!r} has an empty sequence")
        if strict and not AMINO_ACID_RE.match(sequence):
            raise SystemExit(f"FASTA record {header!r} contains non-protein characters")
        repeat = longest_homopolymer(sequence)
        if repeat >= repeat_threshold:
            print(
                f"warning: FASTA record {header!r} has a homopolymer run of length {repeat}",
                file=sys.stderr,
            )
        if "," in header:
            print(
                f"warning: FASTA header {header!r} contains a comma; simple CSV output may be awkward to parse",
                file=sys.stderr,
            )


def longest_homopolymer(sequence: str) -> int:
    longest = 0
    current = 0
    previous = None
    for residue in sequence.upper():
        if residue == previous:
            current += 1
        else:
            previous = residue
            current = 1
        longest = max(longest, current)
    return longest


def dry_run_command(args: argparse.Namespace) -> List[str]:
    script_path = Path(__file__).resolve()
    try:
        display_script = str(script_path.relative_to(Path.cwd()))
    except ValueError:
        display_script = script_path.name
    command = ["python", display_script]
    if args.nogpu:
        command.append("--nogpu")
    if args.strict_fasta:
        command.append("--strict-fasta")
    if args.repeat_threshold != 8:
        command.extend(["--repeat-threshold", str(args.repeat_threshold)])
    command.append("--execute")
    command.append(args.mode)
    command.append(args.pdbfile)
    command.extend(["--chain", args.chain])
    if args.multichain_backbone:
        command.append("--multichain-backbone")
    if args.mode == "sample":
        command.extend(["--temperature", str(args.temperature)])
        command.extend(["--num-samples", str(args.num_samples)])
        command.extend(["--outpath", args.outpath])
    else:
        command.append(args.seqfile)
        command.extend(["--outpath", args.outpath])
    return command


def print_dry_run(args: argparse.Namespace) -> None:
    command = dry_run_command(args)
    print("Dry run only; model was not loaded and no output was written.")
    print("Execute command:")
    print(" ".join(shlex.quote(part) for part in command))
    print()
    print(f"Mode: {args.mode}")
    print(f"Structure: {args.pdbfile}")
    print(f"Target chain: {args.chain}")
    print(f"Backbone conditioning: {'multichain' if args.multichain_backbone else 'single-chain'}")
    if args.mode == "sample":
        print(f"Output FASTA: {args.outpath}")
        print(f"Temperature: {args.temperature}")
        print(f"Num samples: {args.num_samples}")
    else:
        print(f"Sequence FASTA: {args.seqfile}")
        print(f"Output CSV: {args.outpath}")


def ensure_execute_inputs(args: argparse.Namespace) -> None:
    structure_path = Path(args.pdbfile)
    if not structure_path.exists():
        raise SystemExit(f"Structure file does not exist: {structure_path}")
    Path(args.outpath).parent.mkdir(parents=True, exist_ok=True)


def load_model(nogpu: bool):
    import torch
    import esm
    import esm.inverse_folding

    model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
    model = model.eval()
    if torch.cuda.is_available() and not nogpu:
        model = model.cuda()
        print("Transferred model to GPU")
    return model, alphabet, torch


def run_sample(args: argparse.Namespace) -> None:
    import numpy as np
    import esm.inverse_folding

    model, alphabet, torch = load_model(args.nogpu)
    if args.multichain_backbone:
        structure = esm.inverse_folding.util.load_structure(args.pdbfile)
        coords, native_seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
        if args.chain not in coords:
            raise SystemExit(f"Chain {args.chain} not found after complex extraction; available chains: {sorted(coords)}")
        native_seq = native_seqs[args.chain]
    else:
        coords, native_seq = esm.inverse_folding.util.load_coords(args.pdbfile, args.chain)

    print("Native sequence loaded from structure file:")
    print(native_seq)
    print(f"Saving sampled sequences to {args.outpath}.")

    with torch.no_grad(), Path(args.outpath).open("w") as output_handle:
        for index in range(args.num_samples):
            print(f"Sampling.. ({index + 1} of {args.num_samples})")
            if args.multichain_backbone:
                sampled_seq = esm.inverse_folding.multichain_util.sample_sequence_in_complex(
                    model, coords, args.chain, temperature=args.temperature
                )
            else:
                device = next(model.parameters()).device
                sampled_seq = model.sample(coords, temperature=args.temperature, device=device)
            output_handle.write(f">sampled_seq_{index + 1}\n{sampled_seq}\n")
            recovery = np.mean([native == sampled for native, sampled in zip(native_seq, sampled_seq)])
            repeat = longest_homopolymer(sampled_seq)
            print(sampled_seq)
            print(f"Sequence recovery: {recovery:.4f}")
            if repeat >= args.repeat_threshold:
                print(
                    f"warning: sampled_seq_{index + 1} has a homopolymer run of length {repeat}",
                    file=sys.stderr,
                )


def run_score(args: argparse.Namespace) -> None:
    import numpy as np
    import esm.inverse_folding

    model, alphabet, torch = load_model(args.nogpu)
    records = read_fasta(Path(args.seqfile))
    validate_fasta_records(records, strict=args.strict_fasta, repeat_threshold=args.repeat_threshold)

    if args.multichain_backbone:
        structure = esm.inverse_folding.util.load_structure(args.pdbfile)
        coords, native_seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
        if args.chain not in coords:
            raise SystemExit(f"Chain {args.chain} not found after complex extraction; available chains: {sorted(coords)}")
        native_seq = native_seqs[args.chain]
        target_len = coords[args.chain].shape[0]
    else:
        coords, native_seq = esm.inverse_folding.util.load_coords(args.pdbfile, args.chain)
        target_len = coords.shape[0]

    print("Native sequence loaded from structure file:")
    print(native_seq)
    print(f"Target chain coordinate length: {target_len}")
    print(f"Scoring {len(records)} FASTA records.")

    with torch.no_grad(), Path(args.outpath).open("w", newline="") as output_handle:
        writer = csv.writer(output_handle)
        writer.writerow(["seqid", "log_likelihood", "log_likelihood_withcoord"])
        for header, sequence in records:
            if len(sequence) != target_len:
                raise SystemExit(
                    f"Sequence length mismatch for {header!r}: FASTA length {len(sequence)} vs target-chain coordinates {target_len}"
                )
            if args.multichain_backbone:
                ll_fullseq, ll_withcoord = esm.inverse_folding.multichain_util.score_sequence_in_complex(
                    model, alphabet, coords, args.chain, sequence
                )
            else:
                ll_fullseq, ll_withcoord = esm.inverse_folding.util.score_sequence(
                    model, alphabet, coords, sequence
                )
            writer.writerow([header, ll_fullseq, ll_withcoord])
            print(f"{header}: log_likelihood={ll_fullseq:.4f}, withcoord={ll_withcoord:.4f}, perplexity={np.exp(-ll_fullseq):.4f}")
    print(f"Results saved to {args.outpath}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    if not args.execute:
        print_dry_run(args)
        return 0
    ensure_execute_inputs(args)
    if args.mode == "sample":
        run_sample(args)
    elif args.mode == "score":
        run_score(args)
    else:
        raise SystemExit(f"Unsupported mode: {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
