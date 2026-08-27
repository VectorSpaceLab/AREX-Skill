#!/usr/bin/env python3
"""Print a reusable CogDL experiment/trainer config template."""

from __future__ import annotations

import argparse
import json
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="cora")
    parser.add_argument("--model", default="gcn")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--cpu", action="store_true", help="set CPU mode in the template")
    parser.add_argument("--devices", nargs="+", type=int, default=[0])
    parser.add_argument("--checkpoint-path", default="checkpoints/model.pt")
    parser.add_argument("--save-emb-path", default=None)
    parser.add_argument("--load-emb-path", default=None)
    parser.add_argument("--log-path", default="runs")
    parser.add_argument("--logger", default=None)
    parser.add_argument("--project", default="cogdl-exp")
    parser.add_argument("--seed", nargs="+", type=int, default=[1])
    parser.add_argument("--split", nargs="+", type=int, default=[0])
    parser.add_argument("--distributed", action="store_true")
    parser.add_argument("--cpu-inference", action="store_true")
    parser.add_argument("--resume-training", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--actnn", action="store_true")
    parser.add_argument("--use-best-config", action="store_true")
    parser.add_argument("--n-trials", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a pretty dict")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from cogdl.wrappers.default_match import get_wrappers_name

    mw, dw = get_wrappers_name(args.model) or (None, None)
    payload = {
        "experiment_kwargs": {
            "dataset": args.dataset,
            "model": args.model,
            "seed": args.seed,
            "split": args.split,
            "epochs": args.epochs,
            "cpu": args.cpu,
            "devices": args.devices,
            "resume_training": args.resume_training,
            "use_best_config": args.use_best_config,
            "n_trials": args.n_trials,
        },
        "trainer_kwargs": {
            "checkpoint_path": args.checkpoint_path,
            "save_emb_path": args.save_emb_path,
            "load_emb_path": args.load_emb_path,
            "log_path": args.log_path,
            "logger": args.logger,
            "project": args.project,
            "distributed_training": args.distributed,
            "cpu_inference": args.cpu_inference,
            "fp16": args.fp16,
            "actnn": args.actnn,
        },
        "wrapper_hint": {"mw": mw, "dw": dw},
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        pprint(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
