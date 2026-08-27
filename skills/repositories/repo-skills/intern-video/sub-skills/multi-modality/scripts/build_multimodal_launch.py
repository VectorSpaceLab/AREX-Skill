#!/usr/bin/env python3
"""Print safe InternVideo2 multi-modality launch skeletons without submitting jobs."""
from __future__ import annotations

import argparse
import shlex


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def default_jobname(branch: str, task: str) -> str:
    return f"multi-{branch}-{task}"


def resolve_entry(branch: str, task: str) -> str | None:
    if task == "demo":
        return None
    if branch == "stage2":
        return "tasks/pretrain.py"
    if task == "pretrain":
        return "tasks_clip/pretrain.py"
    return "tasks_clip/retrieval.py"


def build_override_args(task: str, pretrained: str | None, extra_model_args: list[str]) -> list[str]:
    overrides: list[str] = []
    if task in {"evaluate", "retrieval"}:
        overrides += ["evaluate", "True"]
        if pretrained:
            overrides += ["pretrained_path", pretrained]
    elif pretrained:
        overrides += ["pretrained_path", pretrained]
    overrides += extra_model_args
    return overrides


def print_demo_note(config: str | None) -> None:
    print("# Demo retrieval is a local inference path; it never submits a job.")
    print("export PYTHONPATH=$PWD:$PYTHONPATH")
    if config:
        print(f"# Load the demo config from: {config}")
    print("# Fill the demo config with tokenizer and checkpoint paths before loading demo/utils.py.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a safe InternVideo2 multi-modality launch skeleton.")
    parser.add_argument("--task", choices=["pretrain", "evaluate", "retrieval", "demo"], required=True)
    parser.add_argument("--branch", choices=["stage2", "clip"], default="stage2")
    parser.add_argument("--config", help="Config path relative to the multi_modality directory or an absolute path.")
    parser.add_argument("--pretrained", help="Checkpoint path for evaluation/retrieval.")
    parser.add_argument("--output-dir", default=None, help="Override output directory. Defaults to outputs/<jobname>.")
    parser.add_argument("--jobname", default=None, help="Conceptual job name used by the dry-run tools/run.py line.")
    parser.add_argument("--model-args", default="", help="Extra config overrides that should be appended as key/value pairs.")
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--gpus-per-node", type=int, default=1)
    parser.add_argument("--cpus-per-task", type=int, default=16)
    parser.add_argument("--partition", default="video")
    parser.add_argument("--no-slurm", action="store_true", help="Print a local torchrun skeleton instead of an srun wrapper.")
    parser.add_argument("--vl-exp-dir", default="${VL_EXP_DIR}", help="Conceptual staging root used by tools/run.py notes.")
    args = parser.parse_args()

    if args.task != "demo" and not args.config:
        parser.error("--config is required unless --task demo is selected")

    jobname = args.jobname or default_jobname(args.branch, args.task)
    output_dir = args.output_dir or f"outputs/{jobname}"
    pretrained = args.pretrained or ("<checkpoint-path>" if args.task in {"evaluate", "retrieval"} else None)
    extra_model_args = shlex.split(args.model_args) if args.model_args else []

    print("# This helper only prints command skeletons; it never submits jobs.")
    print("export MASTER_PORT=$((12000 + $RANDOM % 20000))")
    print("export OMP_NUM_THREADS=1")

    if args.task == "demo":
        print_demo_note(args.config)
        return 0

    entry = resolve_entry(args.branch, args.task)
    assert entry is not None
    overrides = build_override_args(args.task, pretrained, extra_model_args)
    direct_model_args = ["output_dir", output_dir, *overrides]

    if args.branch == "stage2":
        dry_run_args = ["python", "tools/run.py", "--jobname", jobname, "--task", "pretrain", "--config", args.config, "--nnodes", str(args.nodes), "--ngpus", str(args.gpus_per_node)]
        if args.no_slurm:
            dry_run_args.append("--no_slurm")
        if overrides:
            dry_run_args += ["--model_args", shell_join([str(x) for x in overrides])]
        print("# tools/run.py dry-run (concept only; do not execute):")
        print(f"# tools/run.py would stage code/output under {args.vl_exp_dir}/{jobname} before calling torchrun.")
        print(shell_join(dry_run_args))
    else:
        print("# CLIP branch uses dedicated shell launchers; the direct launcher skeleton below is the safe path.")

    print("# Direct launcher skeleton:")
    print("export PYTHONPATH=$PWD:$PYTHONPATH")
    if args.no_slurm:
        direct = [
            "torchrun",
            f"--nnodes={args.nodes}",
            f"--nproc_per_node={args.gpus_per_node}",
            "--rdzv_id=12345",
            "--rdzv_backend=c10d",
            "--rdzv_endpoint=localhost:${MASTER_PORT}",
            entry,
            args.config,
            *direct_model_args,
        ]
    else:
        direct = [
            "srun",
            "-p",
            args.partition,
            f"-n{args.nodes}",
            f"--gres=gpu:{args.gpus_per_node}",
            "--ntasks-per-node=1",
            f"--cpus-per-task={args.cpus_per_task}",
            "bash",
            "torchrun.sh",
            f"--nnodes={args.nodes}",
            f"--nproc_per_node={args.gpus_per_node}",
            "--rdzv_backend=c10d",
            entry,
            args.config,
            *direct_model_args,
        ]
    print(shell_join(direct))
    print("# Review config path, checkpoint family, output_dir, PYTHONPATH, and backend readiness before execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
