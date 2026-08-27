#!/usr/bin/env python3
"""Plan an AlphaFold Docker launcher command without running Docker."""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import os
import pathlib
import shlex
import sys
from typing import Iterable

ROOT_MOUNT_DIRECTORY = pathlib.PurePosixPath("/mnt")

MODEL_PRESETS = ("monomer", "monomer_casp14", "monomer_ptm", "multimer")
DB_PRESETS = ("full_dbs", "reduced_dbs")
MODELS_TO_RELAX = ("best", "all", "none")


def _parse_bool(value: str) -> bool:
  normalized = value.lower()
  if normalized in {"1", "true", "t", "yes", "y"}:
    return True
  if normalized in {"0", "false", "f", "no", "n"}:
    return False
  raise argparse.ArgumentTypeError(f"expected boolean, got {value!r}")


def _split_fasta_paths(value: str) -> list[pathlib.Path]:
  paths = [pathlib.Path(item).expanduser() for item in value.split(",") if item]
  if not paths:
    raise argparse.ArgumentTypeError("at least one FASTA path is required")
  return paths


def _quote_command(parts: Iterable[str]) -> str:
  return " ".join(shlex.quote(part) for part in parts)


def _looks_like_alphafold_repo(path: pathlib.Path) -> bool:
  return (path / "run_alphafold.py").exists() and (path / "docker").is_dir()


def _infer_repo_root(start: pathlib.Path) -> pathlib.Path | None:
  for candidate in [start, *start.parents]:
    if _looks_like_alphafold_repo(candidate):
      return candidate.resolve()
  return None


def _is_relative_to(path: pathlib.Path, parent: pathlib.Path) -> bool:
  try:
    path.relative_to(parent)
    return True
  except ValueError:
    return False


def _validate_date(value: str) -> str:
  try:
    _datetime.date.fromisoformat(value)
  except ValueError as exc:
    raise argparse.ArgumentTypeError(
        "expected ISO date in YYYY-MM-DD format"
    ) from exc
  return value


def _path_status(path: pathlib.Path, expected_type: str) -> str:
  if expected_type == "dir":
    return "present" if path.is_dir() else "missing"
  if expected_type == "file":
    return "present" if path.is_file() else "missing"
  return "present" if path.exists() else "missing"


def _mount_plan(mount_name: str, path: pathlib.Path) -> dict[str, str]:
  absolute_path = path.expanduser().resolve()
  target_path = ROOT_MOUNT_DIRECTORY / mount_name
  if absolute_path.is_dir():
    source_path = absolute_path
    mounted_path = target_path
  else:
    source_path = absolute_path.parent
    mounted_path = target_path / absolute_path.name
  return {
      "name": mount_name,
      "source": str(source_path),
      "target": str(target_path),
      "container_path": str(mounted_path),
      "read_only": "true",
  }


def _database_paths(data_dir: pathlib.Path, model_preset: str, db_preset: str):
  paths = [
      ("uniref90_database_path", data_dir / "uniref90" / "uniref90.fasta", "file"),
      ("mgnify_database_path", data_dir / "mgnify" / "mgy_clusters_2022_05.fa", "file"),
      ("data_dir", data_dir, "dir"),
      ("template_mmcif_dir", data_dir / "pdb_mmcif" / "mmcif_files", "dir"),
      ("obsolete_pdbs_path", data_dir / "pdb_mmcif" / "obsolete.dat", "file"),
  ]
  if model_preset == "multimer":
    paths.extend([
        ("uniprot_database_path", data_dir / "uniprot" / "uniprot.fasta", "file"),
        ("pdb_seqres_database_path", data_dir / "pdb_seqres" / "pdb_seqres.txt", "file"),
    ])
  else:
    paths.append(("pdb70_database_path", data_dir / "pdb70" / "pdb70", "file"))

  if db_preset == "reduced_dbs":
    paths.append((
        "small_bfd_database_path",
        data_dir / "small_bfd" / "bfd-first_non_consensus_sequences.fasta",
        "file",
    ))
  else:
    paths.extend([
        ("uniref30_database_path", data_dir / "uniref30" / "UniRef30_2021_03", "dir"),
        (
            "bfd_database_path",
            data_dir
            / "bfd"
            / "bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt",
            "dir",
        ),
    ])
  return paths


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description=(
          "Validate AlphaFold Docker launcher paths and print a command plan. "
          "This script never imports Docker or starts containers."
      )
  )
  parser.add_argument(
      "--fasta-paths",
      required=True,
      type=_split_fasta_paths,
      help="Comma-separated host FASTA paths; basenames must be unique.",
  )
  parser.add_argument("--data-dir", required=True, type=pathlib.Path)
  parser.add_argument("--output-dir", default="/tmp/alphafold", type=pathlib.Path)
  parser.add_argument(
      "--max-template-date", required=True, type=_validate_date
  )
  parser.add_argument("--model-preset", default="monomer", choices=MODEL_PRESETS)
  parser.add_argument("--db-preset", default="full_dbs", choices=DB_PRESETS)
  parser.add_argument("--models-to-relax", default="best", choices=MODELS_TO_RELAX)
  parser.add_argument("--benchmark", default=False, type=_parse_bool)
  parser.add_argument("--use-precomputed-msas", default=False, type=_parse_bool)
  parser.add_argument("--use-gpu", default=True, type=_parse_bool)
  parser.add_argument("--enable-gpu-relax", default=True, type=_parse_bool)
  parser.add_argument("--gpu-devices", default="all")
  parser.add_argument("--docker-image-name", default="alphafold")
  parser.add_argument("--docker-user", default=None)
  parser.add_argument(
      "--num-multimer-predictions-per-model", default=5, type=int
  )
  parser.add_argument(
      "--repo-root",
      type=pathlib.Path,
      default=None,
      help=(
          "AlphaFold project/build-context root used only to reject data_dir "
          "inside the Docker build context. Defaults to the nearest parent "
          "that looks like an AlphaFold project root."
      ),
  )
  parser.add_argument(
      "--allow-missing-databases",
      action="store_true",
      help="Print a plan even when required database files/directories are absent.",
  )
  parser.add_argument(
      "--allow-missing-output-dir",
      action="store_true",
      help="Print a plan even when output_dir does not already exist.",
  )
  parser.add_argument(
      "--format", choices=("text", "json"), default="text"
  )
  return parser


