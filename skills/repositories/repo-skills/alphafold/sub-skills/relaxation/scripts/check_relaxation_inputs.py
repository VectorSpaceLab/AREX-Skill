#!/usr/bin/env python3
"""Dry-run checks for AlphaFold relaxation PDB inputs.

This helper inspects PDB-like text for relaxation triage without importing
AlphaFold, constructing OpenMM systems, running PDBFixer cleanup, or performing
minimization. Optional import checks only test whether OpenMM/PDBFixer modules
can be imported in the current runtime.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import importlib
import json
from pathlib import Path
import sys
from typing import Iterable

STANDARD_RESIDUES = {
    "ALA",
    "ARG",
    "ASN",
    "ASP",
    "CYS",
    "GLN",
    "GLU",
    "GLY",
    "HIS",
    "ILE",
    "LEU",
    "LYS",
    "MET",
    "PHE",
    "PRO",
    "SER",
    "THR",
    "TRP",
    "TYR",
    "VAL",
}

COMMON_BACKBONE = {"N", "CA", "C", "O"}


@dataclass(frozen=True)
class ResidueKey:
  chain_id: str
  residue_number: str
  insertion_code: str
  residue_name: str

  def label(self) -> str:
    insertion = self.insertion_code if self.insertion_code else ""
    return f"{self.chain_id}:{self.residue_name}{self.residue_number}{insertion}"


@dataclass
class ResidueInfo:
  key: ResidueKey
  atoms: set[str] = field(default_factory=set)
  elements: set[str] = field(default_factory=set)
  line_numbers: list[int] = field(default_factory=list)

  def as_dict(self) -> dict[str, object]:
    return {
        "chain_id": self.key.chain_id,
        "residue_number": self.key.residue_number,
        "insertion_code": self.key.insertion_code,
        "residue_name": self.key.residue_name,
        "atom_count": len(self.atoms),
        "atoms": sorted(self.atoms),
        "elements": sorted(self.elements),
        "first_line": self.line_numbers[0] if self.line_numbers else None,
    }


@dataclass
class Finding:
  level: str
  message: str

  def as_dict(self) -> dict[str, str]:
    return {"level": self.level, "message": self.message}


def parse_pdb_atom_line(line: str) -> tuple[str, str, str, str, str] | None:
  """Returns atom_name, residue_name, chain_id, residue_number, insertion_code."""
  if len(line) >= 27:
    atom_name = line[12:16].strip()
    residue_name = line[17:20].strip().upper()
    chain_id = line[21:22].strip() or "_"
    residue_number = line[22:26].strip()
    insertion_code = line[26:27].strip()
    if atom_name and residue_name and residue_number:
      return atom_name, residue_name, chain_id, residue_number, insertion_code

  parts = line.split()
  if len(parts) < 6:
    return None
  atom_name = parts[2].strip()
  residue_name = parts[3].strip().upper()
  chain_id = parts[4].strip() or "_"
  residue_number = parts[5].strip()
  if not atom_name or not residue_name or not residue_number:
    return None
  return atom_name, residue_name, chain_id, residue_number, ""


def parse_seqres_line(line: str) -> tuple[str, int, list[str]] | None:
  if len(line) >= 19:
    chain_id = line[11:12].strip() or "_"
    declared_count_text = line[13:17].strip()
    residues = line[19:].split()
    try:
      declared_count = int(declared_count_text)
    except ValueError:
      declared_count = 0
    if residues:
      return chain_id, declared_count, [residue.upper() for residue in residues]

  parts = line.split()
  if len(parts) < 5:
    return None
  chain_id = parts[2].strip() or "_"
  try:
    declared_count = int(parts[3])
  except ValueError:
    declared_count = 0
  return chain_id, declared_count, [residue.upper() for residue in parts[4:]]


def read_input(path_text: str) -> tuple[str, str]:
  if path_text == "-":
    return "<stdin>", sys.stdin.read()
  path = Path(path_text)
  with path.open("r", encoding="utf-8", errors="replace") as handle:
    return str(path), handle.read()


def inspect_pdb_text(label: str, text: str) -> dict[str, object]:
  findings: list[Finding] = []
  residues: dict[ResidueKey, ResidueInfo] = {}
  seqres_by_chain: dict[str, list[str]] = {}
  seqres_declared_counts: dict[str, int] = {}
  heterogen_counts: dict[str, int] = {}
  malformed_atom_lines: list[int] = []
  atom_record_count = 0
  hetatm_record_count = 0

  for line_number, line in enumerate(text.splitlines(), start=1):
    record = line[:6].strip().upper()
    if record == "SEQRES":
      parsed_seqres = parse_seqres_line(line)
      if parsed_seqres:
        chain_id, declared_count, residue_names = parsed_seqres
        seqres_by_chain.setdefault(chain_id, []).extend(residue_names)
        if declared_count:
          seqres_declared_counts[chain_id] = declared_count
      continue

    if record == "HETATM":
      hetatm_record_count += 1
      parsed = parse_pdb_atom_line(line)
      if parsed:
        _, residue_name, _, _, _ = parsed
        heterogen_counts[residue_name] = heterogen_counts.get(residue_name, 0) + 1
      continue

    if record != "ATOM":
      continue

    atom_record_count += 1
    parsed = parse_pdb_atom_line(line)
    if not parsed:
      malformed_atom_lines.append(line_number)
      continue

    atom_name, residue_name, chain_id, residue_number, insertion_code = parsed
    element = line[76:78].strip().upper() if len(line) >= 78 else ""
    key = ResidueKey(chain_id, residue_number, insertion_code, residue_name)
    residue = residues.setdefault(key, ResidueInfo(key=key))
    residue.atoms.add(atom_name)
    if element:
      residue.elements.add(element)
    residue.line_numbers.append(line_number)

  if atom_record_count == 0:
    findings.append(Finding("error", f"{label}: no ATOM records found; AlphaFold relaxation needs protein atoms"))
  if malformed_atom_lines:
    preview = ", ".join(str(number) for number in malformed_atom_lines[:10])
    suffix = "..." if len(malformed_atom_lines) > 10 else ""
    findings.append(Finding("warning", f"{label}: malformed ATOM lines ignored: {preview}{suffix}"))

  residues_by_chain: dict[str, list[ResidueInfo]] = {}
  for residue in residues.values():
    residues_by_chain.setdefault(residue.key.chain_id, []).append(residue)

  for chain_id, chain_residues in sorted(residues_by_chain.items()):
    if len(chain_residues) == 1:
      findings.append(
          Finding(
              "warning",
              f"{label}: chain {chain_id!r} has one ATOM residue; AlphaFold cleanup removes single-residue chains",
          )
      )

  missing_backbone: list[str] = []
  sparse_residues: list[str] = []
  nonstandard_residues: set[str] = set()
  for residue in residues.values():
    if residue.key.residue_name not in STANDARD_RESIDUES:
      nonstandard_residues.add(residue.key.residue_name)
    missing = COMMON_BACKBONE.difference(residue.atoms)
    if missing:
      missing_backbone.append(f"{residue.key.label()} missing {','.join(sorted(missing))}")
    if len(residue.atoms) <= 1:
      sparse_residues.append(f"{residue.key.label()} has {len(residue.atoms)} atom")

  if missing_backbone:
    preview = "; ".join(missing_backbone[:12])
    suffix = f"; plus {len(missing_backbone) - 12} more" if len(missing_backbone) > 12 else ""
    findings.append(
        Finding(
            "warning",
            f"{label}: residues missing common backbone atoms may fail AlphaFold ideal atom-mask checks: {preview}{suffix}",
        )
    )

  if sparse_residues:
    preview = "; ".join(sparse_residues[:12])
    suffix = f"; plus {len(sparse_residues) - 12} more" if len(sparse_residues) > 12 else ""
    findings.append(Finding("warning", f"{label}: very sparse residue atom sets detected: {preview}{suffix}"))

  if nonstandard_residues:
    findings.append(
        Finding(
            "warning",
            f"{label}: nonstandard ATOM residue names may be converted to UNK or replaced by cleanup: {', '.join(sorted(nonstandard_residues))}",
        )
    )

  if hetatm_record_count:
    common = ", ".join(f"{name}:{count}" for name, count in sorted(heterogen_counts.items())[:10])
    findings.append(
        Finding(
            "warning",
            f"{label}: {hetatm_record_count} HETATM records found; AlphaFold relaxation cleanup removes heterogens and water ({common})",
        )
    )

  for chain_id, seqres_residues in sorted(seqres_by_chain.items()):
    observed_count = len(residues_by_chain.get(chain_id, []))
    declared_count = seqres_declared_counts.get(chain_id, len(seqres_residues))
    seqres_count = max(declared_count, len(seqres_residues))
    if observed_count == 0:
      findings.append(
          Finding(
              "warning",
              f"{label}: SEQRES chain {chain_id!r} has {seqres_count} residues but no ATOM residues",
          )
      )
    elif seqres_count > observed_count:
      findings.append(
          Finding(
              "info",
              f"{label}: SEQRES chain {chain_id!r} lists {seqres_count} residues while ATOM records cover {observed_count}; PDBFixer may add missing residues during cleanup",
          )
      )

  residue_dicts = [residue.as_dict() for residue in sorted(residues.values(), key=lambda item: (item.key.chain_id, item.key.residue_number, item.key.insertion_code, item.key.residue_name))]
  return {
      "label": label,
      "atom_records": atom_record_count,
      "hetatm_records": hetatm_record_count,
      "residue_count": len(residues),
      "chain_count": len(residues_by_chain),
      "chains": {chain_id: len(chain_residues) for chain_id, chain_residues in sorted(residues_by_chain.items())},
      "seqres_chains": {chain_id: len(residue_names) for chain_id, residue_names in sorted(seqres_by_chain.items())},
      "heterogens": dict(sorted(heterogen_counts.items())),
      "residues": residue_dicts,
      "findings": [finding.as_dict() for finding in findings],
  }


def check_import(module_name: str) -> dict[str, object]:
  result: dict[str, object] = {"module": module_name, "available": False}
  try:
    module = importlib.import_module(module_name)
  except Exception as exc:  # pylint: disable=broad-except
    result.update({"error": f"{type(exc).__name__}: {exc}"})
    return result

  result["available"] = True
  version = getattr(module, "__version__", None)
  if version is not None:
    result["version"] = str(version)
  if module_name == "openmm":
    try:
      platform_type = getattr(module, "Platform")
      platforms = [platform_type.getPlatform(i).getName() for i in range(platform_type.getNumPlatforms())]
      result["platforms"] = platforms
    except Exception as exc:  # pylint: disable=broad-except
      result["platform_error"] = f"{type(exc).__name__}: {exc}"
  return result


def summarize_levels(reports: Iterable[dict[str, object]]) -> dict[str, int]:
  counts = {"error": 0, "warning": 0, "info": 0}
  for report in reports:
    for finding in report.get("findings", []):
      level = str(finding.get("level", "info"))
      counts[level] = counts.get(level, 0) + 1
  return counts


def print_text_report(payload: dict[str, object]) -> None:
  for report in payload["reports"]:
    print(f"== {report['label']} ==")
    print(
        "ATOM records: {atom_records}; residues: {residue_count}; chains: {chain_count}; HETATM records: {hetatm_records}".format(
            **report
        )
    )
    chains = report.get("chains", {})
    if chains:
      chain_summary = ", ".join(f"{chain}:{count}" for chain, count in chains.items())
      print(f"Chains: {chain_summary}")
    for finding in report.get("findings", []):
      print(f"[{finding['level']}] {finding['message']}")
    if not report.get("findings"):
      print("[info] No obvious text-level relaxation blockers found.")
    print()

  imports = payload.get("imports") or []
  if imports:
    print("== Import availability ==")
    for item in imports:
      status = "available" if item.get("available") else "missing"
      details = []
      if item.get("version"):
        details.append(f"version {item['version']}")
      if item.get("platforms"):
        details.append("platforms " + ",".join(item["platforms"]))
      if item.get("error"):
        details.append(str(item["error"]))
      if item.get("platform_error"):
        details.append("platform probe: " + str(item["platform_error"]))
      suffix = f" ({'; '.join(details)})" if details else ""
      print(f"{item['module']}: {status}{suffix}")
    print()

  levels = payload["summary"]
  print(f"Summary: {levels.get('error', 0)} error(s), {levels.get('warning', 0)} warning(s), {levels.get('info', 0)} info finding(s).")


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description="Inspect PDB-like files for AlphaFold relaxation triage without running minimization."
  )
  parser.add_argument("pdb_paths", nargs="+", help="PDB-like files to inspect, or '-' for stdin")
  parser.add_argument(
      "--check-imports",
      action="store_true",
      help="Optionally import openmm and pdbfixer to report runtime availability without minimization.",
  )
  parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
  parser.add_argument(
      "--fail-on",
      choices=("never", "error", "warning"),
      default="error",
      help="Exit nonzero on findings at or above this severity. Defaults to error.",
  )
  return parser


def should_fail(levels: dict[str, int], fail_on: str) -> bool:
  if fail_on == "never":
    return False
  if fail_on == "warning":
    return levels.get("error", 0) > 0 or levels.get("warning", 0) > 0
  return levels.get("error", 0) > 0


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  reports: list[dict[str, object]] = []

  for path_text in args.pdb_paths:
    try:
      label, text = read_input(path_text)
    except OSError as exc:
      reports.append(
          {
              "label": path_text,
              "atom_records": 0,
              "hetatm_records": 0,
              "residue_count": 0,
              "chain_count": 0,
              "chains": {},
              "seqres_chains": {},
              "heterogens": {},
              "residues": [],
              "findings": [Finding("error", f"{path_text}: cannot read file: {exc}").as_dict()],
          }
      )
      continue
    reports.append(inspect_pdb_text(label, text))

  imports = []
  if args.check_imports:
    imports = [check_import("openmm"), check_import("pdbfixer")]
    for item in imports:
      if not item.get("available"):
        reports.append(
            {
                "label": f"import:{item['module']}",
                "atom_records": 0,
                "hetatm_records": 0,
                "residue_count": 0,
                "chain_count": 0,
                "chains": {},
                "seqres_chains": {},
                "heterogens": {},
                "residues": [],
                "findings": [
                    Finding(
                        "warning",
                        f"optional relaxation dependency {item['module']} is not importable: {item.get('error', 'missing')}",
                    ).as_dict()
                ],
            }
        )

  summary = summarize_levels(reports)
  payload: dict[str, object] = {"reports": reports, "imports": imports, "summary": summary}

  if args.json:
    print(json.dumps(payload, indent=2, sort_keys=True))
  else:
    print_text_report(payload)

  return 1 if should_fail(summary, args.fail_on) else 0


if __name__ == "__main__":
  raise SystemExit(main())
