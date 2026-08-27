#!/usr/bin/env python3
"""Validate OpenFold inference inputs without importing or running OpenFold."""

from __future__ import print_function

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


MONOMER_REQUIRED_ANY = (
    ("BFD/clustered A3M", ("bfd_uniclust_hits.a3m", "bfd_uniref_hits.a3m")),
    ("MGnify Stockholm", ("mgnify_hits.sto",)),
    ("UniRef90 Stockholm", ("uniref90_hits.sto",)),
)

MONOMER_TEMPLATE_ANY = (
    "hhsearch_output.hhr",
    "pdb70_hits.hhr",
)

MULTIMER_HINT_FILES = (
    "uniprot_hits.sto",
    "uniprot_hits.a3m",
    "hmm_output.sto",
    "pdb_seqres_hits.sto",
    "uniref30_hits.a3m",
    "uniref30_hits.sto",
)

EMBEDDING_SUFFIXES = (
    ".pt",
    ".npy",
    ".npz",
    ".pkl",
    ".pickle",
)

ALLOWED_FASTA_SUFFIXES = (".fa", ".fasta", ".faa", ".fna")
ALLOWED_MMCIF_SUFFIXES = (".cif", ".mmcif")
ALLOWED_RESIDUES = set("ABCDEFGHIKLMNPQRSTVWXYZUO-*.")


@dataclass
class FastaRecord:
    path: Path
    header: str
    sequence: str

    @property
    def tag(self):
        return self.header.split()[0]


class Reporter:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.notes = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def note(self, message):
        self.notes.append(message)

    def print(self):
        for note in self.notes:
            print("ok: " + note)
        for warning in self.warnings:
            print("warning: " + warning, file=sys.stderr)
        for error in self.errors:
            print("error: " + error, file=sys.stderr)


def read_fasta(path, reporter):
    records = []
    header = None
    chunks = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        reporter.error("FASTA is not UTF-8 text: {}".format(path))
        return records
    except OSError as exc:
        reporter.error("cannot read FASTA {}: {}".format(path, exc))
        return records

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(path, header, "".join(chunks).upper()))
            header = line[1:].strip()
            chunks = []
            if not header:
                reporter.error("empty FASTA header in {} at line {}".format(path, line_number))
        else:
            if header is None:
                reporter.error("sequence line before first FASTA header in {} at line {}".format(path, line_number))
                continue
            sequence = "".join(line.split()).upper()
            invalid = sorted(set(sequence) - ALLOWED_RESIDUES)
            if invalid:
                reporter.warn("{} line {} contains unusual residue symbols: {}".format(path, line_number, "".join(invalid)))
            chunks.append(sequence.replace("-", "").replace("*", "").replace(".", ""))

    if header is not None:
        records.append(FastaRecord(path, header, "".join(chunks).upper()))
    if not records:
        reporter.error("no FASTA records found in {}".format(path))
    for record in records:
        if not record.sequence:
            reporter.error("empty sequence for record {!r} in {}".format(record.header, path))
    return records


def collect_fasta_records(fasta_dir, reporter):
    if not fasta_dir.exists():
        reporter.error("FASTA directory does not exist: {}".format(fasta_dir))
        return []
    if not fasta_dir.is_dir():
        reporter.error("FASTA path is not a directory: {}".format(fasta_dir))
        return []

    fasta_files = sorted(
        path for path in fasta_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_FASTA_SUFFIXES
    )
    if not fasta_files:
        reporter.error("no FASTA files with {} suffixes found in {}".format("/".join(ALLOWED_FASTA_SUFFIXES), fasta_dir))
        return []

    records = []
    for fasta_file in fasta_files:
        records.extend(read_fasta(fasta_file, reporter))
    if records:
        reporter.note("found {} FASTA record(s) across {} file(s)".format(len(records), len(fasta_files)))
    return records


def validate_template_dir(template_dir, reporter, skip_templates):
    if not template_dir.exists():
        reporter.error("template mmCIF directory does not exist: {}".format(template_dir))
        return
    if not template_dir.is_dir():
        reporter.error("template mmCIF path is not a directory: {}".format(template_dir))
        return
    cif_files = sorted(
        path for path in template_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_MMCIF_SUFFIXES
    )
    if cif_files:
        reporter.note("found {} template mmCIF file(s)".format(len(cif_files)))
    elif skip_templates:
        reporter.warn("template directory contains no .cif/.mmcif files; accepted because templates are being skipped")
    else:
        reporter.warn("template directory contains no .cif/.mmcif files; this is valid only for intentional template-free workflows")


