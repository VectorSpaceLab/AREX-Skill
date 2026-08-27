#!/usr/bin/env python3
"""Build safe Docker commands for pangenome-aware DeepVariant.

The helper validates command-line choices and prints a Docker command for
run_pangenome_aware_deepvariant. It never executes Docker and never opens
FASTA, BAM/CRAM, GBZ, VCF, or model files.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import shlex
import sys
from dataclasses import dataclass, field
from typing import Iterable

DEFAULT_IMAGE = "google/deepvariant:pangenome_aware_deepvariant-1.10.0"
WRAPPER_BIN = "/opt/deepvariant/bin/run_pangenome_aware_deepvariant"
ALLOWED_MODELS = {"WGS", "WES"}
REF_EXTENSIONS = (
    ".fa",
    ".fasta",
    ".fna",
    ".fa.gz",
    ".fasta.gz",
    ".fna.gz",
)
READ_EXTENSIONS = (".bam", ".cram")
PANGENOME_EXTENSIONS = (".gbz", ".bam", ".cram")
VCF_EXTENSIONS = (".vcf", ".vcf.gz")
GVCF_EXTENSIONS = (".g.vcf", ".g.vcf.gz", ".gvcf", ".gvcf.gz")


@dataclass
class BuildResult:
    command: list[str]
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _non_empty(value: str | None, name: str, errors: list[str]) -> None:
    if value is None or not str(value).strip():
        errors.append(f"{name} is required and must be non-empty")


def _has_extension(path: str, extensions: Iterable[str]) -> bool:
    lowered = path.lower()
    return any(lowered.endswith(extension) for extension in extensions)


def _is_container_path(path: str | None) -> bool:
    if not path:
        return False
    return path.startswith("/") or path.startswith("gs://")


def _validate_output_parent(path: str, name: str, warnings: list[str]) -> None:
    parent = posixpath.dirname(path)
    if not parent or parent == ".":
        warnings.append(
            f"{name} has no container directory component; prefer a mounted output directory"
        )


def _parse_mounts(mounts: list[str], warnings: list[str]) -> list[str]:
    docker_args: list[str] = []
    for mount in mounts:
        if ":" not in mount:
            warnings.append(
                f"mount {mount!r} is not HOST:CONTAINER format and was ignored"
            )
            continue
        host, container = mount.split(":", 1)
        if not host or not container:
            warnings.append(
                f"mount {mount!r} must include both host and container paths"
            )
            continue
        if not container.startswith("/"):
            warnings.append(
                f"mount {mount!r} has a non-absolute container path; Docker may not expose inputs"
            )
        docker_args.extend(["-v", mount])
    return docker_args


def _image_tag(image: str) -> str:
    image_name = image.rsplit("/", 1)[-1]
    if ":" not in image_name:
        return ""
    return image.rsplit(":", 1)[1]


def validate_args(args: argparse.Namespace) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    for value, name in [
        (args.model_type, "--model_type"),
        (args.ref, "--ref"),
        (args.reads, "--reads"),
        (args.pangenome, "--pangenome"),
        (args.output_vcf, "--output_vcf"),
    ]:
        _non_empty(value, name, errors)

    if args.model_type and args.model_type not in ALLOWED_MODELS:
        errors.append("--model_type must be WGS or WES for pangenome-aware r1.10")

    if args.ref and not _has_extension(args.ref, REF_EXTENSIONS):
        warnings.append(
            "--ref does not look like a FASTA path; ensure the matching .fai is mounted"
        )
    if args.reads and not _has_extension(args.reads, READ_EXTENSIONS):
        warnings.append("--reads should normally be an indexed BAM or CRAM")
    if args.pangenome and not _has_extension(args.pangenome, PANGENOME_EXTENSIONS):
        warnings.append("--pangenome should normally be a GBZ, BAM, or CRAM pangenome input")
    if args.pangenome and not args.pangenome.lower().endswith(".gbz"):
        warnings.append(
            "documented pangenome-aware workflows use GBZ; non-GBZ pangenome inputs need explicit user evidence"
        )
    if args.output_vcf and not _has_extension(args.output_vcf, VCF_EXTENSIONS):
        warnings.append("--output_vcf should usually end with .vcf or .vcf.gz")
    if args.output_gvcf and not _has_extension(args.output_gvcf, GVCF_EXTENSIONS):
        warnings.append("--output_gvcf should usually end with .g.vcf.gz or .gvcf.gz")

    for path, name in [
        (args.ref, "--ref"),
        (args.reads, "--reads"),
        (args.pangenome, "--pangenome"),
        (args.output_vcf, "--output_vcf"),
        (args.output_gvcf, "--output_gvcf"),
        (args.intermediate_results_dir, "--intermediate_results_dir"),
        (args.logging_dir, "--logging_dir"),
        (args.customized_model, "--customized_model"),
        (args.customized_small_model, "--customized_small_model"),
    ]:
        if path and not _is_container_path(path):
            warnings.append(f"{name} is not an absolute/container path; verify Docker mounts")

    if args.output_vcf:
        _validate_output_parent(args.output_vcf, "--output_vcf", warnings)
    if args.output_gvcf:
        _validate_output_parent(args.output_gvcf, "--output_gvcf", warnings)

    if args.num_shards < 1:
        errors.append("--num_shards must be >= 1")
    if args.gbz_shared_memory_size_gb < 1:
        errors.append("--gbz_shared_memory_size_gb must be >= 1")
    if args.postprocess_cpus is not None and args.postprocess_cpus < 0:
        errors.append("--postprocess_cpus must be >= 0 when set")

    tag = _image_tag(args.image)
    if not tag:
        warnings.append(
            "Docker image has no explicit tag; pin a pangenome-aware tag for reproducibility"
        )
    elif not tag.startswith("pangenome_aware_deepvariant"):
        warnings.append(
            "Docker image tag does not look pangenome-aware; expected pangenome_aware_deepvariant-*"
        )
    if args.sbx and tag != "pangenome_aware_deepvariant-sbx":
        warnings.append("--sbx was set but image tag is not pangenome_aware_deepvariant-sbx")
    if tag == "pangenome_aware_deepvariant-sbx" and not args.customized_model:
        warnings.append(
            "SBX image workflows normally require --customized_model and matching model metadata"
        )

    if not args.mount:
        warnings.append(
            "no --mount values supplied; generated Docker command may not expose inputs/outputs"
        )

    if args.pangenome and args.pangenome.lower().endswith(".gbz"):
        notes.append(
            "GBZ input triggers load_gbz_into_shared_memory before make_examples; keep Docker --shm-size >= --gbz_shared_memory_size_gb"
        )
    notes.append(
        f"pangenome reference name is {args.ref_name_pangenome!r}; confirm this is the name inside the GBZ"
    )
    notes.append(
        f"pangenome sample name is {args.sample_name_pangenome!r}; keep it distinct from the reads sample"
    )
    if args.sample_name_reads:
        notes.append(f"reads sample name is forced to {args.sample_name_reads!r}")
    else:
        notes.append("reads sample name will be inferred from the reads header by DeepVariant")

    if args.model_type == "WES" and args.postprocess_cpus is None:
        notes.append(
            "WES default: wrapper sets postprocess_variants --cpus 0 unless --postprocess_cpus is supplied"
        )
    if args.disable_small_model:
        notes.append("pangenome-aware wrapper default disables the small model")
    elif not args.customized_small_model:
        warnings.append(
            "small model was enabled but no --customized_small_model was provided; r1.10 has no default pangenome-aware small model config"
        )

    if args.runtime_report and not args.logging_dir:
        errors.append("--runtime_report requires --logging_dir")

    for extra_value, name in [
        (args.make_examples_extra_args, "--make_examples_extra_args"),
        (args.call_variants_extra_args, "--call_variants_extra_args"),
        (args.postprocess_variants_extra_args, "--postprocess_variants_extra_args"),
    ]:
        if extra_value:
            for piece in extra_value.split(","):
                if "=" not in piece:
                    errors.append(
                        f"{name} entries must be comma-separated flag=value pairs; bad entry {piece!r}"
                    )

    if args.call_variants_extra_args and "use_openvino" in args.call_variants_extra_args:
        warnings.append(
            "default DeepVariant Docker images do not include OpenVINO; avoid use_openvino unless using a custom image"
        )

    return errors, warnings, notes


def build_command(args: argparse.Namespace) -> BuildResult:
    errors, warnings, notes = validate_args(args)
    if errors:
        raise ValueError("; ".join(errors))

    command = ["sudo", "docker", "run"] if args.sudo else ["docker", "run"]
    command.extend(_parse_mounts(args.mount, warnings))
    command.extend(["--shm-size", args.shm_size])
    if args.user:
        command.extend(["--user", args.user])
    if args.remove:
        command.append("--rm")
    command.extend(args.docker_arg)
    command.extend([args.image, WRAPPER_BIN])

    wrapper_flags: list[tuple[str, str | bool | None]] = [
        ("--model_type", args.model_type),
        ("--ref", args.ref),
        ("--reads", args.reads),
        ("--pangenome", args.pangenome),
        ("--output_vcf", args.output_vcf),
        ("--output_gvcf", args.output_gvcf),
        ("--num_shards", str(args.num_shards)),
        ("--regions", args.regions),
        ("--intermediate_results_dir", args.intermediate_results_dir),
        ("--logging_dir", args.logging_dir),
        ("--runtime_report", True if args.runtime_report else None),
        ("--vcf_stats_report", True if args.vcf_stats_report else None),
        ("--report_title", args.report_title),
        ("--customized_model", args.customized_model),
        ("--customized_small_model", args.customized_small_model),
        ("--disable_small_model", args.disable_small_model),
        ("--sample_name_reads", args.sample_name_reads),
        ("--sample_name_pangenome", args.sample_name_pangenome),
        ("--ref_name_pangenome", args.ref_name_pangenome),
        ("--gbz_shared_memory_name", args.gbz_shared_memory_name),
        ("--gbz_shared_memory_size_gb", str(args.gbz_shared_memory_size_gb)),
        (
            "--postprocess_cpus",
            None if args.postprocess_cpus is None else str(args.postprocess_cpus),
        ),
        ("--make_examples_extra_args", args.make_examples_extra_args),
        ("--call_variants_extra_args", args.call_variants_extra_args),
        ("--postprocess_variants_extra_args", args.postprocess_variants_extra_args),
        ("--dry_run", True if args.deepvariant_dry_run else None),
    ]
    for flag, value in wrapper_flags:
        if value is None:
            continue
        if value is True:
            command.append(f"{flag}=true")
        elif value is False:
            command.append(f"{flag}=false")
        else:
            command.extend([flag, str(value)])

    return BuildResult(command=command, warnings=warnings, notes=notes)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely build a Docker run_pangenome_aware_deepvariant command."
    )
    parser.add_argument("--model_type", choices=sorted(ALLOWED_MODELS), required=True)
    parser.add_argument("--ref", required=True, help="Container-visible FASTA path.")
    parser.add_argument("--reads", required=True, help="Container-visible BAM/CRAM path.")
    parser.add_argument(
        "--pangenome", required=True, help="Container-visible GBZ/BAM/CRAM pangenome path."
    )
    parser.add_argument("--output_vcf", required=True, help="Container-visible output VCF path.")
    parser.add_argument("--output_gvcf")
    parser.add_argument("--regions", help="Region literal(s) or container-visible BED/BEDPE path.")
    parser.add_argument("--num_shards", type=int, default=1)
    parser.add_argument("--intermediate_results_dir")
    parser.add_argument("--logging_dir")
    parser.add_argument("--runtime_report", action="store_true")
    parser.add_argument("--vcf_stats_report", action="store_true")
    parser.add_argument("--report_title")
    parser.add_argument("--customized_model")
    parser.add_argument("--customized_small_model")
    parser.add_argument(
        "--disable_small_model",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Defaults to true, matching pangenome-aware r1.10 wrapper behavior.",
    )
    parser.add_argument("--sample_name_reads")
    parser.add_argument("--sample_name_pangenome", default="hprc_v1.1")
    parser.add_argument("--ref_name_pangenome", default="GRCh38")
    parser.add_argument("--gbz_shared_memory_name")
    parser.add_argument("--gbz_shared_memory_size_gb", type=int, default=12)
    parser.add_argument("--postprocess_cpus", type=int)
    parser.add_argument("--make_examples_extra_args")
    parser.add_argument("--call_variants_extra_args")
    parser.add_argument("--postprocess_variants_extra_args")
    parser.add_argument(
        "--deepvariant_dry_run",
        action="store_true",
        help="Append --dry_run=true for the DeepVariant wrapper; this helper still never executes Docker.",
    )
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument(
        "--mount", action="append", default=[], help="Docker mount in HOST:CONTAINER form. Repeatable."
    )
    parser.add_argument("--shm_size", default="12gb", help="Docker --shm-size value.")
    parser.add_argument("--docker_arg", action="append", default=[], help="Extra raw Docker argument. Repeatable.")
    parser.add_argument("--user", help="Optional Docker --user value.")
    parser.add_argument("--sudo", action="store_true", help="Prefix command with sudo.")
    parser.add_argument(
        "--no-remove", dest="remove", action="store_false", default=True, help="Do not add Docker --rm."
    )
    parser.add_argument(
        "--sbx", action="store_true", help="Mark command as Roche/SBX-specialized for validation warnings."
    )
    parser.add_argument("--format", choices=("shell", "json"), default="shell")
    return parser


def emit_shell(result: BuildResult) -> None:
    if result.warnings:
        print("# Warnings", file=sys.stderr)
        for warning in result.warnings:
            print(f"# - {warning}", file=sys.stderr)
    if result.notes:
        print("# Notes", file=sys.stderr)
        for note in result.notes:
            print(f"# - {note}", file=sys.stderr)
    print(shlex.join(result.command))


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        result = build_command(args)
    except ValueError as error:
        parser.error(str(error))

    if args.format == "json":
        print(
            json.dumps(
                {
                    "command": result.command,
                    "shell": shlex.join(result.command),
                    "warnings": result.warnings,
                    "notes": result.notes,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        emit_shell(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
