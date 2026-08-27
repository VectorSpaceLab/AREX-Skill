#!/usr/bin/env python3
"""Dry-run validation for AlphaFold direct prediction CLI inputs.

This helper mirrors important run_alphafold flag constraints without importing
AlphaFold, loading model weights, running external MSA tools, or starting JAX.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Iterable

MODEL_PRESETS = ("monomer", "monomer_casp14", "monomer_ptm", "multimer")
DB_PRESETS = ("full_dbs", "reduced_dbs")
MODELS_TO_RELAX = ("all", "best", "none")

STANDARD_PATHS = {
    "uniref90_database_path": ("file", ("uniref90", "uniref90.fasta")),
    "mgnify_database_path": ("file", ("mgnify", "mgy_clusters_2022_05.fa")),
    "bfd_database_path": (
        "prefix",
        ("bfd", "bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt"),
    ),
    "small_bfd_database_path": (
        "file",
        ("small_bfd", "bfd-first_non_consensus_sequences.fasta"),
    ),
    "uniref30_database_path": ("prefix", ("uniref30", "UniRef30_2021_03")),
    "uniprot_database_path": ("file", ("uniprot", "uniprot.fasta")),
    "pdb70_database_path": ("prefix", ("pdb70", "pdb70")),
    "pdb_seqres_database_path": ("file", ("pdb_seqres", "pdb_seqres.txt")),
    "template_mmcif_dir": ("dir", ("pdb_mmcif", "mmcif_files")),
    "obsolete_pdbs_path": ("file", ("pdb_mmcif", "obsolete.dat")),
}

BINARY_FLAGS = {
    "jackhmmer_binary_path": "jackhmmer",
    "hhblits_binary_path": "hhblits",
    "hhsearch_binary_path": "hhsearch",
    "hmmsearch_binary_path": "hmmsearch",
    "hmmbuild_binary_path": "hmmbuild",
    "kalign_binary_path": "kalign",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Finding:
  def __init__(self, level: str, message: str):
    self.level = level
    self.message = message

  def as_dict(self) -> dict[str, str]:
    return {"level": self.level, "message": self.message}


def parse_bool(value: str) -> bool:
  lowered = value.lower()
  if lowered in {"1", "true", "t", "yes", "y"}:
    return True
  if lowered in {"0", "false", "f", "no", "n"}:
    return False
  raise argparse.ArgumentTypeError(f"expected boolean true/false, got {value!r}")


def split_fasta_paths(value: str) -> list[Path]:
  paths = [item.strip() for item in value.split(",") if item.strip()]
  return [Path(item) for item in paths]


def parse_fasta(path: Path) -> tuple[int, int, list[str]]:
  sequence_count = 0
  total_residues = 0
  headers: list[str] = []
  saw_header = False
  current_length = 0

  with path.open("r", encoding="utf-8") as handle:
    for line_number, raw_line in enumerate(handle, start=1):
      line = raw_line.strip()
      if not line:
        continue
      if line.startswith(">"):
        if saw_header and current_length == 0:
          raise ValueError(f"empty sequence before line {line_number}")
        saw_header = True
        sequence_count += 1
        headers.append(line[1:].strip() or f"sequence_{sequence_count}")
        current_length = 0
        continue
      if not saw_header:
        raise ValueError(f"sequence data appears before first FASTA header at line {line_number}")
      letters = re.sub(r"\s+", "", line)
      current_length += len(letters)
      total_residues += len(letters)

  if not saw_header:
    raise ValueError("no FASTA records found")
  if current_length == 0:
    raise ValueError("last FASTA record has no sequence")
  return sequence_count, total_residues, headers


def path_has_prefix_files(path: Path) -> bool:
  if path.exists():
    return True
  parent = path.parent if str(path.parent) else Path(".")
  if not parent.exists():
    return False
  return any(parent.glob(path.name + "*"))


def check_path(path: Path, kind: str) -> bool:
  if kind == "file":
    return path.is_file()
  if kind == "dir":
    return path.is_dir()
  if kind == "prefix":
    return path_has_prefix_files(path)
  raise ValueError(f"unknown path kind {kind}")


def add_path_finding(
    findings: list[Finding],
    path: Path,
    kind: str,
    label: str,
    strict: bool,
) -> None:
  if check_path(path, kind):
    return
  level = "error" if strict else "warning"
  if kind == "prefix":
    findings.append(
        Finding(level, f"{label} does not exist as a path or database prefix: {path}")
    )
  else:
    findings.append(Finding(level, f"{label} expected {kind} is missing: {path}"))


def set_inferred_database_paths(args: argparse.Namespace) -> None:
  data_dir = Path(args.data_dir)
  needed = {
      "uniref90_database_path",
      "mgnify_database_path",
      "template_mmcif_dir",
      "obsolete_pdbs_path",
  }
  if args.db_preset == "reduced_dbs":
    needed.add("small_bfd_database_path")
  else:
    needed.update({"bfd_database_path", "uniref30_database_path"})
  if args.model_preset == "multimer":
    needed.update({"uniprot_database_path", "pdb_seqres_database_path"})
  else:
    needed.add("pdb70_database_path")

  for name in needed:
    if getattr(args, name):
      continue
    _, parts = STANDARD_PATHS[name]
    setattr(args, name, str(data_dir.joinpath(*parts)))


def require_flag(
    findings: list[Finding], args: argparse.Namespace, name: str, reason: str
) -> None:
  if not getattr(args, name):
    findings.append(Finding("error", f"--{name} is required {reason}"))


def forbid_flag(
    findings: list[Finding], args: argparse.Namespace, name: str, reason: str
) -> None:
  if getattr(args, name):
    findings.append(Finding("error", f"--{name} must not be set {reason}"))


def validate_fasta_paths(args: argparse.Namespace, findings: list[Finding]) -> None:
  fasta_paths = split_fasta_paths(args.fasta_paths)
  if not fasta_paths:
    findings.append(Finding("error", "--fasta_paths must contain at least one FASTA path"))
    return

  stems: dict[str, Path] = {}
  for path in fasta_paths:
    if path.stem in stems:
      findings.append(
          Finding(
              "error",
              "FASTA basenames must be unique; "
              f"{stems[path.stem]} and {path} both map to output target {path.stem!r}",
          )
      )
    else:
      stems[path.stem] = path

    if not path.is_file():
      findings.append(Finding("error", f"FASTA path is not a readable file: {path}"))
      continue
    try:
      sequence_count, total_residues, _ = parse_fasta(path)
    except (OSError, ValueError) as exc:
      findings.append(Finding("error", f"FASTA parse failed for {path}: {exc}"))
      continue
    if args.model_preset == "multimer" and sequence_count < 2:
      findings.append(
          Finding(
              "warning",
              f"{path} contains one sequence while --model_preset=multimer is normally used for multi-sequence complexes",
          )
      )
    if total_residues > 2500:
      findings.append(
          Finding(
              "warning",
              f"{path} contains {total_residues} total residues; long inputs can require substantial GPU memory",
          )
      )
    if sequence_count > 20:
      findings.append(
          Finding(
              "warning",
              f"{path} contains {sequence_count} FASTA records; many-chain multimers can be expensive",
          )
      )


def validate_output_dir(args: argparse.Namespace, findings: list[Finding]) -> None:
  output_dir = Path(args.output_dir)
  if output_dir.exists() and not output_dir.is_dir():
    findings.append(Finding("error", f"--output_dir exists but is not a directory: {output_dir}"))
    return

  check_dir = output_dir if output_dir.exists() else output_dir.parent
  if not check_dir.exists():
    findings.append(Finding("error", f"parent directory for --output_dir does not exist: {check_dir}"))
    return
  if not os.access(check_dir, os.W_OK):
    findings.append(Finding("error", f"output directory or parent is not writable: {check_dir}"))

  data_dir = Path(args.data_dir)
  try:
    if output_dir.resolve() == data_dir.resolve():
      findings.append(Finding("warning", "--output_dir is the same as --data_dir; keep predictions separate from databases"))
  except OSError:
    pass

  for fasta_path in split_fasta_paths(args.fasta_paths):
    target_dir = output_dir / fasta_path.stem
    if args.use_precomputed_msas and not (target_dir / "msas").is_dir():
      findings.append(
          Finding(
              "warning",
              f"--use_precomputed_msas=true but cached MSA directory is not present: {target_dir / 'msas'}",
          )
      )
    elif target_dir.exists() and not args.use_precomputed_msas:
      findings.append(
          Finding(
              "warning",
              f"target output directory already exists and may be overwritten or mixed with a new run: {target_dir}",
          )
      )


def validate_database_flags(args: argparse.Namespace, findings: list[Finding]) -> None:
  if args.infer_database_paths:
    set_inferred_database_paths(args)

  require_flag(findings, args, "uniref90_database_path", "for every run")
  require_flag(findings, args, "mgnify_database_path", "for every run")
  require_flag(findings, args, "template_mmcif_dir", "for every run")
  require_flag(findings, args, "obsolete_pdbs_path", "for every run")

  if args.db_preset == "reduced_dbs":
    require_flag(findings, args, "small_bfd_database_path", "when --db_preset=reduced_dbs")
    forbid_flag(findings, args, "bfd_database_path", "when --db_preset=reduced_dbs")
    forbid_flag(findings, args, "uniref30_database_path", "when --db_preset=reduced_dbs")
  else:
    require_flag(findings, args, "bfd_database_path", "when --db_preset=full_dbs")
    require_flag(findings, args, "uniref30_database_path", "when --db_preset=full_dbs")
    forbid_flag(findings, args, "small_bfd_database_path", "when --db_preset=full_dbs")

  if args.model_preset == "multimer":
    require_flag(findings, args, "pdb_seqres_database_path", "when --model_preset=multimer")
    require_flag(findings, args, "uniprot_database_path", "when --model_preset=multimer")
    forbid_flag(findings, args, "pdb70_database_path", "when --model_preset=multimer")
  else:
    require_flag(findings, args, "pdb70_database_path", f"when --model_preset={args.model_preset}")
    forbid_flag(findings, args, "pdb_seqres_database_path", f"when --model_preset={args.model_preset}")
    forbid_flag(findings, args, "uniprot_database_path", f"when --model_preset={args.model_preset}")

  for name, (kind, _) in STANDARD_PATHS.items():
    value = getattr(args, name)
    if value:
      add_path_finding(findings, Path(value), kind, f"--{name}", args.strict_database_paths)


def validate_binaries(args: argparse.Namespace, findings: list[Finding]) -> None:
  if args.skip_binary_checks:
    return
  for flag_name, binary_name in BINARY_FLAGS.items():
    value = getattr(args, flag_name)
    if value:
      if not Path(value).is_file():
        findings.append(Finding("error", f"--{flag_name} is not a file: {value}"))
      continue
    if not shutil.which(binary_name):
      findings.append(
          Finding(
              "warning",
              f"{binary_name!r} was not found on PATH; run_alphafold will require --{flag_name} or a PATH fix",
          )
      )


def validate_misc_flags(args: argparse.Namespace, findings: list[Finding]) -> None:
  if not DATE_RE.match(args.max_template_date):
    findings.append(Finding("warning", "--max_template_date should use YYYY-MM-DD format"))
  if args.model_preset != "multimer" and args.num_multimer_predictions_per_model != 5:
    findings.append(
        Finding(
            "warning",
            "--num_multimer_predictions_per_model is ignored unless --model_preset=multimer",
        )
    )
  if args.use_precomputed_msas:
    findings.append(
        Finding(
            "warning",
            "--use_precomputed_msas=true does not verify that cached MSAs match the current FASTA, databases, or flags",
        )
    )
  if args.random_seed is not None:
    findings.append(
        Finding(
            "warning",
            "--random_seed improves comparability but AlphaFold may still be nondeterministic on GPU or changed data",
        )
    )
  if args.benchmark:
    findings.append(
        Finding(
            "warning",
            "--benchmark=true runs an additional prediction call per model to exclude JAX compile time from benchmark timing",
        )
    )
  if args.models_to_relax == "none":
    findings.append(Finding("info", "--models_to_relax=none skips relaxation and relax_metrics.json"))


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description="Validate AlphaFold direct CLI inputs without running inference."
  )
  parser.add_argument("--fasta_paths", required=True, help="Comma-separated FASTA paths.")
  parser.add_argument("--data_dir", required=True, help="AlphaFold data directory.")
  parser.add_argument("--output_dir", required=True, help="Prediction output directory.")
  parser.add_argument("--max_template_date", required=True, help="Template cutoff date, usually YYYY-MM-DD.")
  parser.add_argument("--model_preset", choices=MODEL_PRESETS, default="monomer")
  parser.add_argument("--db_preset", choices=DB_PRESETS, default="full_dbs")
  parser.add_argument("--models_to_relax", choices=MODELS_TO_RELAX, default="best")
  parser.add_argument("--use_gpu_relax", type=parse_bool, required=True)
  parser.add_argument("--num_multimer_predictions_per_model", type=int, default=5)
  parser.add_argument("--benchmark", type=parse_bool, default=False)
  parser.add_argument("--use_precomputed_msas", type=parse_bool, default=False)
  parser.add_argument("--random_seed", type=int)
  parser.add_argument("--infer_database_paths", action="store_true", help="Fill missing database flags from the standard AlphaFold data layout under --data_dir.")
  parser.add_argument("--strict_database_paths", action="store_true", help="Treat missing database files/prefixes as errors instead of warnings.")
  parser.add_argument("--skip_binary_checks", action="store_true", help="Do not check HMMER, HH-suite, and Kalign binary availability.")
  parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")

  for name in STANDARD_PATHS:
    parser.add_argument(f"--{name}")
  for name in BINARY_FLAGS:
    parser.add_argument(f"--{name}")
  return parser


def summarize_command(args: argparse.Namespace) -> dict[str, object]:
  return {
      "fasta_targets": [Path(path).stem for path in split_fasta_paths(args.fasta_paths)],
      "model_preset": args.model_preset,
      "db_preset": args.db_preset,
      "models_to_relax": args.models_to_relax,
      "multimer_predictions_per_model": (
          args.num_multimer_predictions_per_model if args.model_preset == "multimer" else None
      ),
      "use_precomputed_msas": args.use_precomputed_msas,
      "benchmark": args.benchmark,
  }


def print_text(findings: Iterable[Finding], summary: dict[str, object]) -> None:
  print("AlphaFold prediction input dry-run")
  print("Summary:")
  for key, value in summary.items():
    print(f"  {key}: {value}")
  print("Findings:")
  any_findings = False
  for finding in findings:
    any_findings = True
    print(f"  [{finding.level.upper()}] {finding.message}")
  if not any_findings:
    print("  [OK] no issues found")


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv)
  findings: list[Finding] = []

  if args.num_multimer_predictions_per_model < 1:
    findings.append(Finding("error", "--num_multimer_predictions_per_model must be at least 1"))

  validate_fasta_paths(args, findings)
  validate_output_dir(args, findings)
  validate_database_flags(args, findings)
  validate_binaries(args, findings)
  validate_misc_flags(args, findings)

  summary = summarize_command(args)
  has_errors = any(finding.level == "error" for finding in findings)
  if args.json:
    print(
        json.dumps(
            {
                "ok": not has_errors,
                "summary": summary,
                "findings": [finding.as_dict() for finding in findings],
            },
            indent=2,
        )
    )
  else:
    print_text(findings, summary)
  return 1 if has_errors else 0


if __name__ == "__main__":
  sys.exit(main())
