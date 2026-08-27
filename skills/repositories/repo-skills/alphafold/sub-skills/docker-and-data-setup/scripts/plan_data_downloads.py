#!/usr/bin/env python3
"""Plan AlphaFold data downloads or updates without downloading anything."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
from typing import Iterable

MODES = ("full_dbs", "reduced_dbs")

DATASETS = {
    "params": {
        "path": "params",
        "required_for": "all model presets",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download AlphaFold model parameters into params/",
        "notes": "Model parameters archive for AlphaFold 2.3.2-era presets.",
    },
    "bfd": {
        "path": "bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt",
        "required_for": "full_dbs",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and extract BFD into bfd/",
        "notes": "Large BFD database used by the full database preset.",
    },
    "small_bfd": {
        "path": "small_bfd/bfd-first_non_consensus_sequences.fasta",
        "required_for": "reduced_dbs",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and decompress Small BFD into small_bfd/",
        "notes": "Reduced BFD substitute used only with --db_preset=reduced_dbs.",
    },
    "mgnify": {
        "path": "mgnify/mgy_clusters_2022_05.fa",
        "required_for": "all workflows",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and decompress MGnify into mgnify/",
        "notes": "MGnify v2022_05 sequence database.",
    },
    "pdb70": {
        "path": "pdb70/pdb70",
        "required_for": "monomer-style presets",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and extract PDB70 into pdb70/",
        "notes": "HH-suite PDB70 database used outside multimer mode.",
    },
    "pdb_mmcif": {
        "path": "pdb_mmcif/mmcif_files",
        "extra_paths": ["pdb_mmcif/obsolete.dat"],
        "required_for": "template search",
        "prerequisites": ["aria2c", "rsync"],
        "supervised_operation": (
            "rsync, decompress, and flatten PDB mmCIF into pdb_mmcif/"
        ),
        "notes": "PDB mmCIF structures; keep date-aligned with PDB SeqRes.",
    },
    "uniref30": {
        "path": "uniref30/UniRef30_2021_03",
        "required_for": "full_dbs",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and extract UniRef30 into uniref30/",
        "notes": "UniRef30/UniClust30 database used by the full database preset.",
    },
    "uniref90": {
        "path": "uniref90/uniref90.fasta",
        "required_for": "all workflows",
        "prerequisites": ["aria2c"],
        "supervised_operation": "download and decompress UniRef90 into uniref90/",
        "notes": "UniRef90 sequence database.",
    },
    "uniprot": {
        "path": "uniprot/uniprot.fasta",
        "required_for": "multimer",
        "prerequisites": ["aria2c"],
        "supervised_operation": (
            "download SwissProt and TrEMBL, then merge into uniprot/uniprot.fasta"
        ),
        "notes": "Merged TrEMBL and SwissProt FASTA used by AlphaFold-Multimer.",
    },
    "pdb_seqres": {
        "path": "pdb_seqres/pdb_seqres.txt",
        "required_for": "multimer",
        "prerequisites": ["aria2c"],
        "supervised_operation": (
            "download and filter PDB SeqRes into pdb_seqres/pdb_seqres.txt"
        ),
        "notes": "Filtered protein SeqRes FASTA; keep date-aligned with PDB mmCIF.",
    },
}

UPDATE_ORDER = [
    "uniprot",
    "uniref30",
    "uniref90",
    "mgnify",
    "pdb_mmcif",
    "pdb_seqres",
    "params",
]


def _is_relative_to(path: pathlib.Path, parent: pathlib.Path) -> bool:
  try:
    path.relative_to(parent)
    return True
  except ValueError:
    return False


def _looks_like_alphafold_repo(path: pathlib.Path) -> bool:
  return (path / "run_alphafold.py").exists() and (path / "docker").is_dir()


def _infer_repo_root(start: pathlib.Path) -> pathlib.Path | None:
  for candidate in [start, *start.parents]:
    if _looks_like_alphafold_repo(candidate):
      return candidate.resolve()
  return None


def _dataset_names_for_mode(mode: str) -> list[str]:
  names = [
      "params",
      "mgnify",
      "pdb70",
      "pdb_mmcif",
      "uniref90",
      "uniprot",
      "pdb_seqres",
  ]
  if mode == "reduced_dbs":
    names.insert(1, "small_bfd")
  else:
    names.insert(1, "bfd")
    names.insert(5, "uniref30")
  return names


def _status(download_dir: pathlib.Path, dataset: dict[str, object]) -> str:
  paths = [dataset["path"], *dataset.get("extra_paths", [])]
  resolved = [download_dir / str(path) for path in paths]
  if all(path.exists() for path in resolved):
    return "present"
  if any(path.exists() for path in resolved):
    return "partial"
  return "missing"


def _prerequisite_status(names: Iterable[str]) -> dict[str, str]:
  return {name: "found" if shutil.which(name) else "missing" for name in names}


def _initial_actions(mode: str, download_dir: pathlib.Path) -> list[dict[str, object]]:
  actions = []
  for name in _dataset_names_for_mode(mode):
    dataset = DATASETS[name]
    actions.append({
        "dataset": name,
        "action": "download_or_verify",
        "target": str(download_dir / str(dataset["path"])),
        "status": _status(download_dir, dataset),
        "required_for": dataset["required_for"],
        "prerequisites": dataset["prerequisites"],
        "supervised_operation": dataset["supervised_operation"],
        "notes": dataset["notes"],
    })
  return actions


def _update_actions(download_dir: pathlib.Path) -> list[dict[str, object]]:
  remove_paths = {
      "uniprot": ["uniprot"],
      "uniref30": ["uniclust30", "uniref30"],
      "uniref90": ["uniref90"],
      "mgnify": ["mgnify"],
      "pdb_mmcif": ["pdb_mmcif"],
      "pdb_seqres": [],
      "params": ["params"],
  }
  actions = []
  for name in UPDATE_ORDER:
    dataset = DATASETS[name]
    actions.append({
        "dataset": name,
        "action": "remove_then_refresh" if remove_paths[name] else "refresh",
        "remove_paths": [str(download_dir / item) for item in remove_paths[name]],
        "target": str(download_dir / str(dataset["path"])),
        "status": _status(download_dir, dataset),
        "required_for": dataset["required_for"],
        "prerequisites": dataset["prerequisites"],
        "supervised_operation": dataset["supervised_operation"],
        "notes": dataset["notes"],
    })
  return actions


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description=(
          "Print an AlphaFold database/model-parameter setup or update plan. "
          "This script never downloads, deletes, extracts, or creates files."
      )
  )
  parser.add_argument("--download-dir", required=True, type=pathlib.Path)
  parser.add_argument("--mode", choices=MODES, default="full_dbs")
  parser.add_argument(
      "--update-from",
      default=None,
      help="Existing AlphaFold version being updated from; enables update plan.",
  )
  parser.add_argument(
      "--repo-root",
      type=pathlib.Path,
      default=None,
      help="AlphaFold checkout root used only to warn about nested data dirs.",
  )
  parser.add_argument("--format", choices=("text", "json"), default="text")
  return parser


def _plan(args: argparse.Namespace) -> dict[str, object]:
  download_dir = args.download_dir.expanduser().resolve()
  repo_root = (
      args.repo_root.expanduser().resolve()
      if args.repo_root is not None
      else _infer_repo_root(pathlib.Path.cwd().resolve())
  )

  warnings = [
      "Do not run download/update commands automatically; they are large, network-heavy external operations.",
      "Full databases are about 556 GB downloaded and about 2.62 TB expanded; use SSD storage when possible.",
      "Ensure the selected prediction --db_preset matches this data mode.",
  ]
  if args.mode == "reduced_dbs":
    warnings.append(
        "reduced_dbs uses small_bfd and should be paired with --db_preset=reduced_dbs."
    )
  else:
    warnings.append(
        "full_dbs uses bfd plus uniref30 and should be paired with --db_preset=full_dbs."
    )

  if repo_root is None:
    warnings.append(
        "could not infer AlphaFold repo root; pass --repo-root to check Docker build-context risk."
    )
  elif download_dir == repo_root or _is_relative_to(download_dir, repo_root):
    warnings.append(
        "download_dir is inside the AlphaFold repository/build context "
        f"({repo_root}); move it before Docker builds."
    )

  required_prerequisites = sorted({
      prerequisite
      for name in _dataset_names_for_mode(args.mode)
      for prerequisite in DATASETS[name]["prerequisites"]
  })
  if args.update_from is not None:
    required_prerequisites = sorted({
        prerequisite
        for name in UPDATE_ORDER
        for prerequisite in DATASETS[name]["prerequisites"]
    })

  plan_type = "incremental_update" if args.update_from is not None else "initial_setup"
  actions = (
      _update_actions(download_dir)
      if args.update_from is not None
      else _initial_actions(args.mode, download_dir)
  )

  if args.update_from is not None:
    warnings.append(
        "For updates after v2.3.0-era installs, keep PDB mmCIF and PDB SeqRes refreshed together in this order."
    )
    warnings.append(
        "Refresh model parameters after database/code updates unless deliberately pinning older/deprecated weights."
    )

  return {
      "ok": True,
      "plan_type": plan_type,
      "download_dir": str(download_dir),
      "mode": args.mode,
      "update_from": args.update_from,
      "prerequisites": _prerequisite_status(required_prerequisites),
      "actions": actions,
      "warnings": warnings,
      "dry_run_only": True,
  }


def _print_text(plan: dict[str, object]) -> None:
  print("AlphaFold data setup plan")
  print("=========================")
  print(f"Plan type: {plan['plan_type']}")
  print(f"Download directory: {plan['download_dir']}")
  print(f"Mode: {plan['mode']}")
  if plan["update_from"]:
    print(f"Updating from: {plan['update_from']}")

  print("\nPrerequisites on PATH:")
  for name, status in plan["prerequisites"].items():
    print(f"  {name}: {status}")

  print("\nPlanned actions (user-supervised external operations):")
  for index, action in enumerate(plan["actions"], start=1):
    print(f"  {index}. {action['dataset']} [{action['status']}]")
    if action.get("remove_paths"):
      print("     remove first:")
      for path in action["remove_paths"]:
        print(f"       - {path}")
    print(f"     target: {action['target']}")
    print(f"     required for: {action['required_for']}")
    print(f"     supervised operation: {action['supervised_operation']}")
    print(f"     note: {action['notes']}")

  print("\nWarnings:")
  for warning in plan["warnings"]:
    print(f"  - {warning}")

  print(
      "\nThis helper performed a dry run only: no download, deletion, extraction, "
      "directory creation, rsync, aria2c, tar, gunzip, or network access was attempted."
  )


def main(argv: list[str] | None = None) -> int:
  parser = _build_parser()
  args = parser.parse_args(argv)
  plan = _plan(args)
  if args.format == "json":
    print(json.dumps(plan, indent=2, sort_keys=True))
  else:
    _print_text(plan)
  return 0


if __name__ == "__main__":
  sys.exit(main())
