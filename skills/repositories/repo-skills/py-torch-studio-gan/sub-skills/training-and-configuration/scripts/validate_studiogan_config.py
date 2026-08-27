#!/usr/bin/env python3
"""Validate a StudioGAN YAML/config flag combination without training.

This helper imports the StudioGAN ``src/config.py`` module from an explicit
checkout, injects parser-equivalent RUN defaults, computes a caller-declared GPU
world size, and calls ``Configurations.check_compatability``. It does not start
training, prepare HDF5 files, download datasets or weights, contact logging
services, or create output directories.
"""

from __future__ import annotations

import argparse
import importlib
import shlex
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional

VALID_METRICS = {"is", "fid", "prdc", "none"}
VALID_RESIZERS = {"wo_resize", "nearest", "bilinear", "bicubic", "lanczos"}
VALID_POST_RESIZERS = {"legacy", "clean", "friendly"}
VALID_BACKBONES = {
    "InceptionV3_tf",
    "InceptionV3_torch",
    "ResNet50_torch",
    "SwAV_torch",
    "DINO_torch",
    "Swin-T_torch",
}


class ValidationError(RuntimeError):
    """Raised for user-correctable validation errors."""


def normalize_path(value: Optional[str], *, base: Optional[Path] = None) -> Optional[Path]:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve(strict=False)


def visible_gpu_count(value: str) -> int:
    text = value.strip()
    if not text:
        return 1
    if "," in text:
        return max(1, len([item for item in text.split(",") if item.strip()]))
    if text.isdigit():
        number = int(text)
        # In command builders, "0" usually means device id 0. In validators,
        # "4" often means four visible GPUs. Treat positive integers as counts
        # and zero as the common single-device id.
        return max(1, number)
    return 1


def normalize_metrics(metrics: List[str]) -> List[str]:
    normalized = [item.lower() for item in metrics]
    invalid = sorted(set(normalized) - VALID_METRICS)
    if invalid:
        raise ValidationError("unsupported metrics: " + ", ".join(invalid) + " (expected is, fid, prdc, or none)")
    if "none" in normalized and len(normalized) > 1:
        raise ValidationError("use -metrics none by itself; do not combine none with metric names")
    return normalized


def ensure_pkg_resources_parse_version() -> None:
    """Provide the small pkg_resources surface StudioGAN imports when setuptools is absent."""
    if "pkg_resources" in sys.modules:
        return
    try:
        importlib.import_module("pkg_resources")
        return
    except ModuleNotFoundError:
        try:
            from packaging.version import parse as parse_version  # type: ignore
        except Exception:
            return
        module = types.ModuleType("pkg_resources")
        module.parse_version = parse_version  # type: ignore[attr-defined]
        sys.modules["pkg_resources"] = module


def import_studiogan_config(repo_root: Path):
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    ensure_pkg_resources_parse_version()
    existing = sys.modules.get("config")
    if existing is not None:
        existing_file = Path(getattr(existing, "__file__", "")).resolve(strict=False)
        if existing_file != (src_dir / "config.py").resolve(strict=False):
            del sys.modules["config"]
    return importlib.import_module("config")


