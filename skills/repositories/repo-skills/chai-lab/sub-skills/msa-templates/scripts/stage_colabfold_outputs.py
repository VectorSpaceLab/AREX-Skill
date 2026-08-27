#!/usr/bin/env python3
"""Stage local ColabFold outputs into Chai-ready MSA/template inputs.

This helper reads a ColabFold output tree and writes, for each sequence id, a
Chai FASTA file, Chai .aligned.pqt files, and a remapped all_template_hits.m8.
It does not call any network service or run Chai inference.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MSA_COLUMNS = ["sequence", "source_database", "pairing_key", "comment"]
M8_COLUMNS = [
    "query_id",
    "subject_id",
    "pident",
    "length",
    "mismatch",
    "gapopen",
    "query_start",
    "query_end",
    "subject_start",
    "subject_end",
    "evalue",
    "bitscore",
    "comment",
]
CHAIN_VOCAB = [*string.ascii_uppercase, *string.ascii_lowercase]
CHAIN_VOCAB = CHAIN_VOCAB + [first + second for first in CHAIN_VOCAB for second in CHAIN_VOCAB]


@dataclass(frozen=True)
class FastaRecord:
    header: str
    sequence: str


def chain_letter(one_indexed_asym_id: int) -> str:
    if one_indexed_asym_id <= 0 or one_indexed_asym_id > len(CHAIN_VOCAB):
        raise ValueError(f"chain index {one_indexed_asym_id} is outside supported range")
    return CHAIN_VOCAB[one_indexed_asym_id - 1]


def hash_sequence(sequence: str) -> str:
    return hashlib.sha256(sequence.encode()).hexdigest()


def expected_basename(query_sequence: str) -> str:
    return f"{hash_sequence(query_sequence.upper())}.aligned.pqt"


def read_fasta_text(text: str) -> list[FastaRecord]:
    records: list[FastaRecord] = []
    header: str | None = None
    sequence_parts: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(header=header, sequence="".join(sequence_parts)))
            header = line[1:].strip()
            sequence_parts = []
        else:
            if header is None:
                raise ValueError("FASTA sequence line appears before the first header")
            sequence_parts.append(line)
    if header is not None:
        records.append(FastaRecord(header=header, sequence="".join(sequence_parts)))
    if not records:
        raise ValueError("FASTA block contains no records")
    return records


def read_colabfold_a3m(path: Path) -> dict[str, list[FastaRecord]]:
    text = path.read_text()
    blocks = [block for block in text.split("\x00") if block]
    if not blocks and text.strip():
        blocks = [text]
    result: dict[str, list[FastaRecord]] = {}
    for block in blocks:
        records = read_fasta_text(block)
        query_id = records[0].header
        if not query_id.isdigit() or len(query_id) != 3:
            raise ValueError(f"expected ColabFold numeric query header like 101 in {path}, got {query_id!r}")
        result[query_id] = records
    return result


def write_fastas(records: Iterable[FastaRecord], path: Path) -> None:
    with path.open("w") as handle:
        for record in records:
            handle.write(f">{record.header}\n")
            handle.write(f"{record.sequence}\n")


def is_padding_msa_row(sequence: str) -> bool:
    return bool(sequence) and set(sequence) == {"-"}


def read_colabfold_inputs(path: Path) -> dict[str, list[FastaRecord]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["id", "sequence"]:
            raise ValueError(f"{path} must have exactly the columns: id, sequence")
        result: dict[str, list[FastaRecord]] = {}
        for row in reader:
            identifier = row["id"]
            sequences = row["sequence"].split(":")
            if not identifier or not all(sequences):
                raise ValueError(f"invalid row in {path}: {row}")
            result[identifier] = [
                FastaRecord(header=f"protein|{chain_letter(index)}", sequence=sequence)
                for index, sequence in enumerate(sequences, start=1)
            ]
    if not result:
        raise ValueError(f"{path} contains no sequence rows")
    return result


def require_pandas():
    try:
        import pandas as pd
    except ImportError as import_error:  # pragma: no cover - exercised by users without pandas
        raise RuntimeError(
            "pandas is required to write .aligned.pqt and parse m8 files. Install Chai Lab or pandas with a parquet engine."
        ) from import_error
    return pd


def validate_aligned_table(table) -> None:
    if list(table.columns) != MSA_COLUMNS:
        raise ValueError(f"aligned table columns must be {MSA_COLUMNS}, got {list(table.columns)}")
    if table.empty:
        raise ValueError("aligned table is empty")
    if table.iloc[0]["source_database"] != "query":
        raise ValueError("first aligned table row must have source_database=query")
    if int((table["source_database"] == "query").sum()) != 1:
        raise ValueError("aligned table must contain exactly one query row")
    if table.isnull().any().any():
        raise ValueError("aligned table contains null values")


def gather_colabfold_msas(colabfold_out_dir: Path, identifier: str, output_folder: Path) -> dict[str, str]:
    pd = require_pandas()
    output_folder.mkdir(parents=True, exist_ok=True)
    paired_path = colabfold_out_dir / f"{identifier}_pairgreedy" / "pair.a3m"
    uniref_path = colabfold_out_dir / f"{identifier}_env" / "uniref.a3m"
    env_path = colabfold_out_dir / f"{identifier}_env" / "bfd.mgnify30.metaeuk30.smag30.a3m"
    for required_path in [paired_path, uniref_path, env_path]:
        if not required_path.is_file():
            raise FileNotFoundError(f"required ColabFold MSA file is missing: {required_path}")

    paired_msa = read_colabfold_a3m(paired_path)
    paired_lengths = {len(records) for records in paired_msa.values()}
    if len(paired_lengths) != 1:
        raise ValueError(f"{paired_path} has inconsistent paired MSA row counts")
    logging.info("[%s] ColabFold paired MSA rows per chain: %s", identifier, paired_lengths.pop())

    uniref_msa = read_colabfold_a3m(uniref_path)
    env_msa = read_colabfold_a3m(env_path)
    if set(uniref_msa) != set(env_msa) or set(uniref_msa) != set(paired_msa):
        raise ValueError(f"{identifier} MSA query IDs differ between pair, uniref, and env A3M files")

    colabfold_id_to_sequence: dict[str, str] = {}
    for query_id in paired_msa:
        query_sequence = uniref_msa[query_id][0].sequence
        rows: list[dict[str, str]] = []

        for row_index, record in enumerate(paired_msa[query_id]):
            if is_padding_msa_row(record.sequence):
                continue
            rows.append(
                {
                    "sequence": record.sequence,
                    "source_database": "query" if row_index == 0 else "uniref90",
                    "pairing_key": "" if row_index == 0 else str(row_index),
                    "comment": record.header,
                }
            )

        paired_sequences = {row["sequence"] for row in rows[1:]}
        for record in uniref_msa[query_id][1:]:
            if not is_padding_msa_row(record.sequence) and record.sequence not in paired_sequences:
                rows.append(
                    {
                        "sequence": record.sequence,
                        "source_database": "uniref90",
                        "pairing_key": "",
                        "comment": record.header,
                    }
                )

        for record in env_msa[query_id][1:]:
            if not is_padding_msa_row(record.sequence) and record.sequence not in paired_sequences:
                rows.append(
                    {
                        "sequence": record.sequence,
                        "source_database": "bfd_uniclust",
                        "pairing_key": "",
                        "comment": record.header,
                    }
                )

        table = pd.DataFrame.from_records(rows, columns=MSA_COLUMNS)
        validate_aligned_table(table)
        output_path = output_folder / expected_basename(query_sequence)
        table.to_parquet(output_path)
        colabfold_id_to_sequence[query_id] = query_sequence
        logging.info("[%s] wrote %s with %d MSA rows", identifier, output_path.name, len(table))

    return colabfold_id_to_sequence


def parse_m8_file(path: Path):
    pd = require_pandas()
    if not path.is_file():
        raise FileNotFoundError(f"required template m8 file is missing: {path}")
    table = pd.read_csv(path, delimiter="\t", header=None, names=M8_COLUMNS)
    for column in ["query_start", "query_end", "subject_start", "subject_end"]:
        table[column] = table[column].astype(int)
    return table.sort_values(by=["query_id", "evalue"])


def gather_colabfold_templates(
    colabfold_out_dir: Path,
    identifier: str,
    chain_id_mapping: dict[str, str],
    output_folder: Path,
) -> Path:
    template_file = colabfold_out_dir / f"{identifier}_env" / "pdb70.m8"
    templates = parse_m8_file(template_file)

    def remap_query_id(value: object) -> str:
        key = str(value)
        if key not in chain_id_mapping:
            raise KeyError(f"template query id {key!r} is not present in staged MSA mapping")
        return chain_id_mapping[key]

    templates["query_id"] = templates["query_id"].apply(remap_query_id)
    output_path = output_folder / "all_template_hits.m8"
    templates.to_csv(output_path, sep="\t", index=False, header=False)
    logging.info("[%s] wrote %s with %d template rows", identifier, output_path.name, len(templates))
    return output_path


def find_sequences_csv(colabfold_out_dir: Path, explicit_csv: Path | None) -> Path:
    if explicit_csv is not None:
        if not explicit_csv.is_file():
            raise FileNotFoundError(f"specified sequences CSV does not exist: {explicit_csv}")
        return explicit_csv
    csv_files = sorted(colabfold_out_dir.glob("*.csv"))
    if len(csv_files) != 1:
        raise ValueError(f"expected exactly one CSV file in {colabfold_out_dir}, found {len(csv_files)}")
    return csv_files[0]


def ensure_output_folder(path: Path, *, force: bool) -> None:
    if path.exists() and any(path.iterdir()) and not force:
        raise FileExistsError(f"output folder already exists and is not empty: {path}; pass --force to overwrite staged files")
    path.mkdir(parents=True, exist_ok=True)


def stage_outputs(colabfold_out_dir: Path, chai_dir: Path, *, sequences_csv: Path | None, force: bool) -> list[Path]:
    if not colabfold_out_dir.is_dir():
        raise NotADirectoryError(f"ColabFold output directory does not exist: {colabfold_out_dir}")
    csv_path = find_sequences_csv(colabfold_out_dir, sequences_csv)
    fasta_entries = read_colabfold_inputs(csv_path)
    staged_folders: list[Path] = []

    for identifier, sequences in fasta_entries.items():
        chai_output_folder = chai_dir / identifier
        ensure_output_folder(chai_output_folder, force=force)

        colabfold_id_to_sequence = gather_colabfold_msas(
            colabfold_out_dir=colabfold_out_dir,
            identifier=identifier,
            output_folder=chai_output_folder / "msas",
        )
        expected_sequences = {record.sequence for record in sequences}
        observed_sequences = set(colabfold_id_to_sequence.values())
        if observed_sequences != expected_sequences:
            raise ValueError(
                f"{identifier} staged MSA query sequences do not match sequences.csv: "
                f"observed={sorted(observed_sequences)} expected={sorted(expected_sequences)}"
            )

        colabfold_id_to_chai_id: dict[str, str] = {}
        for colabfold_id, sequence in colabfold_id_to_sequence.items():
            matches = [record for record in sequences if record.sequence == sequence]
            if not matches:
                raise ValueError(f"no Chai FASTA sequence matches ColabFold query {colabfold_id}")
            colabfold_id_to_chai_id[colabfold_id] = matches[0].header.split("|", maxsplit=1)[-1]

        gather_colabfold_templates(
            colabfold_out_dir=colabfold_out_dir,
            identifier=identifier,
            chain_id_mapping=colabfold_id_to_chai_id,
            output_folder=chai_output_folder,
        )
        write_fastas(sequences, chai_output_folder / "chai.fasta")
        staged_folders.append(chai_output_folder)
        logging.info("[%s] staged Chai inputs under %s", identifier, chai_output_folder)

    return staged_folders


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage an existing ColabFold output directory into Chai-ready local inputs: "
            "chai.fasta, msas/*.aligned.pqt, and all_template_hits.m8."
        )
    )
    parser.add_argument("colabfold_out_dir", type=Path, help="ColabFold output directory containing sequences.csv and <id>_env/<id>_pairgreedy subfolders.")
    parser.add_argument("chai_dir", type=Path, help="Destination directory for staged Chai input folders.")
    parser.add_argument("--sequences-csv", type=Path, default=None, help="Explicit sequences.csv path. Defaults to the single *.csv file in colabfold_out_dir.")
    parser.add_argument("--force", action="store_true", help="Allow writing into existing non-empty staged output folders.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    try:
        staged_folders = stage_outputs(
            args.colabfold_out_dir,
            args.chai_dir,
            sequences_csv=args.sequences_csv,
            force=args.force,
        )
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print("Staged Chai input folders:")
    for folder in staged_folders:
        print(f"  {folder}")
        print(f"    fold command: chai-lab fold {folder / 'chai.fasta'} OUTPUT_DIR --msa-directory {folder / 'msas'} --template-hits-path {folder / 'all_template_hits.m8'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