def candidate_alignment_dirs(root, record):
    candidates = []
    for name in (record.tag, record.path.stem):
        candidate = root / name
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def choose_alignment_dir(root, record):
    for candidate in candidate_alignment_dirs(root, record):
        if candidate.is_dir():
            return candidate
    return None


def validate_monomer_alignment_dir(directory, reporter, skip_templates):
    filenames = {path.name for path in directory.iterdir() if path.is_file()}
    for label, choices in MONOMER_REQUIRED_ANY:
        if not any(name in filenames for name in choices):
            reporter.error("{} is missing {}; expected one of: {}".format(directory, label, ", ".join(choices)))
    if not skip_templates and not any(name in filenames for name in MONOMER_TEMPLATE_ANY):
        reporter.warn("{} has no recognized template hit file ({})".format(directory, ", ".join(MONOMER_TEMPLATE_ANY)))


def validate_multimer_alignment_dir(directory, reporter, skip_templates):
    filenames = {path.name for path in directory.rglob("*") if path.is_file()}
    if not filenames:
        reporter.error("{} contains no alignment files".format(directory))
        return
    if not any(name in filenames for name in ("uniref90_hits.sto", "mgnify_hits.sto")):
        reporter.warn("{} does not show common UniRef90/MGnify files; verify the multimer alignment layout".format(directory))
    if not any(name in filenames for name in MULTIMER_HINT_FILES):
        reporter.warn("{} does not show multimer-specific hint files such as UniProt/HMM/PDB SeqRes hits".format(directory))
    if not skip_templates:
        has_template_hint = any(
            (name.endswith(".hhr") or name.endswith(".sto")) and ("hmm" in name.lower() or "seqres" in name.lower())
            for name in filenames
        )
        if not has_template_hint:
            reporter.warn("{} has no obvious HMMSearch/PDB SeqRes template hit file".format(directory))


def validate_soloseq_alignment_dir(directory, reporter, skip_templates):
    files = [path for path in directory.rglob("*") if path.is_file()]
    if not files:
        reporter.error("{} contains no SoloSeq embedding/template files".format(directory))
        return
    if not any(path.suffix.lower() in EMBEDDING_SUFFIXES for path in files):
        reporter.warn("{} has no obvious embedding artifact with suffix {}".format(directory, ", ".join(EMBEDDING_SUFFIXES)))
    if not skip_templates and not any(path.suffix.lower() == ".hhr" for path in files):
        reporter.warn("{} has no .hhr template hit file; pass --skip-templates if template-free SoloSeq is intentional".format(directory))


def validate_precomputed_alignments(args, records, reporter):
    if not args.precomputed_alignments:
        reporter.note("no precomputed alignment directory supplied; command must generate alignments or embeddings at runtime")
        return
    root = Path(args.precomputed_alignments)
    if not root.exists():
        reporter.error("precomputed alignment directory does not exist: {}".format(root))
        return
    if not root.is_dir():
        reporter.error("precomputed alignment path is not a directory: {}".format(root))
        return

    matched = 0
    for record in records:
        alignment_dir = choose_alignment_dir(root, record)
        if alignment_dir is None:
            expected = ", ".join(str(path) for path in candidate_alignment_dirs(root, record))
            reporter.error("no precomputed alignment/embedding subdirectory for FASTA record {!r}; checked {}".format(record.header, expected))
            continue
        matched += 1
        if args.mode == "multimer":
            validate_multimer_alignment_dir(alignment_dir, reporter, args.skip_templates)
        elif args.mode == "soloseq":
            validate_soloseq_alignment_dir(alignment_dir, reporter, args.skip_templates)
        else:
            validate_monomer_alignment_dir(alignment_dir, reporter, args.skip_templates)
    if matched:
        reporter.note("matched precomputed alignment/embedding directories for {} FASTA record(s)".format(matched))


def validate_soloseq_lengths(records, reporter):
    for record in records:
        length = len(record.sequence)
        if length > 1022:
            reporter.error("SoloSeq record {!r} in {} has length {}, exceeding the 1022-residue ESM-1b limit".format(record.header, record.path, length))
        else:
            reporter.note("SoloSeq record {!r} length {} is within the 1022-residue limit".format(record.header, length))


def validate_checkpoint(path_text, reporter):
    if not path_text:
        return
    path = Path(path_text)
    if not path.exists():
        reporter.error("checkpoint path does not exist: {}".format(path))
        return
    if path.is_file() and path.suffix.lower() not in (".pt", ".npz", ".ckpt"):
        reporter.warn("checkpoint file has an unusual suffix for OpenFold planning: {}".format(path.name))
    reporter.note("checkpoint path exists: {}".format(path))


