#!/usr/bin/env python3
"""Smoke-test pysam samtools/bcftools command wrappers and print JSON."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check that pysam command dispatchers are importable, expose usage(), "
            "capture stderr, and can run tiny safe samtools/bcftools commands."
        )
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="Directory for generated tiny FASTA/index files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--skip-tiny-flow",
        action="store_true",
        help="Only inspect dispatcher objects and usage strings; do not create or index tiny files.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary directory when --outdir is not supplied.",
    )
    return parser


def summarize_usage(dispatcher: Any) -> dict[str, Any]:
    try:
        usage = dispatcher.usage()
    except Exception as exc:  # pragma: no cover - depends on installed htslib behavior
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "type": type(usage).__name__,
        "length": len(usage),
        "first_line": first_line(usage),
    }


def first_line(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    if not isinstance(value, str):
        value = repr(value)
    lines = value.splitlines()
    return lines[0] if lines else ""


def safe_len(value: Any) -> int | None:
    try:
        return len(value)
    except TypeError:
        return None


def flush_c_stdio() -> None:
    try:
        ctypes.CDLL(None).fflush(None)
    except Exception:
        pass


def call_dispatch(func: Any, *args: Any, **kwargs: Any) -> tuple[Any, str, str]:
    """Call a pysam dispatcher while capturing direct writes to stdout/stderr."""
    sys.stdout.flush()
    sys.stderr.flush()
    flush_c_stdio()
    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
        try:
            os.dup2(stdout_file.fileno(), 1)
            os.dup2(stderr_file.fileno(), 2)
            value = func(*args, **kwargs)
            sys.stdout.flush()
            sys.stderr.flush()
            flush_c_stdio()
        finally:
            os.dup2(saved_stdout, 1)
            os.dup2(saved_stderr, 2)
            os.close(saved_stdout)
            os.close(saved_stderr)
        stdout_file.seek(0)
        stderr_file.seek(0)
        captured_stdout = stdout_file.read().decode("utf-8", "replace")
        captured_stderr = stderr_file.read().decode("utf-8", "replace")
    return value, captured_stdout, captured_stderr


def run_tiny_flow(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    fasta_path = outdir / "tiny.fa"
    fasta_path.write_text(">chr1\nACGTACGTACGT\n", encoding="utf-8")

    result: dict[str, Any] = {"fasta": str(fasta_path), "steps": {}}

    try:
        faidx_return, captured_stdout, captured_stderr = call_dispatch(
            pysam_module.samtools.faidx, str(fasta_path)
        )
        result["steps"]["samtools_faidx"] = {
            "ok": True,
            "return_is_none": faidx_return is None,
            "captured_stdout_length": len(captured_stdout),
            "captured_stderr_first_line": first_line(captured_stderr),
            "fai_exists": fasta_path.with_suffix(".fa.fai").exists(),
            "messages": pysam_module.samtools.faidx.get_messages(),
        }
    except Exception as exc:
        result["steps"]["samtools_faidx"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        sequence, captured_stdout, captured_stderr = call_dispatch(
            pysam_module.samtools.faidx, str(fasta_path), "chr1:1-4"
        )
        observed = sequence or captured_stdout
        result["steps"]["samtools_faidx_region"] = {
            "ok": True,
            "type": type(sequence).__name__,
            "value": observed,
            "captured_stdout_length": len(captured_stdout),
            "captured_stderr_first_line": first_line(captured_stderr),
            "messages": pysam_module.samtools.faidx.get_messages(),
        }
    except Exception as exc:
        result["steps"]["samtools_faidx_region"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        split, captured_stdout, captured_stderr = call_dispatch(
            pysam_module.samtools.faidx, str(fasta_path), "chr1:1-4", split_lines=True
        )
        result["steps"]["split_lines"] = {
            "ok": True,
            "type": type(split).__name__,
            "length": safe_len(split),
            "value": split,
            "captured_stdout_lines": captured_stdout.splitlines(),
            "captured_stderr_first_line": first_line(captured_stderr),
        }
    except Exception as exc:
        result["steps"]["split_lines"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        output_path = outdir / "region.fa"
        saved, captured_stdout, captured_stderr = call_dispatch(
            pysam_module.samtools.faidx, str(fasta_path), "chr1:1-4", save_stdout=str(output_path)
        )
        result["steps"]["save_stdout"] = {
            "ok": True,
            "return_is_none": saved is None,
            "exists": output_path.exists(),
            "size": output_path.stat().st_size if output_path.exists() else None,
            "captured_stdout_length": len(captured_stdout),
            "captured_stderr_first_line": first_line(captured_stderr),
        }
    except Exception as exc:
        result["steps"]["save_stdout"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        quiet, captured_stdout, captured_stderr = call_dispatch(
            pysam_module.samtools.faidx, str(fasta_path), catch_stdout=False
        )
        result["steps"]["catch_stdout_false"] = {
            "ok": True,
            "return_is_none": quiet is None,
            "captured_stdout_length": len(captured_stdout),
            "captured_stderr_first_line": first_line(captured_stderr),
        }
    except Exception as exc:
        result["steps"]["catch_stdout_false"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        call_dispatch(pysam_module.samtools.faidx, str(outdir / "missing.fa"))
    except pysam_module.SamtoolsError as exc:
        result["steps"]["samtools_error"] = {
            "ok": True,
            "exception_type": type(exc).__name__,
            "exception_contains_stderr": "stderr=" in str(exc),
            "messages": pysam_module.samtools.faidx.get_messages(),
        }
    except Exception as exc:
        result["steps"]["samtools_error"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    else:
        result["steps"]["samtools_error"] = {"ok": False, "error": "missing file unexpectedly succeeded"}

    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import pysam
        import pysam.bcftools
        import pysam.samtools
    except Exception as exc:
        return {
            "ok": False,
            "stage": "import",
            "error": f"{type(exc).__name__}: {exc}",
            "hint": "Run from an environment with a built or installed pysam package; avoid source-checkout shadowing of compiled extensions.",
        }

    result: dict[str, Any] = {
        "ok": True,
        "pysam_version": getattr(pysam, "__version__", None),
        "samtools_version": getattr(pysam, "__samtools_version__", None),
        "bcftools_version": getattr(pysam, "__bcftools_version__", None),
        "dispatchers": {
            "samtools_faidx_type": type(pysam.samtools.faidx).__name__,
            "samtools_cram_size_dispatch": getattr(pysam.samtools.cram_size, "dispatch", None),
            "samtools_fqimport_dispatch": getattr(pysam.samtools.fqimport, "dispatch", None),
            "top_level_faidx_type": type(pysam.faidx).__name__,
            "bcftools_view_type": type(pysam.bcftools.view).__name__,
        },
        "usage": {
            "samtools_faidx": summarize_usage(pysam.samtools.faidx),
            "samtools_sort": summarize_usage(pysam.samtools.sort),
            "bcftools_view": summarize_usage(pysam.bcftools.view),
        },
    }

    if args.skip_tiny_flow:
        result["tiny_flow_skipped"] = True
        return result

    temp_dir = None
    if args.outdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="pysam-command-wrapper-smoke-")
        outdir = Path(temp_dir.name)
    else:
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        result["tiny_flow"] = run_tiny_flow(pysam, outdir)
        result["tiny_flow_ok"] = all(step.get("ok") for step in result["tiny_flow"]["steps"].values())
    finally:
        if temp_dir is not None and not args.keep:
            result["temporary_directory_removed"] = True
            temp_dir.cleanup()
        elif temp_dir is not None:
            result["temporary_directory_removed"] = False

    return result


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print(json.dumps(run(args), sort_keys=True))


if __name__ == "__main__":
    main()