def _plan(args: argparse.Namespace) -> tuple[dict[str, object], list[str], list[str]]:
  errors: list[str] = []
  warnings: list[str] = []

  fasta_paths = [path.expanduser().resolve() for path in args.fasta_paths]
  fasta_basenames = [path.name for path in fasta_paths]
  duplicate_basenames = sorted({
      basename for basename in fasta_basenames if fasta_basenames.count(basename) > 1
  })
  if duplicate_basenames:
    errors.append(
        "duplicate FASTA basenames are not allowed: "
        + ", ".join(duplicate_basenames)
    )
  for fasta_path in fasta_paths:
    if not fasta_path.is_file():
      errors.append(f"FASTA path is not a file: {fasta_path}")

  data_dir = args.data_dir.expanduser().resolve()
  if not data_dir.is_dir():
    errors.append(f"data_dir is not a directory: {data_dir}")

  output_dir = args.output_dir.expanduser().resolve()
  if not output_dir.is_dir() and not args.allow_missing_output_dir:
    errors.append(
        f"output_dir does not exist; create it before Docker run: {output_dir}"
    )

  if args.repo_root is not None:
    repo_root = args.repo_root.expanduser().resolve()
  else:
    repo_root = _infer_repo_root(pathlib.Path.cwd().resolve())
  if repo_root is None:
    warnings.append(
        "could not infer AlphaFold repo root; pass --repo-root to check whether "
        "data_dir is inside the Docker build context"
    )
  else:
    if data_dir == repo_root or _is_relative_to(data_dir, repo_root):
      errors.append(
          "data_dir must not be inside the AlphaFold repository/build context: "
          f"{data_dir} is under {repo_root}"
      )

  database_entries = []
  database_mounts = []
  for flag_name, host_path, expected_type in _database_paths(
      data_dir, args.model_preset, args.db_preset
  ):
    absolute_host_path = host_path.expanduser().resolve()
    status = _path_status(absolute_host_path, expected_type)
    mount = _mount_plan(flag_name, absolute_host_path)
    database_entries.append({
        "flag": flag_name,
        "host_path": str(absolute_host_path),
        "container_path": mount["container_path"],
        "expected_type": expected_type,
        "status": status,
    })
    database_mounts.append(mount)
    if status == "missing" and not args.allow_missing_databases:
      errors.append(
          f"required {expected_type} for --{flag_name} is missing: "
          f"{absolute_host_path}"
      )

  fasta_mounts = []
  container_fasta_paths = []
  for index, fasta_path in enumerate(fasta_paths):
    mount = _mount_plan(f"fasta_path_{index}", fasta_path)
    fasta_mounts.append(mount)
    container_fasta_paths.append(mount["container_path"])

  effective_gpu_relax = args.enable_gpu_relax and args.use_gpu
  output_container_path = str(ROOT_MOUNT_DIRECTORY / "output")

  container_args = [
      f"--fasta_paths={','.join(container_fasta_paths)}",
      *[
          f"--{entry['flag']}={entry['container_path']}"
          for entry in database_entries
      ],
      f"--output_dir={output_container_path}",
      f"--max_template_date={args.max_template_date}",
      f"--db_preset={args.db_preset}",
      f"--model_preset={args.model_preset}",
      f"--benchmark={args.benchmark}",
      f"--use_precomputed_msas={args.use_precomputed_msas}",
      (
          "--num_multimer_predictions_per_model="
          f"{args.num_multimer_predictions_per_model}"
      ),
      f"--models_to_relax={args.models_to_relax}",
      f"--use_gpu_relax={effective_gpu_relax}",
      "--logtostderr",
  ]

  output_mount = {
      "name": "output",
      "source": str(output_dir),
      "target": output_container_path,
      "container_path": output_container_path,
      "read_only": "false",
  }
  mounts = [*fasta_mounts, *database_mounts, output_mount]

  docker_parts = ["docker", "run", "--rm"]
  if args.use_gpu:
    docker_parts.extend(["--gpus", args.gpu_devices])
    docker_parts.extend(["-e", f"NVIDIA_VISIBLE_DEVICES={args.gpu_devices}"])
    docker_parts.extend(["-e", "TF_FORCE_UNIFIED_MEMORY=1"])
    docker_parts.extend(["-e", "XLA_PYTHON_CLIENT_MEM_FRACTION=4.0"])
  if args.docker_user:
    docker_parts.extend(["--user", args.docker_user])
  for mount in mounts:
    suffix = ":ro" if mount["read_only"] == "true" else ""
    docker_parts.extend([
        "--mount",
        f"type=bind,source={mount['source']},target={mount['target']}{suffix}",
    ])
  docker_parts.append(args.docker_image_name)
  docker_parts.extend(container_args)

  plan = {
      "ok": not errors,
      "docker_run_command": _quote_command(docker_parts),
      "container_args": container_args,
      "mounts": mounts,
      "database_paths": database_entries,
      "gpu": {
          "use_gpu": args.use_gpu,
          "gpu_devices": args.gpu_devices,
          "enable_gpu_relax_requested": args.enable_gpu_relax,
          "effective_gpu_relax": effective_gpu_relax,
          "environment": {
              "NVIDIA_VISIBLE_DEVICES": args.gpu_devices,
              "TF_FORCE_UNIFIED_MEMORY": "1",
              "XLA_PYTHON_CLIENT_MEM_FRACTION": "4.0",
          }
          if args.use_gpu
          else {},
      },
      "warnings": warnings,
      "errors": errors,
  }
  return plan, errors, warnings