def validate_custom_template_shape(template_dir, records, reporter):
    cif_files = sorted(path for path in template_dir.iterdir() if path.is_file() and path.suffix.lower() in ALLOWED_MMCIF_SUFFIXES) if template_dir.exists() and template_dir.is_dir() else []
    if not cif_files:
        reporter.warn("--use-custom-template was requested but no .cif/.mmcif files were found")
    if len(records) > 1:
        reporter.warn("custom-template mode applies the same template collection to every query; split runs if templates differ per query")
    reporter.warn("custom-template length and chain-A compatibility require mmCIF parsing; confirm chain A and query/template lengths before real inference")


def validate_run(args, reporter):
    records = collect_fasta_records(Path(args.fasta_dir), reporter)
    template_dir = Path(args.template_mmcif_dir)
    validate_template_dir(template_dir, reporter, args.skip_templates)

    if args.mode == "monomer" and records:
        records_by_file = {}
        for record in records:
            records_by_file.setdefault(record.path, 0)
            records_by_file[record.path] += 1
        for fasta_path, count in sorted(records_by_file.items()):
            if count > 1:
                reporter.warn("monomer FASTA file {} contains {} records; OpenFold will treat multiple records as a complex-like multi-sequence input unless multimer is enabled".format(fasta_path, count))
    if args.mode == "multimer" and records and len(records) == 1:
        reporter.warn("multimer mode saw only one FASTA record; confirm the FASTA encodes all complex chains as intended")
    if args.mode == "soloseq" and records:
        validate_soloseq_lengths(records, reporter)

    if args.use_custom_template and records:
        validate_custom_template_shape(template_dir, records, reporter)
    validate_precomputed_alignments(args, records, reporter)
    validate_checkpoint(args.checkpoint, reporter)


def validate_threading(args, reporter):
    fasta_path = Path(args.input_fasta)
    mmcif_path = Path(args.input_mmcif)
    if not fasta_path.exists() or not fasta_path.is_file():
        reporter.error("threading FASTA file does not exist or is not a file: {}".format(fasta_path))
    else:
        records = read_fasta(fasta_path, reporter)
        if len(records) != 1:
            reporter.error("thread_sequence.py expects exactly one FASTA record, found {}".format(len(records)))
        elif records[0].sequence:
            reporter.note("threading FASTA contains one sequence of length {}".format(len(records[0].sequence)))
    if not mmcif_path.exists() or not mmcif_path.is_file():
        reporter.error("threading mmCIF file does not exist or is not a file: {}".format(mmcif_path))
    elif mmcif_path.suffix.lower() not in ALLOWED_MMCIF_SUFFIXES:
        reporter.warn("threading template file does not use .cif/.mmcif suffix: {}".format(mmcif_path.name))
    else:
        reporter.note("threading mmCIF file exists")
    if not args.template_id:
        reporter.warn("--template-id was not supplied; output metadata may be less traceable")
    if not args.chain_id:
        reporter.warn("--chain-id was not supplied; template chain selection may be ambiguous")
    reporter.warn("threading template chain/length compatibility requires mmCIF parsing; confirm the requested chain matches the query before real inference")
    validate_checkpoint(args.checkpoint, reporter)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    try:
        subparsers.required = True
    except AttributeError:
        pass

    run_parser = subparsers.add_parser("run", help="Validate run_pretrained_openfold.py inputs")
    run_parser.add_argument("--mode", choices=("monomer", "multimer", "soloseq"), default="monomer")
    run_parser.add_argument("--fasta-dir", required=True)
    run_parser.add_argument("--template-mmcif-dir", required=True)
    run_parser.add_argument("--precomputed-alignments")
    run_parser.add_argument("--checkpoint", help="Optional OpenFold checkpoint or JAX parameter path to check")
    run_parser.add_argument("--skip-templates", action="store_true", help="Accept template-free workflows where template hits/mmCIFs are absent")
    run_parser.add_argument("--use-custom-template", action="store_true", help="Warn about custom template chain/length guardrails")

    thread_parser = subparsers.add_parser("thread", help="Validate thread_sequence.py inputs")
    thread_parser.add_argument("--input-fasta", required=True)
    thread_parser.add_argument("--input-mmcif", required=True)
    thread_parser.add_argument("--template-id")
    thread_parser.add_argument("--chain-id")
    thread_parser.add_argument("--checkpoint", help="Optional OpenFold checkpoint or JAX parameter path to check")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()
    if args.command == "run":
        validate_run(args, reporter)
    elif args.command == "thread":
        validate_threading(args, reporter)
    else:
        parser.error("choose a subcommand")
    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
