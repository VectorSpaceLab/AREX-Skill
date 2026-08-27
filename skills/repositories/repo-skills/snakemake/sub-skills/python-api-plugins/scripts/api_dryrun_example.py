#!/usr/bin/env python3
"""Run a safe Snakemake Python API dry-run on a tiny or user-provided workflow."""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import tempfile
from pathlib import Path
from textwrap import dedent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise Snakemake's Python API without shelling out. By default, "
            "the script creates a temporary tiny workflow and runs executor='dryrun'."
        )
    )
    parser.add_argument(
        "--snakefile",
        type=Path,
        help="Existing Snakefile to inspect. If omitted, a temporary demo Snakefile is used.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Workflow working directory. Defaults to the Snakefile parent or a temporary demo directory.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target rule or file. May be supplied multiple times. Defaults to the workflow default target.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary instead of executing the dry-run plan.",
    )
    parser.add_argument(
        "--dag",
        action="store_true",
        help="Print DOT DAG output instead of executing the dry-run plan.",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="Capture stdout/stderr around the API call and print captured sections with labels.",
    )
    return parser


@contextlib.contextmanager
def workflow_inputs(args: argparse.Namespace):
    if args.snakefile is not None:
        snakefile = args.snakefile.resolve()
        workdir = (args.workdir or snakefile.parent).resolve()
        yield snakefile, workdir
        return

    with tempfile.TemporaryDirectory(prefix="snakemake-api-dryrun-") as tmp:
        workdir = Path(tmp)
        snakefile = workdir / "Snakefile"
        snakefile.write_text(
            dedent(
                """
                rule all:
                    input: "result.txt"

                rule make_result:
                    output: "result.txt"
                    shell: "echo api-demo > {output}"
                """
            ).lstrip(),
            encoding="utf-8",
        )
        yield snakefile, workdir


def run_api(args: argparse.Namespace, snakefile: Path, workdir: Path) -> None:
    try:
        from snakemake.api import SnakemakeApi
        from snakemake.settings.types import (
            DAGSettings,
            ExecutionSettings,
            OutputSettings,
            ResourceSettings,
        )
    except ModuleNotFoundError as exc:
        if exc.name == "snakemake":
            raise RuntimeError(
                "Snakemake is not importable in this Python environment. "
                "Install Snakemake or run this script with the Python environment "
                "that provides the snakemake package."
            ) from exc
        raise

    targets = frozenset(args.target)
    output_settings = OutputSettings(
        dryrun=not (args.summary or args.dag),
        printshellcmds=True,
        stdout=True,
        verbose=False,
    )

    with SnakemakeApi(output_settings=output_settings) as snakemake_api:
        workflow_api = snakemake_api.workflow(
            resource_settings=ResourceSettings(cores=1),
            snakefile=snakefile,
            workdir=workdir,
        )
        dag_api = workflow_api.dag(DAGSettings(targets=targets))

        if args.summary:
            dag_api.summary(detailed=False)
        elif args.dag:
            dag_api.printdag()
        else:
            dag_api.execute_workflow(
                executor="dryrun",
                execution_settings=ExecutionSettings(),
            )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.summary and args.dag:
        parser.error("choose at most one of --summary or --dag")

    with workflow_inputs(args) as (snakefile, workdir):
        try:
            if args.capture:
                stdout_buffer = io.StringIO()
                stderr_buffer = io.StringIO()
                with contextlib.redirect_stdout(
                    stdout_buffer
                ), contextlib.redirect_stderr(stderr_buffer):
                    run_api(args, snakefile, workdir)
                print("--- captured stdout ---")
                print(stdout_buffer.getvalue(), end="")
                print("--- captured stderr ---")
                print(stderr_buffer.getvalue(), end="")
            else:
                run_api(args, snakefile, workdir)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
