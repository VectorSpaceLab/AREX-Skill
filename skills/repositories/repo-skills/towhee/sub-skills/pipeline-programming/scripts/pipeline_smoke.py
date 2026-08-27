#!/usr/bin/env python3
"""Safe local Towhee pipeline smoke check.

This script intentionally uses only lambda/callable pipeline nodes. It does not
load Hub operators, models, Triton, Docker, or network resources.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from typing import Any, Tuple


def _err(message: str, code: int = 1) -> int:
    print(f"[pipeline-smoke] ERROR: {message}", file=sys.stderr)
    return code


def _import_towhee(verbose: bool) -> Tuple[Any, Any, Any] | None:
    try:
        import towhee  # pylint: disable=import-outside-toplevel
        from towhee import AutoConfig, pipe  # pylint: disable=import-outside-toplevel
        return towhee, pipe, AutoConfig
    except Exception as exc:  # pragma: no cover - exercised in missing-env checks
        if verbose:
            traceback.print_exc()
        print(
            "[pipeline-smoke] ERROR: Towhee import failed. Install Towhee and "
            "its required runtime dependencies in the active Python environment "
            "(Towhee 1.1.x also imports pkg_resources from setuptools). "
            f"Original error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None


def _build_pipeline(pipe: Any) -> Any:
    return (
        pipe.input('x')
            .map('x', 'double', lambda x: x * 2)
            .map('double', 'label', lambda value: f'value={value}')
            .output('double', 'label')
    )


def run(verbose: bool = False) -> int:
    imported = _import_towhee(verbose)
    if imported is None:
        return 2

    towhee, pipe, AutoConfig = imported
    if verbose:
        version = getattr(towhee, '__version__', 'unknown')
        print(f"[pipeline-smoke] Imported towhee version: {version}")

    try:
        pipeline = _build_pipeline(pipe)

        single = pipeline(3).get()
        if single != [6, 'value=6']:
            return _err(f"single call returned {single!r}; expected [6, 'value=6']")
        if verbose:
            print(f"[pipeline-smoke] Single call OK: {single!r}")

        batch_rows = pipeline.batch([0, 5, -2])
        batch = [row.get() for row in batch_rows]
        expected_batch = [[0, 'value=0'], [10, 'value=10'], [-4, 'value=-4']]
        if batch != expected_batch:
            return _err(f"batch returned {batch!r}; expected {expected_batch!r}")
        if verbose:
            print(f"[pipeline-smoke] Batch call OK: {batch!r}")

        debug_viz = pipeline.debug(4, profiler=True, tracer=True, include='lambda')
        debug_result = debug_viz.result.get()
        if debug_result != [8, 'value=8']:
            return _err(f"debug result returned {debug_result!r}; expected [8, 'value=8']")
        profiler = debug_viz.profiler
        tracer = debug_viz.tracer
        if profiler is None or len(profiler) != 1:
            return _err("debug profiler was not created for the single debug run")
        if tracer is None or len(tracer) != 1 or not tracer.nodes:
            return _err("debug tracer was not created or traced no nodes")
        if verbose:
            print(f"[pipeline-smoke] Debug profiler/tracer OK: traced nodes={tracer.nodes!r}")

        cpu_config = AutoConfig.LocalCPUConfig()
        if getattr(cpu_config, 'config', None) != {'device': -1}:
            return _err(f"LocalCPUConfig returned {getattr(cpu_config, 'config', None)!r}; expected {{'device': -1}}")
        if verbose:
            print(f"[pipeline-smoke] AutoConfig.LocalCPUConfig OK: {cpu_config.config!r}")

    except Exception as exc:  # pragma: no cover - environment/runtime dependent
        if verbose:
            traceback.print_exc()
        return _err(f"pipeline smoke failed: {type(exc).__name__}: {exc}")

    if verbose:
        print("[pipeline-smoke] All checks passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe local Towhee lambda-pipeline smoke check.")
    parser.add_argument('--verbose', action='store_true', help='Print successful checkpoints and import tracebacks.')
    args = parser.parse_args(argv)
    return run(verbose=args.verbose)


if __name__ == '__main__':
    raise SystemExit(main())
