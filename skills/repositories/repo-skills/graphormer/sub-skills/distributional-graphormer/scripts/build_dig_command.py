#!/usr/bin/env python3
"""Render safe command sketches for Distributional Graphormer workflows.

The helper does not train, sample, or download anything. It prints a reviewed
command sketch or a reference-only sketch for the DiG subprojects.
"""

from __future__ import annotations

import argparse
import shlex
from typing import List, Sequence, Tuple


def quote_command(parts: Sequence[str], gpu_ids: str | None) -> str:
    rendered = " \\\n  ".join(shlex.quote(str(part)) for part in parts)
    if gpu_ids:
        return f"CUDA_VISIBLE_DEVICES={shlex.quote(gpu_ids)} {rendered}"
    return rendered


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render command sketches for the Distributional Graphormer (DiG) "
            "subprojects without executing any workflow."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=(
            "catalyst-train",
            "catalyst-sample",
            "catalyst-density",
            "property-train",
            "property-sample",
            "protein-inference",
            "protein-ligand-single",
            "protein-ligand-full-eval",
        ),
        help="DiG workflow to render.",
    )
    parser.add_argument(
        "--gpu-ids",
        default=None,
        help="Optional CUDA_VISIBLE_DEVICES value to prefix onto the command.",
    )
    parser.add_argument(
        "--num-gpus",
        type=positive_int,
        default=1,
        help="Number of GPUs used in distributed DiG training workflows.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=2,
        help="Per-GPU batch size used in the rendered training workflow.",
    )
    parser.add_argument(
        "--save-dir",
        default="./ckpts",
        help="Checkpoint or output directory used by the rendered workflow.",
    )
    parser.add_argument(
        "--data-root",
        default="./dataset",
        help="Top-level dataset directory used by the rendered workflow.",
    )
    parser.add_argument(
        "--checkpoint",
        default="checkpoints/checkpoint.pt",
        help="Checkpoint path used by the protein or protein-ligand workflows.",
    )
    parser.add_argument(
        "--feature-path",
        default="./dataset/<protein>.pkl",
        help="Protein feature pickle used by the protein inference sketch.",
    )
    parser.add_argument(
        "--fasta-path",
        default="./dataset/<protein>.fasta",
        help="Protein FASTA path used by the protein inference sketch.",
    )
    parser.add_argument(
        "--output-name",
        default="<output-name>",
        help="Protein inference output name.",
    )
    parser.add_argument(
        "--output-prefix",
        default="./output/",
        help="Protein inference output prefix.",
    )
    parser.add_argument(
        "--num-samples",
        type=positive_int,
        default=1,
        help="Number of protein samples to render.",
    )
    parser.add_argument(
        "--pdbid",
        default="<pdbid>",
        help="Protein-ligand single-datapoint target PDB ID.",
    )
    parser.add_argument(
        "--number",
        type=positive_int,
        default=50,
        help="Protein-ligand single-datapoint sample count.",
    )
    parser.add_argument(
        "--num-atoms",
        type=positive_int,
        default=10,
        help="Property-guided workflow atom count hint.",
    )
    parser.add_argument(
        "--target-bandgap",
        default="-1",
        help="Property-guided target bandgap interval.",
    )
    parser.add_argument(
        "--z-offset",
        type=float,
        default=0.0,
        help="Catalyst density z-offset used by the density workflow.",
    )
    parser.add_argument(
        "--master-port",
        default="10086",
        help="Distributed master port used in the catalyst/property sketches.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed value used in the rendered sketches.",
    )
    return parser


