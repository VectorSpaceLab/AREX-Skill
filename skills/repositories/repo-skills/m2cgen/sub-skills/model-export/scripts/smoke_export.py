#!/usr/bin/env python3
"""Smoke-check m2cgen export APIs with a tiny deterministic fitted model.

The default path creates a local LinearRegression model, asks every public
exporter for source, and executes only the generated Python source. Other
target outputs are checked only for a source-shape marker; no foreign runtime,
compiler, user model, or repository e2e fixture is exercised.

Execution boundary: ``exec`` receives only Python emitted by the installed
``m2cgen`` package for the model this script creates. It is not a sandbox and
must not be repurposed to execute untrusted generated source, models, or an
untrusted/modified exporter.

The default path neither spawns a subprocess nor creates serialized files.
``--cli`` invokes ``sys.executable -m m2cgen`` without a shell and supplies a
pickle created in memory by this script. It creates an ``m2cgen-smoke-*``
TemporaryDirectory only for that CLI work; the context manager removes it on
exit, including check failures. ``--joblib`` and ``--console-script`` run only
with ``--cli``. The latter resolves ``m2cgen`` through PATH and therefore
should be used only with a trusted PATH.
"""

from __future__ import annotations

import argparse
import math
import pickle
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple


def _import_dependencies():
    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing required dependency 'numpy'. Install m2cgen's base dependency first."
        ) from exc

    try:
        import m2cgen as m2c  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing required package 'm2cgen'. Install m2cgen before running this smoke check."
        ) from exc

    try:
        from sklearn.linear_model import LinearRegression  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing optional dependency 'scikit-learn'. Install scikit-learn to build the tiny fitted "
            "LinearRegression model used by this smoke check."
        ) from exc

    return np, m2c, LinearRegression


def _fit_tiny_model():
    np, _m2c, LinearRegression = _import_dependencies()
    x = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [2.0, -1.0],
        ],
        dtype=float,
    )
    y = 1.0 + 2.0 * x[:, 0] - 3.0 * x[:, 1]
    return LinearRegression().fit(x, y), np.array([1.5, -2.0], dtype=float)


def _validate_python_export(code: str, sample, expected: float) -> None:
    namespace: Dict[str, object] = {}
    exec(code, namespace)  # noqa: S102 - deterministic generated Python from local fitted linear model.
    score = namespace.get("score")
    if not callable(score):
        raise RuntimeError("Python export did not define a callable score(input) function.")
    actual = float(score(sample.tolist()))
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9):
        raise RuntimeError(f"Generated Python score mismatch: expected {expected!r}, got {actual!r}.")


def _exercise_api(model, sample) -> Tuple[int, int]:
    _np, m2c, _LinearRegression = _import_dependencies()
    expected = float(model.predict([sample])[0])

    exporters: Tuple[Tuple[str, Callable[..., str], str], ...] = (
        ("export_to_java", m2c.export_to_java, "class Model"),
        ("export_to_python", m2c.export_to_python, "def score"),
        ("export_to_c", m2c.export_to_c, "double score"),
        ("export_to_go", m2c.export_to_go, "func score"),
        ("export_to_javascript", m2c.export_to_javascript, "function score"),
        ("export_to_visual_basic", m2c.export_to_visual_basic, "Function Score"),
        ("export_to_c_sharp", m2c.export_to_c_sharp, "class Model"),
        ("export_to_powershell", m2c.export_to_powershell, "function Score"),
        ("export_to_r", m2c.export_to_r, "score <- function"),
        ("export_to_php", m2c.export_to_php, "function score"),
        ("export_to_dart", m2c.export_to_dart, "double score"),
        ("export_to_haskell", m2c.export_to_haskell, "score ::"),
        ("export_to_ruby", m2c.export_to_ruby, "def score"),
        ("export_to_f_sharp", m2c.export_to_f_sharp, "let score"),
        ("export_to_rust", m2c.export_to_rust, "fn score"),
        ("export_to_elixir", m2c.export_to_elixir, "def score"),
    )

    for name, exporter, needle in exporters:
        code = exporter(model)
        if not isinstance(code, str) or needle not in code:
            raise RuntimeError(f"{name} returned unexpected code; missing {needle!r}.")
        if name == "export_to_python":
            _validate_python_export(code, sample, expected)

    return len(exporters), 1


def _run_command(cmd, *, input_bytes: Optional[bytes] = None) -> str:
    proc = subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{stderr}")
    return proc.stdout.decode("utf-8", errors="replace")


def _exercise_cli(model, *, use_joblib: bool, use_console_script: bool) -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="m2cgen-smoke-") as td:
        tmpdir = Path(td)
        pickle_path = tmpdir / "tiny-model.pkl"
        pickle_bytes = pickle.dumps(model)
        pickle_path.write_bytes(pickle_bytes)

        file_out = _run_command([sys.executable, "-m", "m2cgen", "--language", "python", str(pickle_path)])
        if "def score" not in file_out:
            raise RuntimeError("python -m m2cgen file export did not produce a score function.")
        checks += 1

        stdin_out = _run_command([sys.executable, "-m", "m2cgen", "--language", "python"], input_bytes=pickle_bytes)
        if "def score" not in stdin_out:
            raise RuntimeError("python -m m2cgen stdin export did not produce a score function.")
        checks += 1

        if use_joblib:
            try:
                import joblib  # type: ignore
            except ModuleNotFoundError as exc:
                raise RuntimeError("Missing optional dependency 'joblib'; install it or omit --joblib.") from exc
            joblib_path = tmpdir / "tiny-model.joblib"
            joblib.dump(model, joblib_path)
            joblib_out = _run_command(
                [sys.executable, "-m", "m2cgen", "--language", "go", "--pickle-lib", "joblib", str(joblib_path)]
            )
            if "func score" not in joblib_out:
                raise RuntimeError("joblib CLI export did not produce a Go score function.")
            checks += 1

        if use_console_script:
            exe = shutil.which("m2cgen")
            if exe is None:
                raise RuntimeError(
                    "Console script 'm2cgen' was requested but is not on PATH. Use 'python -m m2cgen' or fix the "
                    "environment's console-script installation."
                )
            console_out = _run_command([exe, "--language", "python", str(pickle_path)])
            if "def score" not in console_out:
                raise RuntimeError("m2cgen console-script export did not produce a score function.")
            checks += 1

    return checks


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-check m2cgen public export APIs (narrow, local-model check).")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Also run python -m m2cgen file and stdin roundtrips (creates a temporary directory).",
    )
    parser.add_argument(
        "--joblib",
        action="store_true",
        help="With --cli, also test --pickle-lib joblib (optional dependency; requires --cli).",
    )
    parser.add_argument(
        "--console-script",
        action="store_true",
        help="With --cli, also test the installed m2cgen console script from PATH (requires --cli).",
    )
    args = parser.parse_args(argv)
    if (args.joblib or args.console_script) and not args.cli:
        parser.error("--joblib and --console-script require --cli; no optional CLI path was run.")

    try:
        model, sample = _fit_tiny_model()
        api_count, python_validation_count = _exercise_api(model, sample)
        cli_count = (
            _exercise_cli(model, use_joblib=args.joblib, use_console_script=args.console_script)
            if args.cli
            else 0
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep the default user experience helpful instead of a raw traceback.
        print(f"ERROR: unexpected smoke-check failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(
        "m2cgen smoke export ok: "
        f"api_exports={api_count}, python_validation={python_validation_count}, cli_checks={cli_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
