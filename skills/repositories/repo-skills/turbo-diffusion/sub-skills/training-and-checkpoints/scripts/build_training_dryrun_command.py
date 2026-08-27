#!/usr/bin/env python3
"""Build a TurboDiffusion training dry-run command without executing it."""

from __future__ import annotations

import argparse
import glob
import shlex
import sys
from pathlib import Path


EXPERIMENTS = {
    ("registry_sla", "1.3B"): "wan2pt1_1pt3B_res480p_t2v_SLA",
    ("registry_sla", "14B"): "wan2pt1_14B_res480p_t2v_SLA",
    ("registry_distill", "1.3B"): "wan2pt1_1pt3B_res480p_t2v_rCM",
    ("registry_distill", "14B"): "wan2pt1_14B_res480p_t2v_rCM",
}

TEACHERS = {
    "1.3B": "Wan2.1-T2V-1.3B.dcp",
    "14B": "Wan2.1-T2V-14B.dcp",
}


def q(value: object) -> str:
    return shlex.quote(str(value))


def join_path(root: str, leaf: str) -> str:
    return str(Path(root) / leaf)


def render_command(env: list[tuple[str, str]], argv: list[str], one_line: bool) -> str:
    tokens = [f"{key}={q(value)}" for key, value in env] + [q(part) for part in argv]
    if one_line:
        return " ".join(tokens)

    if len(tokens) <= 3:
        return " ".join(tokens)

    lines: list[str] = []
    prefix = tokens[: len(env)]
    rest = tokens[len(env) :]
    if prefix:
        lines.append(" ".join(prefix) + " \\")
        if rest:
            lines.append("  " + rest[0] + " \\")
            rest = rest[1:]
    elif rest:
        lines.append(rest[0] + " \\")
        rest = rest[1:]

    for i, token in enumerate(rest):
        suffix = " \\" if i < len(rest) - 1 else ""
        lines.append("  " + token + suffix)
    return "\n".join(lines)


def validate_layout(args: argparse.Namespace, paths: dict[str, str]) -> int:
    errors: list[str] = []
    for label in ["config_path", "teacher_dcp", "vae_path", "text_encoder_path", "negative_embed_path"]:
        value = paths[label]
        if not Path(value).exists():
            errors.append(f"missing {label}: {value}")

    matches = glob.glob(paths["tar_pattern"])
    if not matches:
        errors.append(f"tar_pattern matched no shards: {paths['tar_pattern']}")

    output_root = Path(args.output_root)
    if output_root.exists() and not output_root.is_dir():
        errors.append(f"output_root exists but is not a directory: {args.output_root}")

    if errors:
        print("Layout validation failed:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        return 2

    print("Layout validation passed:", file=sys.stderr)
    print(f"  - shard matches: {len(matches)}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboDiffusion torchrun dry-run command for rCM/SLA training setup. "
            "The generated command includes --dryrun; this helper never executes training."
        )
    )
    parser.add_argument("--registry", choices=["registry_sla", "registry_distill"], default="registry_sla")
    parser.add_argument("--model-size", choices=["1.3B", "14B"], default="1.3B")
    parser.add_argument("--experiment", help="Override derived experiment name.")
    parser.add_argument(
        "--full-experiment-name",
        action="store_true",
        help="Use the non-debug experiment name while still rendering a --dryrun command.",
    )
    parser.add_argument("--nproc-per-node", type=int, default=1, help="torchrun process count; default is safe for dry-run.")
    parser.add_argument("--master-port", type=int, help="Optional torchrun master port.")
    parser.add_argument("--torchrun", default="torchrun", help="torchrun executable name/path.")
    parser.add_argument("--package-source-dir", default="turbodiffusion", help="Source-layout package directory for PYTHONPATH/config defaults.")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prefix command with PYTHONPATH.")
    parser.add_argument("--config-path", help="Override config registry file path.")
    parser.add_argument("--output-root", default="outputs", help="IMAGINAIRE_OUTPUT_ROOT value.")
    parser.add_argument("--checkpoint-root", default="assets/checkpoints", help="Root containing teacher DCP, VAE, text encoder, and negative embedding.")
    parser.add_argument("--teacher-dcp", help="Override teacher DCP directory path.")
    parser.add_argument("--vae-path", help="Override Wan2.1 VAE checkpoint path.")
    parser.add_argument("--text-encoder-path", help="Override umT5 text encoder checkpoint path.")
    parser.add_argument("--negative-embed-path", help="Override negative embedding checkpoint path.")
    parser.add_argument(
        "--dataset-root",
        default="assets/datasets/Wan2.1_14B_480p_16:9_Euler-step100_shift-3.0_cfg-5.0_seed-0_250K",
        help="Dataset root used to derive shard glob.",
    )
    parser.add_argument("--tar-pattern", help="Override WebDataset shard glob.")
    parser.add_argument(
        "--extra-override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Append an extra config override after the -- separator; can be repeated.",
    )
    parser.add_argument("--validate-layout", action="store_true", help="Check paths/globs locally without running training.")
    parser.add_argument("--one-line", action="store_true", help="Print command on one line.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    base_experiment = args.experiment or EXPERIMENTS[(args.registry, args.model_size)]
    if args.experiment:
        experiment = args.experiment
    elif args.full_experiment_name:
        experiment = base_experiment
    else:
        experiment = base_experiment + "_debug"

    config_path = args.config_path or join_path(args.package_source_dir, f"rcm/configs/{args.registry}.py")
    teacher_dcp = args.teacher_dcp or join_path(args.checkpoint_root, TEACHERS[args.model_size])
    vae_path = args.vae_path or join_path(args.checkpoint_root, "Wan2.1_VAE.pth")
    text_encoder_path = args.text_encoder_path or join_path(args.checkpoint_root, "models_t5_umt5-xxl-enc-bf16.pth")
    negative_embed_path = args.negative_embed_path or join_path(args.checkpoint_root, "umT5_wan_negative_emb.pt")
    tar_pattern = args.tar_pattern or join_path(args.dataset_root, "shard*.tar")

    paths = {
        "config_path": config_path,
        "teacher_dcp": teacher_dcp,
        "vae_path": vae_path,
        "text_encoder_path": text_encoder_path,
        "negative_embed_path": negative_embed_path,
        "tar_pattern": tar_pattern,
    }

    if args.validate_layout:
        status = validate_layout(args, paths)
        if status:
            return status

    env: list[tuple[str, str]] = [("IMAGINAIRE_OUTPUT_ROOT", args.output_root)]
    if not args.no_pythonpath:
        env.insert(0, ("PYTHONPATH", args.package_source_dir))

    argv = [args.torchrun, f"--nproc_per_node={args.nproc_per_node}"]
    if args.master_port is not None:
        argv.append(f"--master_port={args.master_port}")
    argv.extend(
        [
            "-m",
            "scripts.train",
            f"--config={config_path}",
            "--dryrun",
            "--",
            f"experiment={experiment}",
            f"model.config.teacher_ckpt={teacher_dcp}",
            f"model.config.tokenizer.vae_pth={vae_path}",
            f"model.config.text_encoder_path={text_encoder_path}",
            f"model.config.neg_embed_path={negative_embed_path}",
            f"dataloader_train.tar_path_pattern={tar_pattern}",
        ]
    )
    argv.extend(args.extra_override)

    print(render_command(env, argv, args.one_line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
