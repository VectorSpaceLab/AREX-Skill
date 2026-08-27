#!/usr/bin/env python3
"""Convert PDB/mmCIF structures into SaProt AA+3Di sequences.

This script is a standalone adaptation of SaProt's structure-sequence
conversion pattern. It does not import SaProt repository modules.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, Iterable, List, Optional, Tuple


Record = Tuple[str, str, str]


class ConversionError(RuntimeError):
    """Raised for user-actionable conversion failures."""


def parse_bool_mode(value: str) -> str:
    normalized = value.lower()
    if normalized not in {"auto", "true", "false"}:
        raise argparse.ArgumentTypeError("expected one of: auto, true, false")
    return normalized


def resolve_foldseek(foldseek: str) -> str:
    candidate = Path(foldseek).expanduser()
    if candidate.exists():
        if not candidate.is_file():
            raise ConversionError(f"Foldseek path is not a file: {candidate}")
        if not os.access(candidate, os.X_OK):
            raise ConversionError(f"Foldseek path is not executable: {candidate}")
        return str(candidate)

    found = shutil.which(foldseek)
    if found:
        return found

    raise ConversionError(
        "Foldseek executable not found. Put foldseek on PATH and pass --foldseek foldseek, "
        "or pass the executable file location supplied by the user."
    )


def resolve_structure(path: str) -> Path:
    structure = Path(path).expanduser()
    if not structure.exists():
        raise ConversionError(f"Structure path not found: {structure}")
    if not structure.is_file():
        raise ConversionError(f"Structure path is not a file: {structure}")
    return structure


def should_auto_mask(structure: Path) -> bool:
    try:
        text = structure.read_text(errors="ignore")
    except OSError as exc:
        raise ConversionError(f"Could not read structure for pLDDT auto-detection: {exc}") from exc
    return "alphafold" in text.lower()


def extract_plddt(structure_path: Path, chain_id: str) -> "object":
    try:
        import numpy as np
    except ImportError as exc:
        raise ConversionError(
            "pLDDT masking requires numpy. Install numpy or rerun with --plddt-mask false."
        ) from exc

    try:
        from Bio.PDB import MMCIFParser, PDBParser
    except ImportError as exc:
        raise ConversionError(
            "pLDDT masking requires biopython. Install biopython or rerun with --plddt-mask false."
        ) from exc

    suffix = structure_path.suffix.lower()
    if suffix in {".cif", ".mmcif"}:
        parser = MMCIFParser(QUIET=True)
    elif suffix == ".pdb":
        parser = PDBParser(QUIET=True)
    else:
        raise ConversionError(
            "pLDDT extraction only supports .pdb, .cif, and .mmcif structure files."
        )

    try:
        structure = parser.get_structure("protein", str(structure_path))
        model = structure[0]
        chain = model[chain_id]
    except Exception as exc:  # Bio.PDB raises several parser/key exception types.
        raise ConversionError(f"Bio.PDB could not parse chain {chain_id!r} for pLDDT: {exc}") from exc

    plddts = []
    for residue in chain:
        atom_scores = [atom.get_bfactor() for atom in residue]
        if atom_scores:
            plddts.append(float(np.mean(atom_scores)))

    return np.array(plddts, dtype=float)


def run_foldseek(
    foldseek: str,
    structure: Path,
    output_tsv: Path,
    verbose: bool,
) -> None:
    command = [
        foldseek,
        "structureto3didescriptor",
        "--threads",
        "1",
        "--chain-name-mode",
        "1",
    ]
    if not verbose:
        command.extend(["-v", "0"])
    command.extend([str(structure), str(output_tsv)])

    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ConversionError(
            "Foldseek executable could not be launched. Check --foldseek and PATH."
        ) from exc
    except OSError as exc:
        raise ConversionError(f"Foldseek launch failed: {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if detail:
            raise ConversionError(f"Foldseek failed with exit code {completed.returncode}: {detail}")
        raise ConversionError(f"Foldseek failed with exit code {completed.returncode}.")

    if not output_tsv.exists() or output_tsv.stat().st_size == 0:
        raise ConversionError(
            "Foldseek produced no descriptor output. Confirm the structure contains a valid protein chain."
        )


def derive_chain_id(description: str, structure_name: str) -> str:
    name_chain = description.split(" ", 1)[0]
    without_name = name_chain.replace(structure_name, "")
    return without_name.split("_")[-1]


def combine_sequence(aa_sequence: str, foldseek_sequence: str) -> str:
    return "".join(
        amino_acid + structure_token.lower()
        for amino_acid, structure_token in zip(aa_sequence, foldseek_sequence)
    )


def apply_plddt_mask(
    structure: Path,
    chain_id: str,
    foldseek_sequence: str,
    threshold: float,
    warnings: List[str],
) -> str:
    try:
        plddts = extract_plddt(structure, chain_id)
        if len(plddts) != len(foldseek_sequence):
            raise ConversionError(
                f"pLDDT length mismatch for chain {chain_id}: "
                f"{len(plddts)} pLDDT values != {len(foldseek_sequence)} 3Di positions"
            )

        masked = list(foldseek_sequence)
        for index, score in enumerate(plddts):
            if score < threshold:
                masked[index] = "#"
        return "".join(masked)
    except ConversionError as exc:
        warnings.append(str(exc))
        return foldseek_sequence


def get_struc_seq(
    foldseek: str,
    path: str,
    chains: Optional[Iterable[str]] = None,
    plddt_mask: str = "auto",
    plddt_threshold: float = 70.0,
    foldseek_verbose: bool = False,
) -> Tuple[Dict[str, Record], List[str], List[str]]:
    foldseek_executable = resolve_foldseek(foldseek)
    structure = resolve_structure(path)
    requested_chains = set(chains) if chains else None
    warnings: List[str] = []

    if plddt_mask == "auto":
        mask_enabled = should_auto_mask(structure)
    else:
        mask_enabled = plddt_mask == "true"

    with tempfile.TemporaryDirectory(prefix="saprot_structure_sequence_") as temp_dir:
        output_tsv = Path(temp_dir) / "foldseek.tsv"
        run_foldseek(foldseek_executable, structure, output_tsv, foldseek_verbose)

        records: Dict[str, Record] = {}
        available_chains: List[str] = []
        structure_name = structure.name

        with output_tsv.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    warnings.append(f"Skipping malformed Foldseek line {line_number}: fewer than 3 columns")
                    continue

                description, aa_sequence, foldseek_sequence = parts[:3]
                chain_id = derive_chain_id(description, structure_name)
                if chain_id not in available_chains:
                    available_chains.append(chain_id)

                if requested_chains is not None and chain_id not in requested_chains:
                    continue
                if chain_id in records:
                    continue

                processed_foldseek = foldseek_sequence
                if mask_enabled:
                    processed_foldseek = apply_plddt_mask(
                        structure,
                        chain_id,
                        processed_foldseek,
                        plddt_threshold,
                        warnings,
                    )

                processed_foldseek = processed_foldseek.lower()
                combined = combine_sequence(aa_sequence, processed_foldseek)
                records[chain_id] = (aa_sequence, processed_foldseek, combined)

    if not records:
        requested = sorted(requested_chains) if requested_chains else None
        if requested:
            raise ConversionError(
                "No requested chains were found. "
                f"Requested chains: {requested}; available chains: {available_chains}"
            )
        raise ConversionError("No chains were parsed from Foldseek descriptor output.")

    return records, available_chains, warnings


def write_json(
    output_path: Path,
    structure: Path,
    requested_chains: Optional[List[str]],
    plddt_mask: str,
    threshold: float,
    records: Dict[str, Record],
    available_chains: List[str],
    warnings: List[str],
) -> None:
    payload = {
        "structure": str(structure),
        "requested_chains": requested_chains,
        "available_chains": available_chains,
        "plddt_mask": plddt_mask,
        "plddt_threshold": threshold,
        "warnings": warnings,
        "chains": {
            chain_id: {
                "aa": values[0],
                "foldseek": values[1],
                "combined": values[2],
                "length": len(values[0]),
            }
            for chain_id, values in records.items()
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_fasta(output_path: Path, records: Dict[str, Record], seq_type: str) -> None:
    index = {"aa": 0, "foldseek": 1, "combined": 2}[seq_type]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chain_id, values in records.items():
            handle.write(f">{chain_id}|{seq_type}\n{values[index]}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a PDB/mmCIF protein structure into SaProt AA, 3Di, or combined AA+3Di sequences.",
    )
    parser.add_argument(
        "--foldseek",
        required=True,
        help="Foldseek executable path, or command name if foldseek is on PATH.",
    )
    parser.add_argument(
        "--structure",
        required=True,
        help="Input .pdb, .cif, or .mmcif structure file.",
    )
    parser.add_argument(
        "--chain",
        action="append",
        default=None,
        help="Chain ID to emit. Repeat for multiple chains. Omit to emit all Foldseek chains.",
    )
    parser.add_argument(
        "--plddt-mask",
        type=parse_bool_mode,
        default="auto",
        metavar="{auto,true,false}",
        help="Mask low-confidence pLDDT positions with '#': auto, true, or false. Default: auto.",
    )
    parser.add_argument(
        "--plddt-threshold",
        type=float,
        default=70.0,
        help="pLDDT threshold below which 3Di tokens are replaced with '#'. Default: 70.0.",
    )
    parser.add_argument(
        "--output-json",
        help="Write a JSON report containing AA, Foldseek, combined sequences, chain lists, and warnings.",
    )
    parser.add_argument(
        "--output-fasta",
        help="Write selected sequence type as FASTA.",
    )
    parser.add_argument(
        "--seq-type",
        choices=["combined", "aa", "foldseek"],
        default="combined",
        help="Sequence type to write to FASTA. Default: combined.",
    )
    parser.add_argument(
        "--foldseek-verbose",
        action="store_true",
        help="Allow Foldseek to print normal diagnostic verbosity.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.output_json and not args.output_fasta:
        parser.error("at least one of --output-json or --output-fasta is required")

    try:
        records, available_chains, warnings = get_struc_seq(
            foldseek=args.foldseek,
            path=args.structure,
            chains=args.chain,
            plddt_mask=args.plddt_mask,
            plddt_threshold=args.plddt_threshold,
            foldseek_verbose=args.foldseek_verbose,
        )
        structure = resolve_structure(args.structure)

        if args.output_json:
            write_json(
                Path(args.output_json).expanduser(),
                structure,
                args.chain,
                args.plddt_mask,
                args.plddt_threshold,
                records,
                available_chains,
                warnings,
            )
        if args.output_fasta:
            write_fasta(Path(args.output_fasta).expanduser(), records, args.seq_type)

        if warnings:
            for warning in warnings:
                print(f"warning: {warning}", file=sys.stderr)
        return 0
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
