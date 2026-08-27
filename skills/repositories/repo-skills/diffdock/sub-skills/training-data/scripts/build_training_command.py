#!/usr/bin/env python3
"""Build safe DiffDock training commands without executing them."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Optional


DATASET_DIR_FLAG = {
    "pdbbind": "--pdbbind_dir",
    "moad": "--moad_dir",
    "generalisation": "--moad_dir",
    "distillation": "--moad_dir",
    "pdbsidechain": "--pdbsidechain_dir",
}


def add_if_value(command: list[str], flag: str, value: Optional[object]) -> None:
    if value is None:
        return
    if isinstance(value, str) and value == "":
        return
    command.extend([flag, str(value)])


def add_flag(command: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def readable_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def existing_path(path: Optional[str]) -> Optional[bool]:
    if not path:
        return None
    return Path(path).exists()


def build_score_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = [args.python, "-m", "train"]
    warnings: list[str] = []

    add_if_value(command, "--config", args.config)
    command.extend(["--dataset", args.dataset])

    dataset_flag = DATASET_DIR_FLAG.get(args.dataset)
    if dataset_flag is None:
        warnings.append(f"Unknown score dataset {args.dataset!r}; not adding a dataset-root flag.")
    else:
        add_if_value(command, dataset_flag, args.data_dir)

    add_if_value(command, "--split_train", args.split_train)
    add_if_value(command, "--split_val", args.split_val)
    add_if_value(command, "--split_test", args.split_test)
    add_if_value(command, "--cache_path", args.cache_path)
    add_if_value(command, "--log_dir", args.log_dir)
    add_if_value(command, "--run_name", args.run_name)
    add_if_value(command, "--limit_complexes", args.limit_complexes)
    add_if_value(command, "--n_epochs", args.n_epochs)
    add_if_value(command, "--batch_size", args.batch_size)
    add_if_value(command, "--num_dataloader_workers", args.num_dataloader_workers)
    add_if_value(command, "--val_inference_freq", args.val_inference_freq)
    add_if_value(command, "--inference_steps", args.inference_steps)
    add_if_value(command, "--num_inference_complexes", args.num_inference_complexes)
    add_if_value(command, "--protein_file", args.protein_file)
    add_if_value(command, "--restart_dir", args.restart_dir)
    add_if_value(command, "--restart_ckpt", args.restart_ckpt)
    add_if_value(command, "--pretrain_dir", args.pretrain_dir)
    add_if_value(command, "--pretrain_ckpt", args.pretrain_ckpt)

    if args.dataset in {"pdbbind", "generalisation"}:
        add_if_value(command, "--pdbbind_esm_embeddings_path", args.esm_embeddings_path)
    elif args.dataset in {"moad", "distillation"}:
        add_if_value(command, "--moad_esm_embeddings_path", args.esm_embeddings_path)
        add_if_value(command, "--moad_esm_embeddings_sequences_path", args.esm_embeddings_sequences_path)
    elif args.dataset == "pdbsidechain":
        add_if_value(command, "--pdbsidechain_esm_embeddings_path", args.esm_embeddings_path)
        add_if_value(command, "--pdbsidechain_esm_embeddings_sequences_path", args.esm_embeddings_sequences_path)

    add_flag(command, "--all_atoms", args.all_atoms)
    add_flag(command, "--combined_training", args.combined_training)
    add_flag(command, "--triple_training", args.triple_training)
    add_flag(command, "--unroll_clusters", args.unroll_clusters)
    add_flag(command, "--wandb", args.wandb)
    add_flag(command, "--use_ema", args.use_ema)

    if args.original_model_dir:
        warnings.append("--original-model-dir is ignored for score training; it is used by confidence mode.")

    return command, warnings


def build_confidence_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = [args.python, "-m", "confidence.confidence_train"]
    warnings: list[str] = []

    add_if_value(command, "--config", args.config)
    add_if_value(command, "--original_model_dir", args.original_model_dir)
    add_if_value(command, "--data_dir", args.data_dir)
    add_if_value(command, "--split_train", args.split_train)
    add_if_value(command, "--split_val", args.split_val)
    add_if_value(command, "--split_test", args.split_test)
    add_if_value(command, "--cache_path", args.cache_path)
    add_if_value(command, "--log_dir", args.log_dir)
    add_if_value(command, "--run_name", args.run_name)
    add_if_value(command, "--limit_complexes", args.limit_complexes)
    add_if_value(command, "--n_epochs", args.n_epochs)
    add_if_value(command, "--batch_size", args.batch_size)
    add_if_value(command, "--ckpt", args.ckpt)
    add_if_value(command, "--inference_steps", args.inference_steps)
    add_if_value(command, "--samples_per_complex", args.samples_per_complex)
    add_if_value(command, "--esm_embeddings_path", args.esm_embeddings_path)
    add_if_value(command, "--cache_creation_id", args.cache_creation_id)
    add_if_value(command, "--restart_dir", args.restart_dir)
    add_if_value(command, "--main_metric", args.main_metric)
    add_if_value(command, "--main_metric_goal", args.main_metric_goal)

    for cache_id in args.cache_ids_to_combine or []:
        if "--cache_ids_to_combine" not in command:
            command.append("--cache_ids_to_combine")
        command.append(str(cache_id))

    add_flag(command, "--use_original_model_cache", args.use_original_model_cache)
    add_flag(command, "--transfer_weights", args.transfer_weights)
    add_flag(command, "--balance", args.balance)
    add_flag(command, "--rmsd_prediction", args.rmsd_prediction)
    add_flag(command, "--all_atoms", args.all_atoms)
    add_flag(command, "--wandb", args.wandb)

    if not args.original_model_dir:
        warnings.append("Confidence mode needs --original-model-dir with model_parameters.yml and the selected score checkpoint.")

    return command, warnings


def validation_notes(args: argparse.Namespace) -> dict[str, object]:
    paths = {
        "data_dir_exists": existing_path(args.data_dir),
        "split_train_exists": existing_path(args.split_train),
        "split_val_exists": existing_path(args.split_val),
        "split_test_exists": existing_path(args.split_test),
        "cache_path_exists": existing_path(args.cache_path),
        "log_dir_parent_exists": existing_path(str(Path(args.log_dir).parent) if args.log_dir else None),
        "esm_embeddings_path_exists": existing_path(args.esm_embeddings_path),
        "esm_embeddings_sequences_path_exists": existing_path(args.esm_embeddings_sequences_path),
        "original_model_dir_exists": existing_path(args.original_model_dir),
    }
    notes = [
        "This script prints a command only; it does not run DiffDock training.",
        "Run the dataset and ESM validators before executing heavy training.",
        "Full training imports require Torch/PyG/e3nn/RDKit/ProDy/W&B and often CUDA.",
    ]
    if args.mode == "confidence":
        notes.append("Confidence training can generate ligand-position/RMSD caches by running score-model inference.")
    return {"paths": paths, "notes": notes}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["score", "confidence"], required=True)
    parser.add_argument("--python", default="python")
    parser.add_argument("--dataset", choices=sorted(DATASET_DIR_FLAG), default="pdbbind")
    parser.add_argument("--config", default=None, help="Optional YAML config path to pass through to the training parser.")
    parser.add_argument("--data-dir", default="data/PDBBind_processed")
    parser.add_argument("--split-train", default="data/splits/timesplit_no_lig_overlap_train")
    parser.add_argument("--split-val", default="data/splits/timesplit_no_lig_overlap_val")
    parser.add_argument("--split-test", default="data/splits/timesplit_test")
    parser.add_argument("--cache-path", default=None)
    parser.add_argument("--log-dir", default="workdir")
    parser.add_argument("--run-name", default="disco_planned_run")
    parser.add_argument("--limit-complexes", type=int, default=None)
    parser.add_argument("--n-epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--num-dataloader-workers", type=int, default=None)
    parser.add_argument("--val-inference-freq", type=int, default=None)
    parser.add_argument("--inference-steps", type=int, default=None)
    parser.add_argument("--num-inference-complexes", type=int, default=None)
    parser.add_argument("--samples-per-complex", type=int, default=None)
    parser.add_argument("--protein-file", default=None)
    parser.add_argument("--esm-embeddings-path", default=None)
    parser.add_argument("--esm-embeddings-sequences-path", default=None)
    parser.add_argument("--original-model-dir", default=None)
    parser.add_argument("--ckpt", default=None)
    parser.add_argument("--cache-creation-id", type=int, default=None)
    parser.add_argument("--cache-ids-to-combine", nargs="*", default=None)
    parser.add_argument("--restart-dir", default=None)
    parser.add_argument("--restart-ckpt", default=None)
    parser.add_argument("--pretrain-dir", default=None)
    parser.add_argument("--pretrain-ckpt", default=None)
    parser.add_argument("--main-metric", default=None)
    parser.add_argument("--main-metric-goal", choices=["min", "max"], default=None)
    parser.add_argument("--all-atoms", action="store_true")
    parser.add_argument("--combined-training", action="store_true")
    parser.add_argument("--triple-training", action="store_true")
    parser.add_argument("--unroll-clusters", action="store_true")
    parser.add_argument("--use-original-model-cache", action="store_true")
    parser.add_argument("--transfer-weights", action="store_true")
    parser.add_argument("--balance", action="store_true")
    parser.add_argument("--rmsd-prediction", action="store_true")
    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--use-ema", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print a JSON command manifest instead of shell text.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.cache_path is None:
        args.cache_path = "data/cache" if args.mode == "score" else "data/cacheNew"

    if args.mode == "score":
        command, warnings = build_score_command(args)
    else:
        command, warnings = build_confidence_command(args)

    manifest = {
        "mode": args.mode,
        "command": command,
        "shell_command": readable_command(command),
        "warnings": warnings,
        **validation_notes(args),
    }

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(manifest["shell_command"])
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
