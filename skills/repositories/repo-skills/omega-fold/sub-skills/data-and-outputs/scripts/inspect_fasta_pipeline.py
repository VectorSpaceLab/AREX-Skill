#!/usr/bin/env python3
"""Inspect OmegaFold FASTA parsing and PDB-writing behavior without inference.

This helper imports ``omegafold.pipeline`` only after argument parsing, runs
``fasta2inputs`` on CPU, prints sequence/output/tensor details, and optionally
writes a tiny synthetic PDB through ``save_pdb``. It never constructs the
OmegaFold model, loads weights, downloads files, or uses a GPU.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Iterable


DEFAULT_FASTA = ">long/path_BZU\nACDBZU-\n:short\nG\n"
RESTYPES_WITH_X_AND_GAP = "ARNDCQEGHILKMFPSTWYVX-"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect OmegaFold pipeline.fasta2inputs and optionally "
            "pipeline.save_pdb without running model inference or downloading weights."
        )
    )
    parser.add_argument(
        "--fasta",
        type=Path,
        default=None,
        help="Existing FASTA file to inspect. If omitted, a tiny temporary FASTA is created.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory passed to fasta2inputs. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--num-pseudo-msa",
        type=int,
        default=2,
        help="Number of pseudo-MSA rows to request per cycle; target row adds one more row.",
    )
    parser.add_argument(
        "--num-cycle",
        type=int,
        default=2,
        help="Number of cycle dictionaries to generate.",
    )
    parser.add_argument(
        "--mask-rate",
        type=float,
        default=0.12,
        help="Masking threshold used for pseudo-MSA rows.",
    )
    parser.add_argument(
        "--random-mask",
        action="store_true",
        help="Disable deterministic masking. By default, OmegaFold seeds masks by sequence length.",
    )
    parser.add_argument(
        "--write-tiny-pdb",
        action="store_true",
        help="Also write a tiny synthetic atom14 PDB through pipeline.save_pdb.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary directory when --fasta or --output-dir is omitted.",
    )
    return parser.parse_args()


def load_pipeline():
    try:
        import torch
        from omegafold import pipeline
    except Exception as exc:  # pragma: no cover - environment-dependent message
        raise SystemExit(
            "Failed to import OmegaFold pipeline. Install OmegaFold with its "
            "runtime dependencies first; for the legacy torch 1.12 stack, keep "
            f"numpy<2. Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return pipeline, torch


def read_fasta_records(fasta_path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    active_header: str | None = None
    active_parts: list[str] = []
    for raw_line in fasta_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith((">", ":")):
            if active_header is not None:
                records.append((active_header, "".join(active_parts).upper()))
            active_header = line[1:]
            active_parts = []
        elif active_header is None:
            raise SystemExit(f"Malformed FASTA: sequence line before header: {line!r}")
        else:
            active_parts.append(line)
    if active_header is not None:
        records.append((active_header, "".join(active_parts).upper()))
    return records


def normalize_sequence(sequence: str) -> str:
    return sequence.replace("Z", "E").replace("B", "D").replace("U", "C")


def validate_records(records: Iterable[tuple[str, str]]) -> None:
    valid = set(RESTYPES_WITH_X_AND_GAP)
    for header, sequence in records:
        normalized = normalize_sequence(sequence)
        invalid = sorted({aa for aa in normalized if aa not in valid})
        if invalid:
            joined = ", ".join(repr(item) for item in invalid)
            raise SystemExit(
                f"Invalid residue(s) after B/Z/U normalization in {header!r}: {joined}. "
                f"Allowed residues are {RESTYPES_WITH_X_AND_GAP}."
            )


def tensor_shape(value) -> str:
    shape = getattr(value, "shape", None)
    return "[" + ", ".join(str(dim) for dim in shape) + "]" if shape is not None else "<no shape>"


def write_tiny_pdb(pipeline, torch, save_path: Path) -> None:
    sequence = torch.tensor([0, 4, 7], dtype=torch.long)  # A, C, G
    pos14 = torch.zeros((3, 14, 3), dtype=torch.float32)
    residue_offsets = torch.arange(3, dtype=torch.float32).view(3, 1)
    atom_offsets = torch.arange(14, dtype=torch.float32).view(1, 14) * 0.05
    pos14[:, :, 0] = residue_offsets * 3.8 + atom_offsets
    pos14[:, :, 1] = atom_offsets
    b_factors = torch.tensor([95.0, 70.0, 40.0], dtype=torch.float32)
    mask = torch.ones(3, dtype=torch.float32)
    pipeline.save_pdb(pos14, b_factors, sequence, mask, str(save_path), model=0)


def main() -> int:
    args = parse_args()
    pipeline, torch = load_pipeline()

    with tempfile.TemporaryDirectory(prefix="omegafold-data-check-") as temp_name:
        temp_dir = Path(temp_name)
        fasta_path = args.fasta or temp_dir / "tiny_input.fasta"
        output_dir = args.output_dir or temp_dir / "outputs"

        if args.fasta is None:
            fasta_path.write_text(DEFAULT_FASTA)
            print(f"created_tiny_fasta={fasta_path}")

        records = read_fasta_records(fasta_path)
        validate_records(records)
        sorted_records = sorted(records, key=lambda item: len(item[1]))
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"fasta={fasta_path}")
        print(f"record_count={len(records)}")
        print(f"output_dir={output_dir}")
        print("output_dir_created_or_exists=True")

        for sorted_index, (header, sequence) in enumerate(sorted_records):
            normalized = normalize_sequence(sequence)
            indices = [RESTYPES_WITH_X_AND_GAP.index(aa) for aa in normalized]
            print(f"record[{sorted_index}].header={header}")
            print(f"record[{sorted_index}].length={len(sequence)}")
            print(f"record[{sorted_index}].normalized={normalized}")
            print(f"record[{sorted_index}].indices={indices}")

        yielded = list(
            pipeline.fasta2inputs(
                str(fasta_path),
                output_dir=str(output_dir),
                num_pseudo_msa=args.num_pseudo_msa,
                device=torch.device("cpu"),
                mask_rate=args.mask_rate,
                num_cycle=args.num_cycle,
                deterministic=not args.random_mask,
            )
        )

        print(f"yield_count={len(yielded)}")
        for item_index, (input_data, save_path) in enumerate(yielded):
            print(f"yield[{item_index}].pdb={save_path}")
            print(f"yield[{item_index}].cycles={len(input_data)}")
            for cycle_index, cycle in enumerate(input_data):
                p_msa = cycle["p_msa"]
                p_msa_mask = cycle["p_msa_mask"]
                target_row = p_msa[0].detach().cpu().tolist()
                print(f"yield[{item_index}].cycle[{cycle_index}].p_msa_shape={tensor_shape(p_msa)}")
                print(f"yield[{item_index}].cycle[{cycle_index}].p_msa_mask_shape={tensor_shape(p_msa_mask)}")
                if cycle_index == 0:
                    print(f"yield[{item_index}].target_indices={target_row}")

        if args.write_tiny_pdb:
            tiny_pdb = output_dir / "tiny_save_pdb_check.pdb"
            write_tiny_pdb(pipeline, torch, tiny_pdb)
            atom_count = sum(1 for line in tiny_pdb.read_text().splitlines() if line.startswith("ATOM"))
            print(f"tiny_pdb={tiny_pdb}")
            print(f"tiny_pdb_atom_count={atom_count}")

        if args.keep_temp and (args.fasta is None or args.output_dir is None):
            kept_dir = Path(tempfile.mkdtemp(prefix="omegafold-data-kept-"))
            for path in temp_dir.rglob("*"):
                target = kept_dir / path.relative_to(temp_dir)
                if path.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.read_bytes())
            print(f"kept_temp_dir={kept_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
