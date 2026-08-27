#!/usr/bin/env python3
"""Construct and validate TFDS Beam pipeline option strings safely.

This helper never imports Apache Beam and never launches a pipeline. It only
builds the comma-separated value passed to `tfds build --beam_pipeline_options`
and prints warnings about external services, credentials, and common TFDS/Beam
pitfalls.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
import json
from pathlib import Path
import re
import shlex
import sys
from typing import Iterable

VALID_FILE_FORMATS = ("tfrecord", "array_record", "riegeli", "parquet")

RUNNER_ALIASES = {
    "direct": "DirectRunner",
    "directrunner": "DirectRunner",
    "local": "DirectRunner",
    "dataflow": "DataflowRunner",
    "dataflowrunner": "DataflowRunner",
    "flink": "FlinkRunner",
    "flinkrunner": "FlinkRunner",
    "spark": "SparkRunner",
    "sparkrunner": "SparkRunner",
    "portable": "PortableRunner",
    "portablerunner": "PortableRunner",
}

KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
DATAFLOW_JOB_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")


def normalize_runner(runner: str | None) -> str | None:
    if not runner:
        return None
    key = runner.replace("_", "").replace("-", "").lower()
    return RUNNER_ALIASES.get(key, runner)


def sanitize_job_name(raw: str) -> str:
    name = raw.lower()
    name = re.sub(r"[^a-z0-9-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    if not name or not name[0].isalpha():
        name = f"tfds-{name}" if name else "tfds-job"
    name = name[:63].rstrip("-")
    if not name[-1].isalnum():
        name = f"{name}0"
    return name


def parse_option_segment(segment: str, warnings: list[str]) -> tuple[str, str | None]:
    original = segment
    segment = segment.strip()
    if not segment:
        raise ValueError("empty option segment; remove repeated/trailing commas")
    if segment.startswith("--"):
        warnings.append(
            f"stripped leading '--' from {original!r}; TFDS adds '--' after splitting"
        )
        segment = segment[2:]
    if "=" in segment:
        key, value = segment.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            raise ValueError(f"option {key!r} has an empty value")
        if "," in value:
            raise ValueError(
                f"option {key!r} contains a comma in its value; TFDS splits on commas"
            )
    else:
        key, value = segment.strip(), None
    if not KEY_RE.match(key):
        raise ValueError(
            f"invalid Beam option key {key!r}; use letters/numbers/_/- and start with a letter"
        )
    return key, value


def parse_options_string(raw: str | None, warnings: list[str]) -> OrderedDict[str, str | None]:
    options: OrderedDict[str, str | None] = OrderedDict()
    if not raw:
        return options
    for segment in raw.split(","):
        key, value = parse_option_segment(segment, warnings)
        if key in options:
            warnings.append(f"duplicate option {key!r}; later value overrides earlier value")
        options[key] = value
    return options


def add_option(
    options: OrderedDict[str, str | None],
    key: str,
    value: str | int | None,
    *,
    warnings: list[str],
) -> None:
    if value is None or value == "":
        return
    key, parsed_value = parse_option_segment(f"{key}={value}", warnings)
    if key in options:
        warnings.append(f"explicit {key!r} overrides the value from --options")
    options[key] = parsed_value


def normalize_gcs_bucket(bucket: str | None) -> str | None:
    if not bucket:
        return None
    return bucket.rstrip("/")


def option_string(options: OrderedDict[str, str | None]) -> str:
    parts = []
    for key, value in options.items():
        if value is None:
            parts.append(key)
        else:
            parts.append(f"{key}={value}")
    return ",".join(parts)


def is_gcs_uri(value: str | None) -> bool:
    return bool(value and value.startswith("gs://"))


def local_path_exists(value: str | None) -> bool | None:
    if not value or "://" in value:
        return None
    return Path(value).expanduser().exists()


def build_tfds_command(args: argparse.Namespace, opts: str) -> str:
    dataset = args.dataset or "DATASET[/CONFIG]"
    if args.config and args.dataset and "/" not in args.dataset:
        dataset = f"{args.dataset}/{args.config}"

    cmd = ["tfds", "build", dataset]
    if args.data_dir:
        cmd.append(f"--data_dir={args.data_dir}")
    if opts:
        cmd.append(f"--beam_pipeline_options={opts}")
    if args.max_examples_per_split is not None:
        cmd.append(f"--max_examples_per_split={args.max_examples_per_split}")
    if args.file_format:
        cmd.append(f"--file_format={args.file_format}")
    if args.num_shards is not None:
        cmd.append(f"--num_shards={args.num_shards}")
    if args.max_shard_size_mb is not None:
        cmd.append(f"--max_shard_size_mb={args.max_shard_size_mb}")
    if args.nondeterministic_order:
        cmd.append("--nondeterministic_order")
    return " ".join(shlex.quote(part) for part in cmd)


def collect_options(args: argparse.Namespace, warnings: list[str]) -> OrderedDict[str, str | None]:
    options = parse_options_string(args.options, warnings)
    bucket = normalize_gcs_bucket(args.gcs_bucket)
    runner = normalize_runner(args.runner)

    if runner:
        add_option(options, "runner", runner, warnings=warnings)
    if args.project:
        add_option(options, "project", args.project, warnings=warnings)
    if args.region:
        add_option(options, "region", args.region, warnings=warnings)

    job_name = args.job_name
    if not job_name and args.dataset and runner == "DataflowRunner":
        job_name = sanitize_job_name(f"{args.dataset}-gen")
    if job_name:
        add_option(options, "job_name", job_name, warnings=warnings)

    staging_location = args.staging_location
    temp_location = args.temp_location
    if bucket:
        staging_location = staging_location or f"{bucket}/binaries"
        temp_location = temp_location or f"{bucket}/temp"
    add_option(options, "staging_location", staging_location, warnings=warnings)
    add_option(options, "temp_location", temp_location, warnings=warnings)

    add_option(options, "requirements_file", args.requirements_file, warnings=warnings)
    add_option(options, "setup_file", args.setup_file, warnings=warnings)
    add_option(options, "flink_version", args.flink_version, warnings=warnings)
    add_option(options, "flink_conf_dir", args.flink_conf_dir, warnings=warnings)

    for extra in args.extra or []:
        key, value = parse_option_segment(extra, warnings)
        if key in options:
            warnings.append(f"extra option {key!r} overrides an earlier value")
        options[key] = value

    return options


def validate(args: argparse.Namespace, options: OrderedDict[str, str | None]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    runner = normalize_runner(options.get("runner") if options.get("runner") else args.runner)
    staging = options.get("staging_location")
    temp = options.get("temp_location")
    project = options.get("project")
    job_name = options.get("job_name")

    if args.num_shards is not None and args.num_shards <= 0:
        errors.append("--num-shards must be positive")
    if args.max_shard_size_mb is not None and args.max_shard_size_mb <= 0:
        errors.append("--max-shard-size-mb must be positive")
    if args.max_examples_per_split is not None and args.max_examples_per_split < 0:
        errors.append("--max-examples-per-split must be zero or positive")

    if args.file_format == "array_record":
        warnings.append(
            "array_record supports random-access/as_data_source workflows; as_dataset/tf.data is not implemented for this format in this TFDS version"
        )
    if args.file_format in {"riegeli", "parquet"}:
        warnings.append(
            f"{args.file_format} may require optional reader/writer dependencies in both local and worker environments"
        )

    if args.nondeterministic_order:
        warnings.append(
            "nondeterministic order can speed Beam writes but prepared example order is not reproducible"
        )

    if runner == "DataflowRunner":
        warnings.append(
            "DataflowRunner uses external Google Cloud services; this helper does not check billing, quotas, IAM, or launch a job"
        )
        for key, value in (
            ("project", project),
            ("staging_location", staging),
            ("temp_location", temp),
        ):
            if not value:
                message = f"DataflowRunner usually requires {key}"
                if args.strict:
                    errors.append(message)
                else:
                    warnings.append(message)
        for key, value in (("staging_location", staging), ("temp_location", temp)):
            if value and not is_gcs_uri(value):
                warnings.append(f"Dataflow {key} is normally a gs:// path; got {value!r}")
        if args.data_dir and not is_gcs_uri(args.data_dir):
            warnings.append(
                "Dataflow workers usually need a shared data_dir such as gs://BUCKET/tensorflow_datasets"
            )
        if job_name and not DATAFLOW_JOB_RE.match(job_name):
            message = (
                "Dataflow job_name should be lowercase letters/numbers/hyphens, "
                "start with a letter, end with a letter/number, and be at most 63 chars"
            )
            if args.strict:
                errors.append(message)
            else:
                warnings.append(message)
        if not (options.get("requirements_file") or options.get("setup_file")):
            warnings.append(
                "cloud workers must be able to import tensorflow_datasets and dataset-specific extras; pass requirements_file or setup_file when needed"
            )
    elif runner == "FlinkRunner":
        warnings.append(
            "FlinkRunner is external to TFDS; verify Apache Beam/Flink version compatibility before launch"
        )
        if not options.get("flink_version"):
            warnings.append("FlinkRunner commonly needs flink_version")
        if not options.get("flink_conf_dir"):
            warnings.append("FlinkRunner commonly needs flink_conf_dir or another valid Flink runner configuration")
    elif runner == "DirectRunner":
        warnings.append(
            "DirectRunner/local Beam is suitable for tiny smokes; full Beam datasets can exceed local RAM, disk, or time"
        )
    elif runner:
        warnings.append(
            f"runner {runner!r} was not classified by this helper; validate required runner-specific options separately"
        )

    for key, value in options.items():
        if value and is_gcs_uri(value):
            warnings.append(f"{key} points at GCS; credentials and permissions are not verified")
        exists = local_path_exists(value)
        if key in {"requirements_file", "setup_file"} and exists is False:
            warnings.append(f"{key} local path does not exist: {value}")

    if args.data_dir and is_gcs_uri(args.data_dir):
        warnings.append("data_dir points at GCS; read/write credentials and network costs are not verified")

    return warnings, errors


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct/validate a TFDS --beam_pipeline_options string without "
            "importing Apache Beam or launching a pipeline."
        )
    )
    parser.add_argument("--options", help="Existing comma-separated options string to validate/extend.")
    parser.add_argument("--runner", help="Beam runner or alias: direct/local, dataflow, flink, spark, portable.")
    parser.add_argument("--project", help="GCP project for Dataflow-style options.")
    parser.add_argument("--region", help="Cloud region option when required by the runner.")
    parser.add_argument("--job-name", help="Beam/Dataflow job_name. Defaults from --dataset for Dataflow.")
    parser.add_argument("--gcs-bucket", help="Base gs:// bucket used to derive staging/temp defaults.")
    parser.add_argument("--staging-location", help="Beam staging_location option.")
    parser.add_argument("--temp-location", help="Beam temp_location option.")
    parser.add_argument("--requirements-file", help="Worker requirements_file option.")
    parser.add_argument("--setup-file", help="Worker setup_file option.")
    parser.add_argument("--flink-version", help="Flink runner version option.")
    parser.add_argument("--flink-conf-dir", help="Flink config directory option.")
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        metavar="KEY[=VALUE]",
        help="Additional Beam option segment. Repeatable.",
    )
    parser.add_argument("--dataset", help="Dataset name for suggested tfds build command and default job name.")
    parser.add_argument("--config", help="Optional config name for suggested command when --dataset has no slash.")
    parser.add_argument("--data-dir", help="TFDS data_dir for suggested command and GCS/locality warnings.")
    parser.add_argument(
        "--file-format",
        choices=VALID_FILE_FORMATS,
        help="TFDS --file_format value to include in suggested command.",
    )
    parser.add_argument("--num-shards", type=int, help="TFDS --num_shards value to validate/include.")
    parser.add_argument(
        "--max-shard-size-mb",
        type=int,
        help="TFDS --max_shard_size_mb value to validate/include.",
    )
    parser.add_argument(
        "--max-examples-per-split",
        type=int,
        help="TFDS --max_examples_per_split value for smoke commands.",
    )
    parser.add_argument(
        "--nondeterministic-order",
        action="store_true",
        help="Include/warn about TFDS --nondeterministic_order in suggested command.",
    )
    parser.add_argument(
        "--print-build-command",
        action="store_true",
        help="Print a suggested tfds build command. The command is not executed.",
    )
    parser.add_argument("--shell-quote", action="store_true", help="Shell-quote the option string output.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing required Dataflow fields and invalid Dataflow job names as errors.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    construction_warnings: list[str] = []
    try:
        options = collect_options(args, construction_warnings)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"errors": [str(exc)], "not_launched": True}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    validation_warnings, errors = validate(args, options)
    warnings = construction_warnings + validation_warnings
    opts = option_string(options)
    displayed_opts = shlex.quote(opts) if args.shell_quote else opts
    command = build_tfds_command(args, opts) if args.print_build_command else None

    if args.json:
        print(
            json.dumps(
                {
                    "beam_pipeline_options": opts,
                    "displayed_beam_pipeline_options": displayed_opts,
                    "tfds_build_command": command,
                    "warnings": warnings,
                    "errors": errors,
                    "not_launched": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("beam_pipeline_options:")
        print(displayed_opts)
        if command:
            print("\nsuggested_tfds_build_command_not_executed:")
            print(command)
        if warnings:
            print("\nwarnings:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("\nerrors:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
