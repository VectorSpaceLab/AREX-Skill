#!/usr/bin/env python3
"""Safely build DeepVariant germline run_deepvariant container commands.

This helper adapts command-planning concepts from DeepVariant's r1.10
run_deepvariant wrapper: it validates obvious local path/index issues and prints
Docker or Singularity command lines. It never executes DeepVariant, Docker,
Singularity, samtools, or TensorFlow, and it does not read large genomics files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shlex
import sys
from typing import Iterable

MODEL_TYPES = {
    "WGS",
    "WES",
    "PACBIO",
    "ONT_R104",
    "HYBRID_PACBIO_ILLUMINA",
    "MASSEQ",
    "RNASEQ",
}
LONG_READ_MODEL_TYPES = {"PACBIO", "ONT_R104"}
REMOTE_PREFIXES = ("gs://", "http://", "https://", "s3://")
BED_SUFFIXES = (".bed", ".bed.gz", ".bedpe", ".bedpe.gz")
REGION_LITERAL_RE = re.compile(r"^[A-Za-z0-9_.-]+(?::[0-9,]+(?:-[0-9,]+)?)?$")


def as_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser()


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def is_remote(value: str | None) -> bool:
    return bool(value and value.startswith(REMOTE_PREFIXES))


def is_probably_host_path(value: str | None) -> bool:
    if not value or is_remote(value):
        return False
    return Path(value).expanduser().is_absolute() or not value.startswith("/")


def companion_exists(path: Path, suffixes: Iterable[str]) -> bool:
    return any(path_exists(Path(str(path) + suffix)) for suffix in suffixes)


def fai_candidates(ref: Path) -> list[Path]:
    candidates = [Path(str(ref) + ".fai")]
    if ref.suffix == ".gz":
        candidates.append(Path(str(ref.with_suffix("")) + ".fai"))
    return candidates


def read_fai_contigs(ref: Path | None) -> set[str]:
    if ref is None:
        return set()
    for candidate in fai_candidates(ref):
        if candidate.is_file():
            contigs: set[str] = set()
            try:
                with candidate.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        if line.strip():
                            contigs.add(line.split("\t", 1)[0])
                return contigs
            except OSError:
                return set()
    return set()


def split_regions(regions: str | None) -> list[str]:
    if not regions:
        return []
    return [token for token in regions.split() if token]


def region_contig(region: str) -> str | None:
    if region.endswith(BED_SUFFIXES):
        return None
    if ":" in region:
        return region.split(":", 1)[0]
    if REGION_LITERAL_RE.match(region):
        return region
    return None


def quote(value: object) -> str:
    return shlex.quote(str(value))


def add_flag(parts: list[str], name: str, value: object | None = None) -> None:
    if value is None:
        parts.append(f"--{name}")
    else:
        parts.append(f"--{name}={value}")


def parse_extra_args(value: str | None, label: str, errors: list[str]) -> None:
    if not value:
        return
    chunks = re.findall(r"[^,]+=[\"'][^\"']*[\"']|[^,]+", value)
    for chunk in chunks:
        if "=" not in chunk:
            errors.append(f"{label} entry {chunk!r} is missing '='")
            continue
        key, raw_value = chunk.split("=", 1)
        key = key.strip().lstrip("-")
        raw_value = raw_value.strip()
        if not key:
            errors.append(f"{label} contains an empty flag name")
        if raw_value == "":
            errors.append(f"{label} entry {chunk!r} has an empty value")


def looks_like_directory(path: Path) -> bool:
    if path.exists():
        return path.is_dir()
    return path.suffix == ""


def validate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if args.model_type not in MODEL_TYPES:
        errors.append(f"unsupported --model-type {args.model_type!r}")

    if args.num_shards < 1:
        errors.append("--num-shards must be >= 1")

    ref = as_path(args.ref)
    reads = as_path(args.reads)
    output_vcf = as_path(args.output_vcf)
    output_gvcf = as_path(args.output_gvcf)
    logging_dir = as_path(args.logging_dir)
    intermediate_dir = as_path(args.intermediate_results_dir)
    par_regions_bed = as_path(args.par_regions_bed)
    customized_model = as_path(args.customized_model)
    customized_model_json = as_path(args.customized_model_json)

    for label, path in (("--ref", ref), ("--reads", reads)):
        if path and is_probably_host_path(str(path)) and not path_exists(path):
            errors.append(f"{label} path does not exist: {path}")

    if ref and path_exists(ref) and not any(path_exists(candidate) for candidate in fai_candidates(ref)):
        errors.append(f"--ref is missing a colocated FASTA index (.fai): {ref}")

    if reads and path_exists(reads):
        reads_name = reads.name.lower()
        if reads_name.endswith(".bam") and not (
            companion_exists(reads, (".bai",)) or path_exists(reads.with_suffix(".bai"))
        ):
            errors.append(f"BAM --reads is missing .bai index: {reads}")
        if reads_name.endswith(".cram") and not (
            companion_exists(reads, (".crai",)) or path_exists(reads.with_suffix(".crai"))
        ):
            errors.append(f"CRAM --reads is missing .crai index: {reads}")
        if reads_name.endswith(".cram"):
            warnings.append("For CRAM, ensure --ref is the decoding reference mounted inside the container; inspect lower-level use_ref_for_cram changes with --dry_run=true.")
        if not reads_name.endswith((".bam", ".cram")):
            warnings.append("--reads does not end in .bam or .cram; confirm DeepVariant can read this aligned, sorted, indexed file.")

    for label, path in (("--output-vcf", output_vcf), ("--output-gvcf", output_gvcf)):
        if path:
            parent = path.parent
            if is_probably_host_path(str(path)) and not parent.exists():
                errors.append(f"{label} parent directory does not exist: {parent}")
            if not str(path).endswith((".vcf.gz", ".g.vcf.gz")):
                warnings.append(f"{label} usually should end with .vcf.gz or .g.vcf.gz so postprocess can create a tabix index.")

    for label, path in (("--logging-dir", logging_dir), ("--intermediate-results-dir", intermediate_dir)):
        if path and is_probably_host_path(str(path)) and not path.exists():
            warnings.append(f"{label} does not exist yet; create and mount it before running: {path}")

    if args.runtime_report and not args.logging_dir:
        errors.append("--runtime-report requires --logging-dir")

    if args.gpu and not args.image_version.endswith("-gpu"):
        runtime_flag = "Docker --gpus 1" if args.engine == "docker" else "Singularity --nv"
        warnings.append(f"--gpu adds {runtime_flag} and uses an image tag with -gpu appended for command output.")

    if args.haploid_contigs and not args.par_regions_bed:
        warnings.append("--haploid-contigs without --par-regions-bed treats all listed contigs as haploid, including PAR unless excluded elsewhere.")
    if args.par_regions_bed and not args.haploid_contigs:
        warnings.append("--par-regions-bed has no effect unless --haploid-contigs is also set.")
    if par_regions_bed and is_probably_host_path(str(par_regions_bed)) and not path_exists(par_regions_bed):
        errors.append(f"--par-regions-bed path does not exist: {par_regions_bed}")

    if args.phase_vcf is True and args.model_type not in LONG_READ_MODEL_TYPES:
        errors.append("--phase-vcf=true is supported only for PACBIO and ONT_R104 models")

    if customized_model:
        if path_exists(customized_model) and customized_model.is_dir():
            saved_model = customized_model / "saved_model.pb"
            metadata = customized_model / "model.example_info.json"
            if not path_exists(saved_model):
                warnings.append("customized model directory exists but has no saved_model.pb; it must be a SavedModel directory or checkpoint prefix.")
        else:
            data_file = Path(str(customized_model) + ".data-00000-of-00001")
            index_file = Path(str(customized_model) + ".index")
            if is_probably_host_path(str(customized_model)) and not (path_exists(data_file) and path_exists(index_file)):
                errors.append("--customized-model checkpoint prefix is missing .data-00000-of-00001 or .index files")
            metadata = customized_model.parent / "model.example_info.json"
        if not args.customized_model_json and not path_exists(metadata):
            errors.append("--customized-model requires model.example_info.json in the model directory or --customized-model-json")
    if customized_model_json and is_probably_host_path(str(customized_model_json)) and not path_exists(customized_model_json):
        errors.append(f"--customized-model-json path does not exist: {customized_model_json}")

    for value, label in (
        (args.make_examples_extra_args, "--make-examples-extra-args"),
        (args.call_variants_extra_args, "--call-variants-extra-args"),
        (args.postprocess_variants_extra_args, "--postprocess-variants-extra-args"),
    ):
        parse_extra_args(value, label, errors)

    ref_contigs = read_fai_contigs(ref)
    for token in split_regions(args.regions):
        candidate = as_path(token)
        if token.endswith(BED_SUFFIXES):
            if candidate and is_probably_host_path(token) and not path_exists(candidate):
                errors.append(f"--regions BED/BEDPE path does not exist: {candidate}")
            continue
        contig = region_contig(token)
        if ref_contigs and contig and contig not in ref_contigs:
            errors.append(f"--regions contig {contig!r} is not present in the FASTA .fai")
        elif not contig:
            warnings.append(f"could not statically classify --regions token {token!r}; verify it is a valid region or mounted BED/BEDPE path")

    if args.model_type == "RNASEQ" and not args.disable_small_model:
        warnings.append("RNASEQ documented workflows commonly use --disable_small_model; confirm before running with small model enabled.")
    if args.model_type == "WES" and not args.regions:
        warnings.append("WES workflows usually provide a capture BED or target regions with --regions.")
    if args.model_type == "HYBRID_PACBIO_ILLUMINA":
        warnings.append("HYBRID_PACBIO_ILLUMINA expects evidence prepared for the hybrid model; confirm separate read sets were merged/sorted/indexed appropriately.")
    if args.customized_small_model and not args.make_examples_extra_args:
        warnings.append("Custom small-model use should normally set explicit small_model_*_gq_threshold values through --make-examples-extra-args.")

    warnings.append("Static validation cannot prove BAM/CRAM header contigs match the FASTA; compare headers before full execution.")
    warnings.append("This helper prints a command only; Docker/Singularity execution remains user-controlled and may be long-running.")
    return errors, warnings


def collect_mount_candidates(args: argparse.Namespace) -> list[str | None]:
    region_paths = [token for token in split_regions(args.regions) if token.endswith(BED_SUFFIXES)]
    return [
        args.ref,
        args.reads,
        args.output_vcf,
        args.output_gvcf,
        *region_paths,
        args.par_regions_bed,
        args.logging_dir,
        args.intermediate_results_dir,
        args.customized_model,
        args.customized_model_json,
        args.customized_small_model,
    ]


def mount_roots(args: argparse.Namespace) -> dict[Path, str]:
    roots: list[Path] = []
    for value in collect_mount_candidates(args):
        if not value or not is_probably_host_path(value):
            continue
        path = Path(value).expanduser().resolve(strict=False)
        root = path if looks_like_directory(path) else path.parent
        if root not in roots:
            roots.append(root)
    selected: list[Path] = []
    for root in sorted(roots, key=lambda item: (len(str(item)), str(item))):
        if not any(root == parent or parent in root.parents for parent in selected):
            selected.append(root)
    return {root: f"/dv_input_{index}" if index else "/dv_input" for index, root in enumerate(selected)}


def containerize_path(value: str | None, mounts: dict[Path, str]) -> str | None:
    if not value or not is_probably_host_path(value):
        return value
    path = Path(value).expanduser().resolve(strict=False)
    best: tuple[Path, str] | None = None
    for root, mount in mounts.items():
        if path == root or root in path.parents:
            if best is None or len(str(root)) > len(str(best[0])):
                best = (root, mount)
    if best is None:
        return value
    root, mount = best
    rel = path.relative_to(root)
    if str(rel) == ".":
        return mount
    return str(Path(mount) / rel)


def containerize_regions(regions: str | None, mounts: dict[Path, str]) -> str | None:
    if not regions:
        return None
    converted: list[str] = []
    for token in split_regions(regions):
        if token.endswith(BED_SUFFIXES):
            converted.append(containerize_path(token, mounts) or token)
        else:
            converted.append(token)
    return " ".join(converted)


def image_tag(args: argparse.Namespace) -> str:
    version = args.image_version
    if args.gpu and not version.endswith("-gpu"):
        version = f"{version}-gpu"
    return f"google/deepvariant:{version}"


def build_run_deepvariant_flags(args: argparse.Namespace, mounts: dict[Path, str]) -> list[str]:
    parts: list[str] = []
    add_flag(parts, "model_type", args.model_type)
    add_flag(parts, "ref", containerize_path(args.ref, mounts))
    add_flag(parts, "reads", containerize_path(args.reads, mounts))
    add_flag(parts, "output_vcf", containerize_path(args.output_vcf, mounts))

    optional_values = [
        ("output_gvcf", args.output_gvcf, True),
        ("regions", containerize_regions(args.regions, mounts), False),
        ("intermediate_results_dir", args.intermediate_results_dir, True),
        ("logging_dir", args.logging_dir, True),
        ("customized_model", args.customized_model, True),
        ("customized_model_json", args.customized_model_json, True),
        ("customized_small_model", args.customized_small_model, True),
        ("haploid_contigs", args.haploid_contigs, False),
        ("par_regions_bed", args.par_regions_bed, True),
        ("sample_name", args.sample_name, False),
        ("report_title", args.report_title, False),
        ("make_examples_extra_args", args.make_examples_extra_args, False),
        ("call_variants_extra_args", args.call_variants_extra_args, False),
        ("postprocess_variants_extra_args", args.postprocess_variants_extra_args, False),
    ]
    for name, value, is_path in optional_values:
        if value:
            add_flag(parts, name, containerize_path(value, mounts) if is_path else value)

    add_flag(parts, "num_shards", args.num_shards)
    if args.vcf_stats_report:
        add_flag(parts, "vcf_stats_report", "true")
    if args.disable_small_model:
        add_flag(parts, "disable_small_model", "true")
    if args.runtime_report:
        add_flag(parts, "runtime_report", "true")
    if args.dry_run:
        add_flag(parts, "dry_run", "true")
    if args.phase_vcf is not None:
        add_flag(parts, "phase_vcf", "true" if args.phase_vcf else "false")
    return parts


def build_command(args: argparse.Namespace) -> str:
    mounts = mount_roots(args)
    run_flags = build_run_deepvariant_flags(args, mounts)

    if args.engine == "docker":
        command = ["sudo", "docker", "run"] if args.sudo else ["docker", "run"]
        if args.gpu:
            command.extend(["--gpus", "1"])
        for host, container in mounts.items():
            command.extend(["-v", f"{host}:{container}"])
        command.append(image_tag(args))
        command.append("/opt/deepvariant/bin/run_deepvariant")
        command.extend(run_flags)
        return " \\\n  ".join(quote(part) for part in command)

    command = ["singularity", "run"]
    if args.gpu:
        command.append("--nv")
    if args.cleanenv:
        command.append("--cleanenv")
    for host, container in mounts.items():
        command.extend(["-B", f"{host}:{container}"])
    command.append(f"docker://{image_tag(args)}")
    command.append("/opt/deepvariant/bin/run_deepvariant")
    command.extend(run_flags)
    return " \\\n  ".join(quote(part) for part in command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and statically validate a DeepVariant germline run_deepvariant Docker/Singularity command without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--engine", choices=["docker", "singularity"], default="docker")
    parser.add_argument("--image-version", default="1.10.0", help="DeepVariant image version; append -gpu or pass --gpu for GPU image")
    parser.add_argument("--gpu", action="store_true", help="Add Docker --gpus 1 or Singularity --nv and use the -gpu image tag")
    parser.add_argument("--sudo", action="store_true", help="Prefix Docker command with sudo")
    parser.add_argument("--cleanenv", action="store_true", help="Add Singularity --cleanenv")

    parser.add_argument("--model-type", required=True, choices=sorted(MODEL_TYPES))
    parser.add_argument("--ref", required=True, help="Host path to FASTA or bgzipped FASTA reference")
    parser.add_argument("--reads", required=True, help="Host path to aligned, sorted, indexed BAM or CRAM")
    parser.add_argument("--output-vcf", required=True, help="Host output VCF path, usually *.vcf.gz")
    parser.add_argument("--output-gvcf", help="Host output gVCF path, usually *.g.vcf.gz")
    parser.add_argument("--regions", help="Region literal(s) or BED/BEDPE path; quote space-separated lists")
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--vcf-stats-report", action="store_true")
    parser.add_argument("--logging-dir")
    parser.add_argument("--runtime-report", action="store_true")
    parser.add_argument("--intermediate-results-dir")
    parser.add_argument("--dry-run", action="store_true", help="Add run_deepvariant --dry_run=true")

    parser.add_argument("--customized-model")
    parser.add_argument("--customized-model-json")
    parser.add_argument("--customized-small-model")
    parser.add_argument("--disable-small-model", action="store_true")
    parser.add_argument("--haploid-contigs")
    parser.add_argument("--par-regions-bed")
    parser.add_argument("--sample-name")
    parser.add_argument("--report-title")
    parser.add_argument("--make-examples-extra-args")
    parser.add_argument("--call-variants-extra-args")
    parser.add_argument("--postprocess-variants-extra-args")
    parser.add_argument("--phase-vcf", dest="phase_vcf", action="store_true", default=None)
    parser.add_argument("--no-phase-vcf", dest="phase_vcf", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings = validate(args)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"  WARNING: {warning}", file=sys.stderr)
        return 2

    print("# DeepVariant command preview; review mounts/resources before running.")
    for warning in warnings:
        print(f"# WARNING: {warning}")
    print(build_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