def make_run_cfgs(args: argparse.Namespace, cfg_path: Path, data_dir: Optional[Path], save_dir: Path,
                  checkpoint: Optional[Path], train: bool, metrics: List[str]) -> Dict[str, Any]:
    return {
        "entity": args.entity,
        "project": args.project,
        "cfg_file": str(cfg_path),
        "data_dir": str(data_dir) if data_dir is not None else None,
        "save_dir": str(save_dir),
        "ckpt_dir": str(checkpoint) if checkpoint is not None else None,
        "load_best": args.load_best,
        "seed": args.seed,
        "distributed_data_parallel": args.ddp,
        "backend": args.backend,
        "total_nodes": args.total_nodes,
        "current_node": args.current_node,
        "num_workers": args.num_workers,
        "synchronized_bn": args.sync_bn,
        "mixed_precision": args.mixed_precision,
        "truncation_factor": args.truncation_factor,
        "truncation_cutoff": args.truncation_cutoff,
        "batch_statistics": args.batch_stat,
        "standing_statistics": args.standing_stats,
        "standing_max_batch": args.standing_max,
        "standing_step": args.standing_step,
        "freezeD": args.freeze_d,
        "langevin_sampling": args.langevin,
        "langevin_rate": args.lgv_rate,
        "langevin_noise_std": args.lgv_std,
        "langevin_decay": args.lgv_decay,
        "langevin_decay_steps": args.lgv_decay_steps,
        "langevin_steps": args.lgv_steps,
        "train": train,
        "load_train_hdf5": args.hdf5,
        "load_data_in_memory": args.load_in_memory,
        "eval_metrics": metrics,
        "pre_resizer": args.pre_resizer,
        "post_resizer": args.post_resizer,
        "num_eval": args.num_eval,
        "save_real_images": args.save_real,
        "save_fake_images": args.save_fake,
        "save_fake_images_num": args.fake_count,
        "vis_fake_images": args.visualize,
        "k_nearest_neighbor": args.knn,
        "interpolation": args.interpolation,
        "frequency_analysis": args.frequency,
        "tsne_analysis": args.tsne,
        "intra_class_fid": args.ifid,
        "GAN_train": args.gan_train,
        "GAN_test": args.gan_test,
        "resume_classifier_train": args.resume_classifier_train,
        "semantic_factorization": args.sefa,
        "num_semantic_axis": args.sefa_axis,
        "maximum_variations": args.sefa_max,
        "empty_cache": args.empty_cache,
        "print_freq": args.print_freq,
        "save_freq": args.save_freq,
        "eval_backbone": args.eval_backbone,
        "ref_dataset": args.ref,
        "calc_is_ref_dataset": args.calc_is_ref_dataset,
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a StudioGAN YAML file plus planned src/main.py flags by calling "
            "Configurations.check_compatability without running training."
        )
    )
    parser.add_argument("--repo-root", required=True, help="Path to a StudioGAN checkout containing src/main.py and src/config.py.")
    parser.add_argument("--cfg", required=True, help="StudioGAN YAML config path; relative paths resolve under --repo-root.")
    parser.add_argument("--data-dir", help="Dataset root to inject as native -data. Required by StudioGAN unless saving fake images only.")
    parser.add_argument("--save-dir", default=".", help="Output root to inject as native -save. Default: current directory token.")
    parser.add_argument("--checkpoint", help="Checkpoint directory to inject as native -ckpt.")
    parser.add_argument("--dry-run-no-path-check", action="store_true", help="Skip repo/config path existence checks before importing config.py.")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--train", action="store_true", help="Validate as a training command. This is the default unless --eval-only is used.")
    mode.add_argument("--eval-only", action="store_true", help="Validate as an eval/analysis command without native -t.")

    parser.add_argument("--gpus", default="1", help="Visible GPU count or CUDA_VISIBLE_DEVICES-like list. Default: 1.")
    parser.add_argument("--metrics", nargs="+", default=["fid"], help="Native -metrics values: is fid prdc none. Default: fid.")
    parser.add_argument("--ddp", action="store_true", help="Inject native -DDP/--distributed_data_parallel.")
    parser.add_argument("--backend", default="nccl", help="Native --backend value. Default: nccl.")
    parser.add_argument("--total-nodes", type=int, default=1, help="Native -tn/--total_nodes. Default: 1.")
    parser.add_argument("--current-node", type=int, default=0, help="Native -cn/--current_node. Default: 0.")
    parser.add_argument("--num-workers", type=int, default=8, help="Native --num_workers. Default: 8.")
    parser.add_argument("--sync-bn", action="store_true", help="Inject native -sync_bn.")
    parser.add_argument("--mixed-precision", action="store_true", help="Inject native -mpc.")
    parser.add_argument("--hdf5", action="store_true", help="Inject native -hdf5.")
    parser.add_argument("--load-in-memory", action="store_true", help="Inject native -l; requires --hdf5.")
    parser.add_argument("--pre-resizer", default="wo_resize", choices=sorted(VALID_RESIZERS), help="Native --pre_resizer. Default: wo_resize.")
    parser.add_argument("--post-resizer", default="legacy", choices=sorted(VALID_POST_RESIZERS), help="Native --post_resizer. Default: legacy.")
    parser.add_argument("--eval-backbone", default="InceptionV3_tf", choices=sorted(VALID_BACKBONES), help="Native --eval_backbone. Default: InceptionV3_tf.")
    parser.add_argument("--ref", default="train", help="Native -ref/--ref_dataset. Common values: train, valid, test.")
    parser.add_argument("--freeze-d", type=int, default=-1, help="Native --freezeD value. Default: -1.")
    parser.add_argument("--print-freq", type=int, default=100, help="Native --print_freq. Default: 100.")
    parser.add_argument("--save-freq", type=int, default=2000, help="Native --save_freq. Default: 2000.")
    parser.add_argument("--seed", type=int, default=-1, help="Native --seed. Default: -1.")
    parser.add_argument("--num-eval", type=int, default=1, help="Native --num_eval. Default: 1.")
    parser.add_argument("--entity", default=None, help="Native --entity value for wandb metadata; not contacted by this validator.")
    parser.add_argument("--project", default=None, help="Native --project value for wandb metadata; not contacted by this validator.")
    parser.add_argument("--load-best", action="store_true", help="Inject native -best.")
    parser.add_argument("--empty-cache", action="store_true", help="Inject native -empty_cache.")
    parser.add_argument("--calc-is-ref-dataset", action="store_true", help="Inject native --calc_is_ref_dataset.")

    analysis = parser.add_argument_group("optional eval/analysis flags for compatibility checks")
    analysis.add_argument("--save-real", action="store_true", help="Inject native -sr.")
    analysis.add_argument("--save-fake", action="store_true", help="Inject native -sf.")
    analysis.add_argument("--fake-count", type=int, default=1, help="Native -sf_num. Default: 1.")
    analysis.add_argument("--visualize", action="store_true", help="Inject native -v.")
    analysis.add_argument("--knn", action="store_true", help="Inject native -knn.")
    analysis.add_argument("--interpolation", action="store_true", help="Inject native -itp.")
    analysis.add_argument("--frequency", action="store_true", help="Inject native -fa.")
    analysis.add_argument("--tsne", action="store_true", help="Inject native -tsne.")
    analysis.add_argument("--ifid", action="store_true", help="Inject native -ifid.")
    analysis.add_argument("--gan-train", action="store_true", help="Inject native --GAN_train.")
    analysis.add_argument("--gan-test", action="store_true", help="Inject native --GAN_test.")
    analysis.add_argument("--resume-classifier-train", action="store_true", help="Inject native -resume_ct.")
    analysis.add_argument("--sefa", action="store_true", help="Inject native -sefa.")
    analysis.add_argument("--sefa-axis", type=int, default=-1, help="Native -sefa_axis. Default: -1.")
    analysis.add_argument("--sefa-max", type=float, default=-1, help="Native -sefa_max. Default: -1.")
    analysis.add_argument("--batch-stat", action="store_true", help="Inject native -batch_stat.")
    analysis.add_argument("--standing-stats", action="store_true", help="Inject native -std_stat.")
    analysis.add_argument("--standing-max", type=int, default=-1, help="Native -std_max. Default: -1.")
    analysis.add_argument("--standing-step", type=int, default=-1, help="Native -std_step. Default: -1.")
    analysis.add_argument("--truncation-factor", type=float, default=-1.0, help="Native --truncation_factor. Default: -1.0.")
    analysis.add_argument("--truncation-cutoff", type=float, default=None, help="Native --truncation_cutoff.")
    analysis.add_argument("--langevin", action="store_true", help="Inject native -lgv.")
    analysis.add_argument("--lgv-rate", type=float, default=-1, help="Native -lgv_rate. Default: -1.")
    analysis.add_argument("--lgv-std", type=float, default=-1, help="Native -lgv_std. Default: -1.")
    analysis.add_argument("--lgv-decay", type=float, default=-1, help="Native -lgv_decay. Default: -1.")
    analysis.add_argument("--lgv-decay-steps", type=int, default=-1, help="Native -lgv_decay_steps. Default: -1.")
    analysis.add_argument("--lgv-steps", type=int, default=-1, help="Native -lgv_steps. Default: -1.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        metrics = normalize_metrics(args.metrics)
        repo_root = normalize_path(args.repo_root)
        assert repo_root is not None
        cfg_path = normalize_path(args.cfg, base=repo_root)
        data_dir = normalize_path(args.data_dir)
        save_dir = normalize_path(args.save_dir)
        checkpoint = normalize_path(args.checkpoint)
        assert cfg_path is not None and save_dir is not None

        if args.total_nodes <= 0:
            raise ValidationError("--total-nodes must be positive")
        if args.current_node < 0:
            raise ValidationError("--current-node must be non-negative")
        if args.print_freq <= 0 or args.save_freq <= 0:
            raise ValidationError("--print-freq and --save-freq must be positive")
        if args.fake_count <= 0:
            raise ValidationError("--fake-count must be positive")

        if not args.dry_run_no_path_check:
            if not repo_root.exists() or not repo_root.is_dir():
                raise ValidationError(f"--repo-root is not a directory: {repo_root}")
            if not (repo_root / "src" / "main.py").is_file():
                raise ValidationError(f"--repo-root does not contain src/main.py: {repo_root}")
            if not (repo_root / "src" / "config.py").is_file():
                raise ValidationError(f"--repo-root does not contain src/config.py: {repo_root}")
            if not cfg_path.is_file():
                raise ValidationError(f"--cfg is not a file: {cfg_path}")

        train = not args.eval_only
        world_size = visible_gpu_count(args.gpus) * args.total_nodes
        run_cfgs = make_run_cfgs(args, cfg_path, data_dir, save_dir, checkpoint, train, metrics)

        cfg_module = import_studiogan_config(repo_root)
        cfgs = cfg_module.Configurations(str(cfg_path))
        cfgs.update_cfgs(run_cfgs, super="RUN")
        cfgs.OPTIMIZATION.world_size = world_size
        cfgs.check_compatability()

        print("OK: StudioGAN configuration compatibility checks passed.")
        print(f"summary: cfg={shlex.quote(str(cfg_path))} train={train} world_size={world_size} metrics={' '.join(metrics)}")
        print("NOTE: this validator did not train, build HDF5 files, download data or weights, contact wandb, or create output directories.")
        return 0
    except ValidationError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
    except Exception as exc:  # noqa: BLE001 - surface concise native/import assertions to users.
        parser.exit(status=2, message=f"error: StudioGAN config validation failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
