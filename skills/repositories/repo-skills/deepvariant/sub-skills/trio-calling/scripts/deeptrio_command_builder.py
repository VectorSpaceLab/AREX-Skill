#!/usr/bin/env python3
"""Build safe DeepTrio and GLnexus planning commands without executing them."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Iterable

DEEPTRIO_VERSION = "1.10.0"
GLNEXUS_VERSION = "v1.2.7"
MODEL_TYPES = ("WGS", "WES", "PACBIO", "ONT")
DEFAULT_GLNEXUS_CONFIG = {
    "WGS": "DeepVariantWGS",
    "WES": "DeepVariantWES",
    "PACBIO": "DeepVariant_unfiltered",
    "ONT": "DeepVariant_unfiltered",
}


def multiline_command(parts: Iterable[str]) -> str:
    return " \\\n  ".join(shlex.quote(str(part)) for part in parts)


def add_flag(parts: list[str], name: str, value: str | int | None) -> None:
    if value not in (None, ""):
        parts.extend([f"--{name}", str(value)])


def add_bool_flag(parts: list[str], name: str, enabled: bool) -> None:
    if enabled:
        parts.append(f"--{name}=true")


def present(values: Iterable[str | None]) -> bool:
    return any(value not in (None, "") for value in values)


def complete(values: Iterable[str | None]) -> bool:
    return all(value not in (None, "") for value in values)


def validate_mounts(mounts: list[str], errors: list[str], warnings: list[str]) -> None:
    if not mounts:
        warnings.append(
            "No Docker mounts were provided; generated container paths must be made visible before execution."
        )
        return
    for mount in mounts:
        if ":" not in mount:
            errors.append(f"Mount {mount!r} must use HOST_DIR:CONTAINER_DIR form.")
            continue
        host_path, container_path = mount.split(":", 1)
        if not host_path or not container_path:
            errors.append(f"Mount {mount!r} must include non-empty host and container paths.")
        if container_path and not container_path.startswith("/"):
            errors.append(f"Mount {mount!r} must use an absolute container path.")


def validate_num_shards(num_shards: int, errors: list[str]) -> None:
    if num_shards < 1:
        errors.append("--num-shards must be a positive integer.")


def validate_args(args: argparse.Namespace) -> tuple[list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []

    validate_num_shards(args.num_shards, errors)
    validate_mounts(args.mount, errors, warnings)

    required = {
        "--ref": args.ref,
        "--reads-child": args.reads_child,
        "--sample-name-child": args.sample_name_child,
        "--output-vcf-child": args.output_vcf_child,
    }
    for flag, value in required.items():
        if value in (None, ""):
            errors.append(f"{flag} is required for DeepTrio command planning.")

    parent1_group = [args.reads_parent1, args.sample_name_parent1, args.output_vcf_parent1]
    if not complete(parent1_group):
        errors.append(
            "DeepTrio family planning requires --reads-parent1, --sample-name-parent1, and --output-vcf-parent1 together."
        )

    parent2_group = [args.reads_parent2, args.sample_name_parent2, args.output_vcf_parent2]
    parent2_is_present = present(parent2_group)
    parent2_is_complete = complete(parent2_group)

    if parent2_is_present and not parent2_is_complete:
        errors.append(
            "Parent2 must be all-or-none: set --reads-parent2, --sample-name-parent2, and --output-vcf-parent2 together, or omit all three for duo mode."
        )
    if args.mode == "duo" and (parent2_is_present or args.output_gvcf_parent2):
        errors.append("--mode duo cannot include any parent2 input, sample, VCF, or gVCF flag.")
    if args.mode == "trio" and not parent2_is_complete:
        errors.append("--mode trio requires a complete parent2 input/sample/output group.")

    family_mode = "trio" if parent2_is_complete else "duo"
    if args.mode in {"duo", "trio"}:
        family_mode = args.mode

    if args.output_gvcf_parent2 and not parent2_is_complete:
        errors.append("--output-gvcf-parent2 is only valid when parent2 is present.")

    gvcf_values = [args.output_gvcf_child, args.output_gvcf_parent1]
    gvcf_names = ["--output-gvcf-child", "--output-gvcf-parent1"]
    if parent2_is_complete:
        gvcf_values.append(args.output_gvcf_parent2)
        gvcf_names.append("--output-gvcf-parent2")
    if present(gvcf_values) and not complete(gvcf_values):
        missing = [name for name, value in zip(gvcf_names, gvcf_values) if not value]
        errors.append(
            "When requesting gVCFs for a family merge, provide gVCF outputs for every supplied sample; missing "
            + ", ".join(missing)
            + "."
        )
    if args.emit_glnexus and not complete(gvcf_values):
        errors.append("--emit-glnexus requires a complete gVCF set for every supplied sample.")
    if args.emit_glnexus and not args.merged_vcf_host:
        errors.append("--emit-glnexus requires --merged-vcf-host because shell redirection happens on the host.")

    if args.model_type == "WES" and not args.regions:
        warnings.append("WES workflows usually pass capture targets or intervals with --regions.")
    if args.model_type in {"PACBIO", "ONT"}:
        warnings.append(
            f"{args.model_type} uses candidate partitioning automatically in the r1.10 wrapper; expect candidate_sweep intermediates."
        )
    if args.gpu:
        warnings.append("GPU mode only accelerates call_variants and still requires correct Docker GPU passthrough.")

    default_config = DEFAULT_GLNEXUS_CONFIG[args.model_type]
    if args.glnexus_config is None:
        args.glnexus_config = default_config
    elif args.glnexus_config != default_config:
        warnings.append(
            f"Selected GLnexus config {args.glnexus_config!r} differs from default guidance {default_config!r} for {args.model_type}."
        )

    if args.glnexus_bed and args.model_type != "WES":
        warnings.append("A GLnexus BED is most commonly paired with WES; verify this is intentional.")

    return errors, warnings, family_mode


def build_deeptrio_command(args: argparse.Namespace) -> list[str]:
    image_suffix = "-gpu" if args.gpu else ""
    image = f"google/deepvariant:deeptrio-{args.bin_version}{image_suffix}"
    parts: list[str] = []
    if args.sudo:
        parts.append("sudo")
    parts.extend([args.docker_binary, "run"])
    if args.gpu:
        parts.extend(["--gpus", args.gpus])
    for mount in args.mount:
        parts.extend(["-v", mount])
    parts.extend([image, "/opt/deepvariant/bin/deeptrio/run_deeptrio"])

    add_flag(parts, "model_type", args.model_type)
    add_flag(parts, "ref", args.ref)
    add_flag(parts, "reads_child", args.reads_child)
    add_flag(parts, "reads_parent1", args.reads_parent1)
    add_flag(parts, "reads_parent2", args.reads_parent2)
    add_flag(parts, "output_vcf_child", args.output_vcf_child)
    add_flag(parts, "output_vcf_parent1", args.output_vcf_parent1)
    add_flag(parts, "output_vcf_parent2", args.output_vcf_parent2)
    add_flag(parts, "sample_name_child", args.sample_name_child)
    add_flag(parts, "sample_name_parent1", args.sample_name_parent1)
    add_flag(parts, "sample_name_parent2", args.sample_name_parent2)
    add_flag(parts, "num_shards", args.num_shards)
    add_flag(parts, "regions", args.regions)
    add_flag(parts, "intermediate_results_dir", args.intermediate_results_dir)
    add_flag(parts, "output_gvcf_child", args.output_gvcf_child)
    add_flag(parts, "output_gvcf_parent1", args.output_gvcf_parent1)
    add_flag(parts, "output_gvcf_parent2", args.output_gvcf_parent2)
    add_flag(parts, "logging_dir", args.logging_dir)
    add_bool_flag(parts, "runtime_report", args.runtime_report)
    add_bool_flag(parts, "vcf_stats_report", args.vcf_stats_report)
    add_bool_flag(parts, "dry_run", args.deeptrio_dry_run)
    return parts


def build_glnexus_command(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.sudo:
        parts.append("sudo")
    parts.extend([args.docker_binary, "run"])
    for mount in args.mount:
        parts.extend(["-v", mount])
    parts.extend([
        f"quay.io/mlin/glnexus:{args.glnexus_version}",
        "/usr/local/bin/glnexus_cli",
        "--config",
        args.glnexus_config,
    ])
    if args.glnexus_bed:
        parts.extend(["--bed", args.glnexus_bed])
    parts.extend([args.output_gvcf_child, args.output_gvcf_parent1])
    if args.output_gvcf_parent2:
        parts.append(args.output_gvcf_parent2)

    deeptrio_image = f"google/deepvariant:deeptrio-{args.bin_version}"
    bcftools: list[str] = []
    bgzip: list[str] = []
    if args.sudo:
        bcftools.append("sudo")
        bgzip.append("sudo")
    bcftools.extend([args.docker_binary, "run", "-i", deeptrio_image, "bcftools", "view", "-"])
    bgzip.extend([args.docker_binary, "run", "-i", deeptrio_image, "bgzip", "-c"])
    return (
        multiline_command(parts)
        + " \\\n  | "
        + multiline_command(bcftools)
        + " \\\n  | "
        + multiline_command(bgzip)
        + " > "
        + shlex.quote(args.merged_vcf_host)
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DeepTrio child/parent flag groups and print Docker/GLnexus commands. "
            "This helper never executes Docker, DeepTrio, or GLnexus."
        )
    )
    parser.add_argument("--mode", choices=("auto", "duo", "trio"), default="auto")
    parser.add_argument("--model-type", choices=MODEL_TYPES, required=True)
    parser.add_argument("--bin-version", default=DEEPTRIO_VERSION)
    parser.add_argument("--docker-binary", default="docker")
    parser.add_argument("--sudo", action="store_true", help="Prefix generated Docker commands with sudo.")
    parser.add_argument("--gpu", action="store_true", help="Use the DeepTrio GPU image and add Docker --gpus.")
    parser.add_argument("--gpus", default="1")
    parser.add_argument("--mount", action="append", default=[], help="Docker -v mount in HOST_DIR:CONTAINER_DIR form; repeat as needed.")
    parser.add_argument("--ref", required=True)
    parser.add_argument("--reads-child", required=True)
    parser.add_argument("--reads-parent1", required=True)
    parser.add_argument("--reads-parent2")
    parser.add_argument("--sample-name-child", required=True)
    parser.add_argument("--sample-name-parent1", required=True)
    parser.add_argument("--sample-name-parent2")
    parser.add_argument("--output-vcf-child", required=True)
    parser.add_argument("--output-vcf-parent1", required=True)
    parser.add_argument("--output-vcf-parent2")
    parser.add_argument("--output-gvcf-child")
    parser.add_argument("--output-gvcf-parent1")
    parser.add_argument("--output-gvcf-parent2")
    parser.add_argument("--regions")
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--intermediate-results-dir")
    parser.add_argument("--logging-dir")
    parser.add_argument("--runtime-report", action="store_true")
    parser.add_argument("--vcf-stats-report", action="store_true")
    parser.add_argument("--deeptrio-dry-run", action="store_true", help="Add --dry_run=true to the generated DeepTrio command.")
    parser.add_argument("--emit-glnexus", action="store_true", help="Also print a GLnexus gVCF merge handoff command.")
    parser.add_argument("--glnexus-version", default=GLNEXUS_VERSION)
    parser.add_argument("--glnexus-config", help="Defaults by model type: DeepVariantWES, DeepVariantWGS, or DeepVariant_unfiltered.")
    parser.add_argument("--glnexus-bed", help="Container-visible BED path for WES GLnexus merge.")
    parser.add_argument("--merged-vcf-host", help="Host-side path used after shell redirection for the merged VCF.")
    parser.add_argument("--format", choices=("shell", "json"), default="shell")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings, family_mode = validate_args(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    deeptrio_parts = build_deeptrio_command(args)
    deeptrio_command = multiline_command(deeptrio_parts)
    glnexus_command = build_glnexus_command(args) if args.emit_glnexus else None

    if args.format == "json":
        payload = {
            "executes_commands": False,
            "family_mode": family_mode,
            "model_type": args.model_type,
            "warnings": warnings,
            "deeptrio_command": deeptrio_command,
            "glnexus_command": glnexus_command,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("# This helper only prints commands; it does not execute Docker, DeepTrio, or GLnexus.")
        print(f"# family_mode={family_mode} model_type={args.model_type}")
        for warning in warnings:
            print(f"# WARNING: {warning}")
        print(deeptrio_command)
        if glnexus_command:
            print("\n# GLnexus handoff command; verify gVCF indexes, config, and host-side redirect path before running.")
            print(glnexus_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
