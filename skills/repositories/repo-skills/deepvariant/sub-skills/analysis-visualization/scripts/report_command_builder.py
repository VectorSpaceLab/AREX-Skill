#!/usr/bin/env python3
"""Build safe DeepVariant analysis/report command previews.

This helper validates common local path and flag combinations for DeepVariant
post-run analysis tools and prints Docker or Singularity command previews. It
never executes DeepVariant, Docker, Singularity, hap.py, or report binaries.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shlex
import sys
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_TYPES = {"channels", "RGB", "both", "none"}
LOCAL_FILE_SUFFIXES = (
    ".vcf",
    ".gz",
    ".tbi",
    ".tsv",
    ".csv",
    ".html",
    ".json",
    ".tfrecord",
    ".bed",
    ".bedpe",
)
REGION_FILE_SUFFIXES = (".bed", ".bed.gz", ".bedpe", ".bedpe.gz")
SHARDED_SPEC_RE = re.compile(r"@([1-9][0-9]*)")
REGION_LITERAL_RE = re.compile(
    r"^[A-Za-z0-9_.-]+(?::[0-9,]+(?:-[0-9,]+)?)?$"
)


def quote(value: object) -> str:
    return shlex.quote(str(value))


def shell_join(parts: Sequence[str]) -> str:
    return " \\\n  ".join(quote(part) for part in parts)


def is_remote_path(value: str) -> bool:
    return value.startswith(("gs://", "s3://", "http://", "https://"))


def is_local_path_like(value: Optional[str], assume_path: bool = False) -> bool:
    if not value or is_remote_path(value):
        return False
    if assume_path:
        return True
    path = Path(value).expanduser()
    return (
        value.startswith(("/", "~", "./", "../"))
        or "/" in value
        or "\\" in value
        or str(path).endswith(LOCAL_FILE_SUFFIXES)
        or path.exists()
    )


def is_region_file_token(token: str) -> bool:
    if is_remote_path(token):
        return token.endswith(REGION_FILE_SUFFIXES)
    path = Path(token).expanduser()
    return (
        token.endswith(REGION_FILE_SUFFIXES)
        or token.startswith(("/", "~", "./", "../"))
        or "/" in token
        or "\\" in token
        or path.exists()
    )


def local_path(value: Optional[str], assume_path: bool = False) -> Optional[Path]:
    if not value or is_remote_path(value):
        return None
    if not is_local_path_like(value, assume_path=assume_path):
        return None
    return Path(value).expanduser()


def path_exists(path: Optional[Path]) -> bool:
    if path is None:
        return False
    try:
        return path.exists()
    except OSError:
        return False


def parent_exists(path: Optional[Path]) -> bool:
    if path is None:
        return False
    try:
        return path.parent.exists()
    except OSError:
        return False


def is_sharded_spec(value: Optional[str]) -> bool:
    return bool(value and SHARDED_SPEC_RE.search(value))


def expected_visual_report_path(outfile_base: str) -> str:
    return f"{outfile_base}.visual_report.html"


def expected_runtime_output_path(output: str) -> str:
    return output if output.endswith("html") else f"{output}.html"


def companion_exists(path: Path, suffixes: Iterable[str]) -> bool:
    return any(path_exists(Path(str(path) + suffix)) for suffix in suffixes)


def add_flag(parts: List[str], name: str, value: Optional[object] = None) -> None:
    flag = f"--{name}"
    if value is None:
        parts.append(flag)
    else:
        parts.append(f"{flag}={value}")


def warn_for_relative_path(value: Optional[str], label: str, warnings: List[str]) -> None:
    if not value or is_remote_path(value):
        return
    if is_local_path_like(value, assume_path=True) and not Path(value).expanduser().is_absolute():
        warnings.append(
            f"{label} is relative; it will be resolved from the directory where this helper is run."
        )


def validate_region_tokens(
    regions: Optional[str], errors: List[str], warnings: List[str]
) -> None:
    if not regions:
        return
    for token in regions.split():
        if is_region_file_token(token):
            candidate = local_path(token, assume_path=True)
            if candidate is not None and not path_exists(candidate):
                errors.append(f"--regions file does not exist: {candidate}")
            if is_remote_path(token):
                warnings.append(
                    f"--regions remote BED/BEDPE path {token!r} cannot be verified locally."
                )
            continue
        if not REGION_LITERAL_RE.match(token):
            warnings.append(
                f"could not statically classify --regions token {token!r}; verify it is a valid region literal or mounted BED/BEDPE path."
            )


def path_mount_root(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    if path.exists() and path.is_dir():
        return resolved
    return resolved.parent


def collect_mount_roots(
    path_values: Iterable[Optional[str]],
    region_values: Iterable[Optional[str]] = (),
) -> Dict[Path, str]:
    roots: List[Path] = []

    for value in path_values:
        path = local_path(value, assume_path=True)
        if path is None:
            continue
        root = path_mount_root(path)
        if root not in roots:
            roots.append(root)

    for value in region_values:
        if not value:
            continue
        for token in value.split():
            if not is_region_file_token(token) or is_remote_path(token):
                continue
            path = Path(token).expanduser()
            root = path_mount_root(path)
            if root not in roots:
                roots.append(root)

    roots_sorted = sorted(roots, key=lambda item: (len(str(item)), str(item)))
    selected: List[Path] = []
    for root in roots_sorted:
        if not any(root == parent or parent in root.parents for parent in selected):
            selected.append(root)

    return {
        root: "/dv_analysis" if index == 0 else f"/dv_analysis_{index}"
        for index, root in enumerate(selected)
    }


def containerize_local_path(value: str, mounts: Dict[Path, str]) -> str:
    if is_remote_path(value) or not is_local_path_like(value, assume_path=True):
        return value
    path = Path(value).expanduser().resolve(strict=False)
    best: Optional[Tuple[Path, str]] = None
    for root, mount in mounts.items():
        if path == root or root in path.parents:
            if best is None or len(str(root)) > len(str(best[0])):
                best = (root, mount)
    if best is None:
        return value
    root, mount = best
    relative = path.relative_to(root)
    if str(relative) == ".":
        return mount
    return str(Path(mount) / relative)


def containerize_value(
    value: Optional[str],
    mounts: Dict[Path, str],
    token_filter: Optional[Callable[[str], bool]] = None,
) -> Optional[str]:
    if value is None:
        return None
    tokens = value.split()
    if len(tokens) > 1 or token_filter is not None:
        converted: List[str] = []
        for token in tokens:
            if token_filter is None or token_filter(token):
                converted.append(containerize_local_path(token, mounts))
            else:
                converted.append(token)
        return " ".join(converted)
    return containerize_local_path(value, mounts)


def image_tag(args: argparse.Namespace) -> str:
    return f"google/deepvariant:{args.image_version}"


def base_command(args: argparse.Namespace, mounts: Dict[Path, str]) -> List[str]:
    if args.engine == "docker":
        command = ["sudo", "docker", "run"] if args.sudo else ["docker", "run"]
        for host, container in mounts.items():
            command.extend(["-v", f"{host}:{container}"])
        command.append(image_tag(args))
        return command

    command = ["singularity", "run"]
    if args.cleanenv:
        command.append("--cleanenv")
    for host, container in mounts.items():
        command.extend(["-B", f"{host}:{container}"])
    command.append(f"docker://{image_tag(args)}")
    return command


def validate_common(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if args.image_version != "1.10.0":
        warnings.append(
            "This skill is based on DeepVariant 1.10.0 evidence; confirm tool flags for other image tags."
        )
    if args.engine == "singularity":
        warnings.append(
            "Singularity preview assumes docker:// images are allowed or cached locally; confirm site policy before execution."
        )
    return errors, warnings


def validate_vcf_stats(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors, warnings = validate_common(args)
    input_vcf = local_path(args.input_vcf, assume_path=True)
    outfile_base = local_path(args.outfile_base, assume_path=True)

    warn_for_relative_path(args.input_vcf, "--input-vcf", warnings)
    warn_for_relative_path(args.outfile_base, "--outfile-base", warnings)

    if input_vcf is not None and not path_exists(input_vcf):
        errors.append(f"--input-vcf does not exist: {input_vcf}")
    if input_vcf is not None and path_exists(input_vcf):
        if not str(input_vcf).endswith((".vcf", ".vcf.gz")):
            warnings.append(
                "--input-vcf does not end with .vcf or .vcf.gz; confirm it is readable as VCF."
            )
        if str(input_vcf).endswith(".vcf.gz") and not companion_exists(input_vcf, (".tbi",)):
            warnings.append(
                "bgzipped VCF is missing a colocated .tbi index; reporting or downstream review may fail in containerized environments."
            )
    if outfile_base is not None and not parent_exists(outfile_base):
        warnings.append(
            f"Output parent does not exist yet; create or mount it before running: {outfile_base.parent}"
        )
    if args.outfile_base.endswith(".visual_report.html"):
        warnings.append(
            "--outfile-base should be a base path; DeepVariant will append .visual_report.html again."
        )
    elif args.outfile_base.endswith(".html"):
        warnings.append(
            "--outfile-base ends with .html; output will still be <outfile_base>.visual_report.html."
        )
    if args.num_records is not None and args.num_records == 0:
        errors.append("--num-records must be non-zero when provided")
    warnings.append(f"Expected report path: {expected_visual_report_path(args.outfile_base)}")
    warnings.append(
        "vcf_stats_report requires a single-sample VCF with a GT FORMAT field; this helper does not parse VCF headers."
    )
    return errors, warnings


def build_vcf_stats(args: argparse.Namespace) -> str:
    mounts = collect_mount_roots([args.input_vcf, args.outfile_base])
    command = base_command(args, mounts)
    command.append("/opt/deepvariant/bin/vcf_stats_report")
    add_flag(command, "input_vcf", containerize_value(args.input_vcf, mounts))
    add_flag(command, "outfile_base", containerize_value(args.outfile_base, mounts))
    if args.title:
        add_flag(command, "title", args.title)
    if args.num_records is not None:
        add_flag(command, "num_records", args.num_records)
    return shell_join(command)


def validate_runtime(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors, warnings = validate_common(args)
    runtime_tsv = local_path(args.runtime_tsv, assume_path=True)
    output_html = local_path(args.output_html, assume_path=True)

    warn_for_relative_path(args.runtime_tsv, "--runtime-tsv", warnings)
    warn_for_relative_path(args.output_html, "--output-html", warnings)
    if args.logging_dir:
        warn_for_relative_path(args.logging_dir, "--logging-dir", warnings)

    if runtime_tsv is not None:
        if is_sharded_spec(args.runtime_tsv):
            warnings.append(
                "Runtime TSV uses a sharded spec; confirm all expanded shards exist before running runtime_by_region_vis."
            )
        elif not path_exists(runtime_tsv):
            errors.append(f"--runtime-tsv does not exist: {runtime_tsv}")
    if output_html is not None and not parent_exists(output_html):
        warnings.append(
            f"Output parent does not exist yet; create or mount it before running: {output_html.parent}"
        )
    if not args.output_html.endswith("html"):
        warnings.append(
            f"runtime_by_region_vis will write {expected_runtime_output_path(args.output_html)} because --output lacks an html suffix."
        )
    if args.logging_dir and "make_examples_runtime_by_region" not in args.runtime_tsv:
        warnings.append(
            "Wrapper-created runtime TSVs usually live under logging_dir/make_examples_runtime_by_region/."
        )
    warnings.append(
        "Runtime TSVs are produced only when make_examples ran with --runtime_by_region, usually through wrapper --runtime_report and --logging_dir."
    )
    return errors, warnings


def build_runtime(args: argparse.Namespace) -> str:
    mounts = collect_mount_roots([args.runtime_tsv, args.output_html, args.logging_dir])
    command = base_command(args, mounts)
    command.append("/opt/deepvariant/bin/runtime_by_region_vis")
    add_flag(command, "input", containerize_value(args.runtime_tsv, mounts))
    add_flag(command, "output", containerize_value(args.output_html, mounts))
    add_flag(command, "title", args.title)
    return shell_join(command)


def validate_show_examples(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors, warnings = validate_common(args)
    examples = local_path(args.examples, assume_path=True)
    output_prefix = local_path(args.output_prefix, assume_path=True)

    warn_for_relative_path(args.examples, "--examples", warnings)
    warn_for_relative_path(args.output_prefix, "--output-prefix", warnings)

    if examples is not None:
        if is_sharded_spec(args.examples):
            warnings.append(
                "Examples path uses a sharded spec; pair it with --regions, --vcf, --filter-by-tsv, --num-records, or --max-examples-to-scan for bounded review."
            )
        elif not path_exists(examples):
            errors.append(f"--examples does not exist: {examples}")

    if args.example_info_json and args.example_info_json != "auto":
        warn_for_relative_path(args.example_info_json, "--example-info-json", warnings)
        info = local_path(args.example_info_json, assume_path=True)
        if info is not None and not path_exists(info):
            errors.append(f"--example-info-json does not exist: {info}")

    for label, value in (("--vcf", args.vcf), ("--filter-by-tsv", args.filter_by_tsv)):
        if value:
            warn_for_relative_path(value, label, warnings)
            candidate = local_path(value, assume_path=True)
            if candidate is not None and not path_exists(candidate):
                errors.append(f"{label} path does not exist: {candidate}")

    if args.column_labels and args.example_info_json and args.example_info_json != "auto":
        errors.append("Set at most one of --column-labels and an explicit --example-info-json")
    if args.image_type not in IMAGE_TYPES:
        errors.append(f"unsupported --image-type {args.image_type!r}")
    if args.num_records is not None and args.num_records < 1:
        errors.append("--num-records must be >= 1")
    if args.max_examples_to_scan is not None and args.max_examples_to_scan < 1:
        errors.append("--max-examples-to-scan must be >= 1")
    if args.scale < 1:
        errors.append("--scale must be >= 1")

    validate_region_tokens(args.regions, errors, warnings)

    if output_prefix is not None and not parent_exists(output_prefix):
        warnings.append(
            f"Output prefix parent does not exist yet; create or mount it before running: {output_prefix.parent}"
        )
    if args.image_type == "both":
        warnings.append("--image-type=both writes two PNGs per selected example; use a small --num-records for review.")
    if args.write_tfrecords:
        warnings.append("--write-tfrecords creates filtered TFRecord data in addition to visualization outputs.")
    if args.curate:
        warnings.append("--curate writes a curation TSV next to the output prefix.")
    if not any([args.vcf, args.regions, args.filter_by_tsv, args.num_records, args.max_examples_to_scan]):
        warnings.append("No bounding filter or record limit was provided; show_examples can scan and write many records.")
    if args.output_prefix.endswith(("/", "\\")):
        warnings.append("--output-prefix behaves as a filename prefix; a trailing separator can produce surprising filenames.")
    warnings.append("show_examples output is a prefix, not a directory-only argument; generated filenames append locus IDs to this value.")
    return errors, warnings


def build_show_examples(args: argparse.Namespace) -> str:
    mounts = collect_mount_roots(
        [
            args.examples,
            None if args.example_info_json == "auto" else args.example_info_json,
            args.vcf,
            args.output_prefix,
            args.filter_by_tsv,
        ],
        region_values=[args.regions],
    )
    command = base_command(args, mounts)
    command.append("/opt/deepvariant/bin/show_examples")
    add_flag(command, "examples", containerize_value(args.examples, mounts))
    if args.example_info_json:
        value = "auto" if args.example_info_json == "auto" else containerize_value(args.example_info_json, mounts)
        add_flag(command, "example_info_json", value)
    if args.vcf:
        add_flag(command, "vcf", containerize_value(args.vcf, mounts))
    if args.regions:
        add_flag(command, "regions", containerize_value(args.regions, mounts, token_filter=is_region_file_token))
    add_flag(command, "output", containerize_value(args.output_prefix, mounts))
    add_flag(command, "image_type", args.image_type)
    if args.num_records is not None:
        add_flag(command, "num_records", args.num_records)
    if args.max_examples_to_scan is not None:
        add_flag(command, "max_examples_to_scan", args.max_examples_to_scan)
    if args.column_labels:
        add_flag(command, "column_labels", args.column_labels)
    if args.filter_by_tsv:
        add_flag(command, "filter_by_tsv", containerize_value(args.filter_by_tsv, mounts))
    if args.scale != 1:
        add_flag(command, "scale", args.scale)
    if args.no_annotation:
        add_flag(command, "noannotation")
    if args.no_truth_labels:
        add_flag(command, "notruth_labels")
    if args.curate:
        add_flag(command, "curate")
    if args.write_tfrecords:
        add_flag(command, "write_tfrecords")
    if args.verbose:
        add_flag(command, "verbose")
    return shell_join(command)


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--engine", choices=["docker", "singularity"], default="docker")
    parser.add_argument("--image-version", default="1.10.0")
    parser.add_argument("--sudo", action="store_true", help="Prefix Docker command with sudo")
    parser.add_argument("--cleanenv", action="store_true", help="Add Singularity --cleanenv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build DeepVariant report command previews without executing them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    vcf_stats = subparsers.add_parser("vcf-stats", help="Preview vcf_stats_report command")
    add_common_arguments(vcf_stats)
    vcf_stats.add_argument("--input-vcf", required=True)
    vcf_stats.add_argument("--outfile-base", required=True)
    vcf_stats.add_argument("--title")
    vcf_stats.add_argument("--num-records", type=int)
    vcf_stats.set_defaults(validate=validate_vcf_stats, build=build_vcf_stats)

    runtime = subparsers.add_parser("runtime", help="Preview runtime_by_region_vis command")
    add_common_arguments(runtime)
    runtime.add_argument("--runtime-tsv", required=True)
    runtime.add_argument("--output-html", required=True)
    runtime.add_argument("--title", required=True)
    runtime.add_argument("--logging-dir", help="Optional logging directory for wrapper-layout sanity checks")
    runtime.set_defaults(validate=validate_runtime, build=build_runtime)

    show_examples = subparsers.add_parser("show-examples", help="Preview show_examples command")
    add_common_arguments(show_examples)
    show_examples.add_argument("--examples", required=True)
    show_examples.add_argument("--example-info-json", default="auto")
    show_examples.add_argument("--vcf")
    show_examples.add_argument("--regions")
    show_examples.add_argument("--output-prefix", required=True)
    show_examples.add_argument("--image-type", default="channels", choices=sorted(IMAGE_TYPES))
    show_examples.add_argument("--num-records", type=int)
    show_examples.add_argument("--max-examples-to-scan", type=int)
    show_examples.add_argument("--column-labels")
    show_examples.add_argument("--filter-by-tsv")
    show_examples.add_argument("--scale", type=int, default=1)
    show_examples.add_argument("--no-annotation", action="store_true")
    show_examples.add_argument("--no-truth-labels", action="store_true")
    show_examples.add_argument("--curate", action="store_true")
    show_examples.add_argument("--write-tfrecords", action="store_true")
    show_examples.add_argument("--verbose", action="store_true")
    show_examples.set_defaults(validate=validate_show_examples, build=build_show_examples)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings = args.validate(args)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"  WARNING: {warning}", file=sys.stderr)
        return 2

    print("# DeepVariant analysis command preview; review mounts/resources before running.")
    print("# This helper does not execute Docker, Singularity, DeepVariant, or hap.py.")
    for warning in warnings:
        print(f"# WARNING: {warning}")
    print(args.build(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
