#!/usr/bin/env python3
"""Local-only hailtop.batch smoke/template for generated Hail repo skills.

Default mode is dry-run: it prints the workflow that would be executed without
importing Hail or touching Docker/cloud services. Use --run to execute a tiny
LocalBackend DAG against temporary files.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from textwrap import dedent


DRY_RUN_TEMPLATE = """\
Local-only hailtop.batch smoke plan:
  1. Create a temporary input file containing two lines.
  2. Build hb.LocalBackend(tmp_dir=<temporary scratch>). No cloud credentials are used.
  3. Create a Batch with three shell jobs:
     - copy-input: reads the input via batch.read_input and writes a job resource file.
     - summarize: references copy-input.copied, so Batch infers a file dependency.
     - finalize: also calls depends_on(summarize) to demonstrate explicit dependencies.
  4. Persist the final job resource with batch.write_output.
  5. Verify the output text is exactly "lines=2".

Run with:
  python scripts/batch_local_smoke.py --run
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print or run a safe local-only hailtop.batch smoke DAG. "
            "The default is --dry-run; --run executes against temporary files."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print the smoke plan without importing Hail (default)")
    mode.add_argument("--run", action="store_true", help="execute the local smoke DAG with hailtop.batch.LocalBackend")
    parser.add_argument(
        "--name",
        default="disco-local-smoke",
        help="Batch name to use in --run mode (default: %(default)s)",
    )
    return parser.parse_args(argv)


def close_backend(backend: object) -> None:
    close = getattr(backend, "close", None)
    if callable(close):
        close()


def run_smoke(name: str) -> int:
    try:
        import hailtop.batch as hb
    except Exception as exc:  # pragma: no cover - exercised in incomplete environments
        print(
            "Could not import hailtop.batch. Verify the active Python environment has the Hail package installed.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="hail-batch-smoke-") as workdir_text:
        workdir = Path(workdir_text)
        input_path = workdir / "input.txt"
        output_path = workdir / "summary.txt"
        scratch_dir = workdir / "scratch"
        input_path.write_text("alpha\nbeta\n", encoding="utf-8")

        backend = hb.LocalBackend(tmp_dir=str(scratch_dir))
        try:
            batch = hb.Batch(name=name, backend=backend)

            copy_input = batch.new_job(name="copy-input")
            input_file = batch.read_input(str(input_path))
            copy_input.command(f"cat {input_file} > {copy_input.copied}")

            summarize = batch.new_job(name="summarize")
            summarize.command(f"echo lines=$(wc -l < {copy_input.copied}) > {summarize.ofile}")

            finalize = batch.new_job(name="finalize")
            finalize.depends_on(summarize)
            finalize.command(f"cat {summarize.ofile} > {finalize.ofile}")

            batch.write_output(finalize.ofile, str(output_path))
            batch.run()
        finally:
            close_backend(backend)

        observed = output_path.read_text(encoding="utf-8").strip()
        expected = "lines=2"
        if observed != expected:
            print(f"Smoke failed: expected {expected!r}, observed {observed!r}", file=sys.stderr)
            return 1

    print("LocalBackend smoke succeeded: lines=2")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.run:
        print(dedent(DRY_RUN_TEMPLATE).rstrip())
        return 0
    return run_smoke(args.name)


if __name__ == "__main__":
    raise SystemExit(main())