def render_catalyst(args: argparse.Namespace, mode: str) -> Tuple[str, List[str]]:
    criterion = "oc_kde"
    valid_subset = "grid-30457"
    best_metric = "kde_kl"
    density_offset = []
    if mode == "catalyst-density":
        criterion = "flow_ode_calc_density"
        best_metric = "loss"
        density_offset = ["--density-calc-z-offset", str(args.z_offset)]
    parts = [
        "python",
        "-m",
        "torch.distributed.launch",
        "--nproc_per_node",
        str(args.num_gpus),
        "--master_port",
        args.master_port,
        "fairseq-train",
        "--user-dir",
        "./graphormer",
        "--ddp-backend",
        "legacy_ddp",
        "--task",
        "graph_diffusion",
        "--data-path",
        f"{args.data_root}/",
        "--arch",
        "graphormer_diff_base",
        "--num-workers",
        "16",
        "--train-subset",
        "train-100",
        "--valid-subset",
        valid_subset,
        "--batch-size",
        str(args.batch_size),
        "--validate-interval",
        "1",
        "--max-update",
        "1",
        "--max-epoch",
        "1",
        "--optimizer",
        "adam",
        "--adam-betas",
        "(0.9, 0.98)",
        "--lr",
        "2e-4",
        "--lr-scheduler",
        "polynomial_decay",
        "--num-diffusion-timesteps",
        "5000",
        "--diffusion-beta-schedule",
        "sigmoid",
        "--diffusion-sampling",
        "ddpm",
        "--ddim-steps",
        "50",
        "--diffusion-beta-end",
        "2e-3",
        "--warmup-updates",
        "0",
        "--total-num-update",
        "1",
        "--keep-best-checkpoints",
        "5",
        "--keep-last-epochs",
        "5",
        "--save-dir",
        args.save_dir,
        "--best-checkpoint-metric",
        best_metric,
        "--criterion",
        criterion,
        "--kde-temperature",
        "1.0",
        "--pbc-cutoff",
        "6.0",
        "--pbc-approach",
        "cutoff",
        "--diffusion-noise-std",
        "1.0",
        "--fp16",
        "--batch-size-valid",
        str(args.batch_size),
        "--num-epsilon-estimator",
        "1",
        "--n-kde-samples",
        "1",
        "--result-save-dir",
        args.save_dir,
        "--seed",
        str(args.seed),
    ]
    parts.extend(density_offset)
    notes = [
        f"{mode} is a GPU-heavy DiG catalyst adsorption workflow.",
        "The command is rendered as a sketch only; real runs need the external LMDB data and checkpoint.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_property(args: argparse.Namespace, mode: str) -> Tuple[str, List[str]]:
    criterion = "diffusion_loss"
    valid_subset = f"sampling_natoms_{args.num_atoms}"
    sampling = "ode"
    beta_end = "2e-2"
    pbc_cutoff = "20.0"
    train_subset = "all_last_conf_10x"
    num_train_data = "156970"
    batch_valid = str(args.batch_size)
    device_id = "0"
    target_bandgap = args.target_bandgap
    conditioned_factor = "0.01"
    save_metric = "loss"
    if mode == "property-sample":
        criterion = "diffusion_loss"
        train_subset = "all_last_conf_10x"
        save_metric = "loss"
        if str(target_bandgap).startswith("-"):
            conditioned_factor = "0.0"
    parts = [
        "python",
        "-m",
        "torch.distributed.launch",
        "--nproc_per_node",
        str(args.num_gpus),
        "--master_port",
        args.master_port,
        "fairseq-train",
        "--user-dir",
        "./graphormer",
        "--ddp-backend",
        "legacy_ddp",
        "--task",
        "graph_diffusion",
        "--data-path",
        f"{args.data_root}/",
        "--arch",
        "graphormer_diff_base",
        "--num-workers",
        "16",
        "--train-subset",
        train_subset,
        "--valid-subset",
        valid_subset,
        "--batch-size",
        str(args.batch_size),
        "--validate-interval",
        "1",
        "--max-update",
        "1",
        "--max-epoch",
        "1",
        "--optimizer",
        "adam",
        "--adam-betas",
        "(0.9, 0.98)",
        "--lr",
        "2e-4",
        "--lr-scheduler",
        "polynomial_decay",
        "--num-diffusion-timesteps",
        "500",
        "--diffusion-beta-schedule",
        "sigmoid",
        "--diffusion-sampling",
        sampling,
        "--ddim-steps",
        "50",
        "--diffusion-beta-end",
        beta_end,
        "--warmup-updates",
        "0",
        "--total-num-update",
        "1",
        "--keep-best-checkpoints",
        "5",
        "--keep-last-epochs",
        "5",
        "--save-dir",
        args.save_dir,
        "--best-checkpoint-metric",
        save_metric,
        "--criterion",
        criterion,
        "--pbc-cutoff",
        pbc_cutoff,
        "--pbc-approach",
        "cutoff",
        "--diffusion-noise-std",
        "1.0",
        "--fp16",
        "--batch-size-valid",
        batch_valid,
        "--seed",
        str(args.seed + 1),
        "--lattice-size",
        "4.0",
        "--conditioned-ode-factor",
        conditioned_factor,
        "--device-id",
        device_id,
        "--target-bandgap-interval",
        str(target_bandgap),
        "--target-bandgap-softmax-temperature",
        "1.0",
        "--sampling-result-dir",
        args.save_dir,
        "--gpu-device-id-record",
        device_id,
        "--seed-record",
        str(args.seed + 1),
    ]
    notes = [
        f"{mode} is the property-guided DiG workflow.",
        "The command sketch assumes the external RSS carbon LMDB data is already unpacked.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_protein_reference(args: argparse.Namespace) -> Tuple[str, List[str]]:
    command = (
        "# reference-only sketch\n"
        f"python <protein-inference-entry-point> -c {shlex.quote(args.checkpoint)} "
        f"-i {shlex.quote(args.feature_path)} -s {shlex.quote(args.fasta_path)} "
        f"-o {shlex.quote(args.output_name)} -n {args.num_samples} "
        f"-p {shlex.quote(args.output_prefix)} --use-gpu --use-tqdm"
    )
    notes = [
        "The protein inference workflow is reference-only in this generated skill.",
        "The source material requires a checkpoint, feature pickle, and FASTA file.",
    ]
    return command, notes


def render_protein_ligand_reference(args: argparse.Namespace, mode: str) -> Tuple[str, List[str]]:
    if mode == "protein-ligand-single":
        command = (
            "# reference-only sketch\n"
            f"bash <protein-ligand-single-datapoint-entry-point> --pdbid {shlex.quote(args.pdbid)} "
            f"--number {args.number}"
        )
    else:
        command = "# reference-only sketch\nbash <protein-ligand-full-evaluation-entry-point>"
    notes = [
        f"{mode} is reference-only in the generated skill because the source workflow depends on external assets and long GPU time.",
        "Use the protein-ligand workflow reference to confirm the dataset, checkpoint, and Docker layout before a real run.",
    ]
    return command, notes


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.workflow == "catalyst-train":
        command, notes = render_catalyst(args, "catalyst-train")
    elif args.workflow == "catalyst-sample":
        command, notes = render_catalyst(args, "catalyst-sample")
    elif args.workflow == "catalyst-density":
        command, notes = render_catalyst(args, "catalyst-density")
    elif args.workflow == "property-train":
        command, notes = render_property(args, "property-train")
    elif args.workflow == "property-sample":
        command, notes = render_property(args, "property-sample")
    elif args.workflow == "protein-inference":
        command, notes = render_protein_reference(args)
    elif args.workflow in ("protein-ligand-single", "protein-ligand-full-eval"):
        command, notes = render_protein_ligand_reference(args, args.workflow)
    else:  # pragma: no cover - guarded by argparse choices
        raise SystemExit(f"Unsupported workflow: {args.workflow}")

    print("# Rendered command only; nothing was executed.")
    for note in notes:
        print(f"# {note}")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
