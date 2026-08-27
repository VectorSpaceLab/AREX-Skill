#!/usr/bin/env python3
"""Bundled FastReID training/evaluation entrypoint.

This is a self-contained replacement for FastReID's source-tree training
launcher. It uses public FastReID APIs after making an optional local checkout
importable. The script is safe by default: it refuses to run train/eval unless
`--confirm-run` is supplied, and `--dry-run` only merges the config and prints
selected launch facts.

Examples
--------
Dry-run config merge without training:

python run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --dry-run \
  --config-file <CONFIG_YAML> \
  MODEL.DEVICE cpu MODEL.BACKBONE.PRETRAIN False

Execute eval-only after explicitly confirming the run:

python run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  --eval-only \
  MODEL.WEIGHTS <CHECKPOINT_FILE.pth> MODEL.DEVICE cuda:0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


def _preparse(argv: Sequence[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--confirm-run", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_known_args(argv)


def _add_repo_root(repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    resolved = repo_root.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"--repo-root does not exist or is not a directory: {resolved}")
    sys.path.insert(0, str(resolved))
    return resolved


def _build_parser(default_argument_parser, pre: argparse.Namespace) -> argparse.ArgumentParser:
    parser = default_argument_parser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=pre.repo_root,
        help="Optional FastReID checkout root to add to sys.path before importing package modules.",
    )
    parser.add_argument(
        "--confirm-run",
        action="store_true",
        default=pre.confirm_run,
        help="Actually run training/evaluation. Without this flag the script exits before launch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=pre.dry_run,
        help="Merge and print config/launch facts without training, evaluating, downloading, or writing checkpoints.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=pre.json,
        help="With --dry-run, print JSON instead of text.",
    )
    return parser


def _setup_cfg(args, get_cfg, default_setup=None):
    cfg = get_cfg()
    cfg.merge_from_file(args.config_file)
    cfg.merge_from_list(args.opts)
    cfg.freeze()
    if default_setup is not None:
        default_setup(cfg, args)
    return cfg


def _dry_run(args, get_cfg) -> int:
    cfg = _setup_cfg(args, get_cfg, default_setup=None)
    payload = {
        "will_execute": False,
        "mode": "eval-only" if args.eval_only else "train",
        "config_file": args.config_file,
        "num_gpus": args.num_gpus,
        "num_machines": args.num_machines,
        "machine_rank": args.machine_rank,
        "dist_url": args.dist_url,
        "model_device": cfg.MODEL.DEVICE,
        "model_meta_architecture": cfg.MODEL.META_ARCHITECTURE,
        "datasets_names": list(cfg.DATASETS.NAMES),
        "datasets_tests": list(cfg.DATASETS.TESTS),
        "output_dir": cfg.OUTPUT_DIR,
        "weights": cfg.MODEL.WEIGHTS,
        "opts": list(args.opts),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Dry run only; no FastReID training/evaluation was launched.")
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


def _fallback_help() -> None:
    parser = argparse.ArgumentParser(
        description="Bundled FastReID training/evaluation entrypoint. Import FastReID or pass --repo-root before real use.",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional FastReID checkout root to add to sys.path.")
    parser.add_argument("--confirm-run", action="store_true", help="Actually run training/evaluation.")
    parser.add_argument("--dry-run", action="store_true", help="Merge config and print launch facts without train/eval.")
    parser.add_argument("--json", action="store_true", help="With --dry-run, print JSON.")
    parser.add_argument("--config-file", metavar="FILE", help="FastReID config file path.")
    parser.add_argument("--resume", action="store_true", help="Resume from OUTPUT_DIR/last_checkpoint.")
    parser.add_argument("--eval-only", action="store_true", help="Run evaluation only; requires MODEL.WEIGHTS override.")
    parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs per machine.")
    parser.add_argument("--num-machines", type=int, default=1, help="Total number of machines.")
    parser.add_argument("--machine-rank", type=int, default=0, help="Rank of this machine.")
    parser.add_argument("--dist-url", default=None, help="Distributed initialization URL.")
    parser.add_argument("opts", nargs=argparse.REMAINDER, help="Trailing FastReID KEY VALUE config overrides.")
    parser.print_help()


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    pre, _ = _preparse(raw)
    _add_repo_root(pre.repo_root)

    try:
        from fastreid.config import get_cfg
        from fastreid.engine import DefaultTrainer, default_argument_parser, default_setup, launch
        from fastreid.utils.checkpoint import Checkpointer
    except Exception as exc:  # pragma: no cover - environment dependent.
        if "--help" in raw or "-h" in raw:
            _fallback_help()
            return 0
        raise SystemExit(
            "Could not import FastReID. Provide --repo-root for a local checkout or "
            f"install/make the fastreid package importable. Original error: {type(exc).__name__}: {exc}"
        ) from exc

    parser = _build_parser(default_argument_parser, pre)
    args = parser.parse_args(raw)
    _add_repo_root(args.repo_root)

    if not args.config_file:
        parser.error("--config-file is required for FastReID training/evaluation")
    if args.eval_only and "MODEL.WEIGHTS" not in args.opts:
        # The config may still contain MODEL.WEIGHTS, but force explicitness for this bundled helper.
        parser.error("--eval-only requires an explicit MODEL.WEIGHTS <checkpoint> override in opts")
    if args.dry_run:
        return _dry_run(args, get_cfg)
    if not args.confirm_run:
        parser.error("refusing to launch a train/eval job without --confirm-run; use --dry-run for config inspection")

    def setup(run_args):
        return _setup_cfg(run_args, get_cfg, default_setup=default_setup)

    def run_main(run_args):
        cfg = setup(run_args)
        if run_args.eval_only:
            cfg.defrost()
            cfg.MODEL.BACKBONE.PRETRAIN = False
            model = DefaultTrainer.build_model(cfg)
            Checkpointer(model).load(cfg.MODEL.WEIGHTS)
            return DefaultTrainer.test(cfg, model)
        trainer = DefaultTrainer(cfg)
        trainer.resume_or_load(resume=run_args.resume)
        return trainer.train()

    return launch(
        run_main,
        args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,),
    )


if __name__ == "__main__":
    raise SystemExit(main())
