#!/usr/bin/env python3
"""Build a safe no-run `protenix pred` command.

This helper prints the command that would be run. It never imports Protenix,
loads models, downloads checkpoints, or starts inference.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


TRUE_FALSE = {"true", "false"}
MODEL_WARNINGS = {
    "protenix_base_default_v0.5.0": [
        "v0.5.0 base default models do not support RNA MSA or templates in the current public docs.",
    ],
    "protenix_base_constraint_v0.5.0": [
        "constraint v0.5.0 is for distance-constraint workflows; confirm the input JSON has a constraint section.",
    ],
    "protenix_mini_default_v0.5.0": [
        "mini/tiny models use smaller default cycle/step settings; prefer --use-default-params true unless overriding intentionally.",
    ],
    "protenix_tiny_default_v0.5.0": [
        "mini/tiny models use smaller default cycle/step settings; prefer --use-default-params true unless overriding intentionally.",
    ],
}


def bool_text(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def add_bool(command: list[str], flag: str, value: bool | None) -> None:
    text = bool_text(value)
    if text is not None:
        command.extend([flag, text])


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    command = ["protenix", "pred", "--input", args.input, "--out_dir", args.out_dir]
    warnings: list[str] = []

    if args.model_name:
        command.extend(["--model_name", args.model_name])
        warnings.extend(MODEL_WARNINGS.get(args.model_name, []))
    if args.seeds:
        command.extend(["--seeds", args.seeds])
    if args.dtype:
        command.extend(["--dtype", args.dtype])
    if args.cycle is not None:
        command.extend(["--cycle", str(args.cycle)])
    if args.step is not None:
        command.extend(["--step", str(args.step)])
    if args.sample is not None:
        command.extend(["--sample", str(args.sample)])
    if args.trimul_kernel:
        command.extend(["--trimul_kernel", args.trimul_kernel])
    if args.triatt_kernel:
        command.extend(["--triatt_kernel", args.triatt_kernel])
    if args.msa_server_mode:
        command.extend(["--msa_server_mode", args.msa_server_mode])

    add_bool(command, "--use_msa", args.use_msa)
    add_bool(command, "--use_template", args.use_template)
    add_bool(command, "--use_rna_msa", args.use_rna_msa)
    add_bool(command, "--use_default_params", args.use_default_params)
    add_bool(command, "--enable_cache", args.enable_cache)
    add_bool(command, "--enable_fusion", args.enable_fusion)
    add_bool(command, "--enable_tf32", args.enable_tf32)
    add_bool(command, "--use_tfg_guidance", args.use_tfg_guidance)
    add_bool(command, "--use_seeds_in_json", args.use_seeds_in_json)
    add_bool(command, "--need_atom_confidence", args.need_atom_confidence)

    for flag, value in [
        ("--kalign_binary_path", args.kalign_binary_path),
        ("--hmmsearch_binary_path", args.hmmsearch_binary_path),
        ("--hmmbuild_binary_path", args.hmmbuild_binary_path),
        ("--seqres_database_path", args.seqres_database_path),
        ("--nhmmer_binary_path", args.nhmmer_binary_path),
        ("--hmmalign_binary_path", args.hmmalign_binary_path),
        ("--hmmbuild_rna_binary_path", args.hmmbuild_rna_binary_path),
        ("--ntrna_database_path", args.ntrna_database_path),
        ("--rfam_database_path", args.rfam_database_path),
        ("--rna_central_database_path", args.rna_central_database_path),
    ]:
        if value:
            command.extend([flag, value])

    if args.use_template and not (args.hmmsearch_binary_path or args.seqres_database_path):
        warnings.append("Template inference needs valid templatesPath fields in JSON or template-search prerequisites already prepared.")
    if args.use_rna_msa and not any([args.nhmmer_binary_path, args.ntrna_database_path, args.rfam_database_path, args.rna_central_database_path]):
        warnings.append("RNA MSA inference needs unpairedMsaPath fields in JSON or RNA MSA databases/tools prepared before running.")
    if args.triatt_kernel == "torch" or args.trimul_kernel == "torch":
        warnings.append("Torch kernels are safer fallbacks for compatibility but may be slower than accelerated kernels.")
    if args.use_default_params is False and (args.cycle is None or args.step is None):
        warnings.append("When --use_default_params false, set --cycle and --step intentionally for reproducible sampling cost.")
    if args.use_seeds_in_json and args.seeds:
        warnings.append("--use_seeds_in_json true gives JSON seeds priority over --seeds.")
    warnings.append("This helper only prints a command; review GPU, checkpoint/cache, input JSON, and output paths before running it.")
    return command, warnings


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Print a no-run Protenix prediction command.")
    p.add_argument("--input", required=True, help="Input JSON file or directory.")
    p.add_argument("--out-dir", required=True, help="Output directory for prediction results.")
    p.add_argument("--model-name", default="protenix_base_default_v1.0.0")
    p.add_argument("--seeds", default="101")
    p.add_argument("--dtype", choices=["bf16", "fp32"], default="bf16")
    p.add_argument("--cycle", type=int)
    p.add_argument("--step", type=int)
    p.add_argument("--sample", type=int)
    p.add_argument("--trimul-kernel", choices=["cuequivariance", "torch"], default="cuequivariance")
    p.add_argument("--triatt-kernel", choices=["triattention", "cuequivariance", "deepspeed", "torch"], default="cuequivariance")
    p.add_argument("--msa-server-mode", choices=["protenix", "colabfold"], default="protenix")
    p.add_argument("--use-msa", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--use-template", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--use-rna-msa", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--use-default-params", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--enable-cache", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--enable-fusion", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--enable-tf32", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--use-tfg-guidance", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--use-seeds-in-json", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--need-atom-confidence", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--kalign-binary-path")
    p.add_argument("--hmmsearch-binary-path")
    p.add_argument("--hmmbuild-binary-path")
    p.add_argument("--seqres-database-path")
    p.add_argument("--nhmmer-binary-path")
    p.add_argument("--hmmalign-binary-path")
    p.add_argument("--hmmbuild-rna-binary-path")
    p.add_argument("--ntrna-database-path")
    p.add_argument("--rfam-database-path")
    p.add_argument("--rna-central-database-path")
    p.add_argument("--print-warnings", action="store_true", help="Print warnings after the command.")
    return p


def main() -> int:
    args = parser().parse_args()
    command, warnings = build_command(args)
    print(shell_join(command))
    if args.print_warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