def _print_text(plan: dict[str, object]) -> None:
  print("AlphaFold Docker command plan")
  print("===============================")
  print(f"Status: {'OK' if plan['ok'] else 'BLOCKED'}")
  print("\nDocker run command (user-supervised external operation):")
  print(plan["docker_run_command"])

  print("\nContainer run_alphafold arguments:")
  for argument in plan["container_args"]:
    print(f"  {argument}")

  print("\nMount plan:")
  for mount in plan["mounts"]:
    access = "read-only" if mount["read_only"] == "true" else "read-write"
    print(f"  {mount['source']} -> {mount['target']} ({access})")

  print("\nDatabase path status:")
  for entry in plan["database_paths"]:
    print(
        f"  --{entry['flag']}: {entry['status']} "
        f"({entry['expected_type']}) {entry['host_path']}"
    )

  gpu = plan["gpu"]
  print("\nGPU notes:")
  print(f"  use_gpu: {gpu['use_gpu']}")
  print(f"  gpu_devices: {gpu['gpu_devices']}")
  print(f"  effective_gpu_relax: {gpu['effective_gpu_relax']}")
  if gpu["use_gpu"]:
    print("  Docker run requires a working NVIDIA container runtime.")

  if plan["warnings"]:
    print("\nWarnings:")
    for warning in plan["warnings"]:
      print(f"  - {warning}")
  if plan["errors"]:
    print("\nErrors:")
    for error in plan["errors"]:
      print(f"  - {error}")

  print(
      "\nThis helper performed a dry run only: no Docker import, daemon call, "
      "container start, directory creation, or download was attempted."
  )


def main(argv: list[str] | None = None) -> int:
  parser = _build_parser()
  args = parser.parse_args(argv)
  plan, errors, _warnings = _plan(args)
  if args.format == "json":
    print(json.dumps(plan, indent=2, sort_keys=True))
  else:
    _print_text(plan)
  return 1 if errors else 0


if __name__ == "__main__":
  sys.exit(main())
