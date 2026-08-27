#!/usr/bin/env python3
"""Probe safe MNE-Python CLI help/version and optional no-download datasets.

The default probes avoid analysis, file writes, GUI launch, and dataset downloads.
Run from any directory with the intended MNE-Python environment active.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_COMMANDS = ("sys_info", "what", "show_info", "show_fiff", "report")


def _base_mne_command(mne_bin: str | None) -> list[str]:
    if mne_bin:
        return [mne_bin]
    if shutil.which("mne"):
        return ["mne"]
    shim = (
        "import sys; "
        "from mne.commands.utils import main; "
        "sys.argv = ['mne'] + sys.argv[1:]; "
        "main()"
    )
    return [sys.executable, "-c", shim]


def _display_argv(argv: list[str]) -> str:
    display = list(argv)
    if display and Path(display[0]).resolve() == Path(sys.executable).resolve():
        display[0] = "python"
    return " ".join(display)


def _run_probe(label: str, argv: list[str], timeout: float, env: dict[str, str]) -> bool:
    print(f"\n## {label}")
    print("$ " + _display_argv(argv))
    proc = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    print(f"exit_code={proc.returncode}")
    if proc.stdout:
        print("-- stdout --")
        print(proc.stdout.rstrip())
    if proc.stderr:
        print("-- stderr --")
        print(proc.stderr.rstrip())
    return proc.returncode == 0


def _dataset_checks(names: list[str], dataset_path: Path | None) -> bool:
    if not names:
        return True

    import importlib

    try:
        import mne

        mne.set_log_level("WARNING")
    except Exception:
        pass

    ok = True
    temp_dir_cm = None
    if dataset_path is None:
        temp_dir_cm = tempfile.TemporaryDirectory(prefix="mne-dataset-probe-")
        root = Path(temp_dir_cm.name)
        root_note = "temporary empty root (pass --dataset-path to check a real cache)"
    else:
        root = dataset_path.expanduser().resolve()
        root_note = str(root)

    print("\n## no-download dataset checks")
    print(f"dataset_root={root_note}")
    try:
        for name in names:
            try:
                module = importlib.import_module(f"mne.datasets.{name}")
                data_path = getattr(module, "data_path")
            except Exception as exc:  # noqa: BLE001 - report import/signature failures
                ok = False
                print(f"{name}: import_error {type(exc).__name__}: {exc}")
                continue
            try:
                path = data_path(path=root, download=False, update_path=False)
            except TypeError as exc:
                ok = False
                print(f"{name}: unsupported_generic_data_path_signature: {exc}")
                continue
            except Exception as exc:  # noqa: BLE001 - probe should report all failures
                ok = False
                print(f"{name}: error {type(exc).__name__}: {exc}")
                continue
            available = str(path) not in ("", ".")
            status = "present" if available else "missing-no-download"
            print(f"{name}: {status}: {path}")
    finally:
        if temp_dir_cm is not None:
            temp_dir_cm.cleanup()
    return ok


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe MNE-Python CLI help/version probes and optional "
            "dataset data_path(download=False) checks."
        )
    )
    parser.add_argument(
        "--commands",
        nargs="*",
        default=list(DEFAULT_COMMANDS),
        help="MNE command names whose --help output should be probed.",
    )
    parser.add_argument(
        "--mne-bin",
        default=None,
        help="Path/name of the mne console script. Defaults to PATH, then a Python shim.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for each CLI subprocess.",
    )
    parser.add_argument(
        "--run-sys-info",
        action="store_true",
        help="Also run mne sys_info --no-check-version --ascii, not just help.",
    )
    parser.add_argument(
        "--dataset-check",
        nargs="*",
        default=[],
        metavar="NAME",
        help=(
            "Dataset module names to check with data_path(download=False, "
            "update_path=False). Examples: sample testing misc."
        ),
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=None,
        help=(
            "Root directory to use for dataset checks. If omitted, a temporary "
            "empty root is used so the probe does not touch user data config."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero if any CLI probe or dataset import/check fails.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("MNE_LOGGING_LEVEL", "WARNING")
    env.setdefault("MNE_DONTWRITE_HOME", "true")

    base = _base_mne_command(args.mne_bin)
    probes: list[tuple[str, list[str]]] = [
        ("mne --help", base + ["--help"]),
        ("mne --version", base + ["--version"]),
        ("mne sys_info --help", base + ["sys_info", "--help"]),
    ]
    if args.run_sys_info:
        probes.append(
            (
                "mne sys_info --no-check-version --ascii",
                base + ["sys_info", "--no-check-version", "--ascii"],
            )
        )
    for command in args.commands:
        if command == "sys_info":
            continue
        probes.append((f"mne {command} --help", base + [command, "--help"]))

    ok = True
    for label, command_argv in probes:
        try:
            ok = _run_probe(label, command_argv, args.timeout, env) and ok
        except subprocess.TimeoutExpired:
            ok = False
            print(f"\n## {label}\nTIMEOUT after {args.timeout} seconds")

    ok = _dataset_checks(args.dataset_check, args.dataset_path) and ok
    if args.strict and not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
