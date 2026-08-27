#!/usr/bin/env python3
"""Check a TensorFlow Datasets runtime environment safely.

The checker imports public packages, inspects optional dependency availability,
and can run the installed `tfds` CLI help/version commands. It never downloads a
dataset, launches Beam, contacts GCS intentionally, or mutates data directories.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


OPTIONAL_MODULES = {
    "tensorflow": "TensorFlow-backed tf.data loading, Keras examples, and some CLI import paths",
    "apache_beam": "Beam/Dataflow/Flink generation and convert_format Beam paths",
    "mlcroissant": "tfds build_croissant and CroissantBuilder workflows",
    "datasets": "HuggingFace community wrapper workflows",
    "pandas": "some tabular dataset builders and Croissant metadata workflows",
    "pydub": "some audio datasets; also requires ffmpeg for several workflows",
}


@dataclass
class ImportResult:
    name: str
    ok: bool
    version: str | None = None
    detail: str | None = None


def import_module(name: str) -> ImportResult:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return ImportResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(name.replace("_", "-"))
        except metadata.PackageNotFoundError:
            version = None
    return ImportResult(name=name, ok=True, version=str(version) if version is not None else None)


def run_command(cmd: list[str], timeout: float) -> dict[str, object]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "command": cmd,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
            "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
        }
    except FileNotFoundError as exc:
        return {"command": cmd, "ok": False, "error": f"not found: {exc}"}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "ok": False, "error": f"timed out after {timeout}s"}


def check_tfds_metadata() -> dict[str, object]:
    result = import_module("tensorflow_datasets")
    data: dict[str, object] = {"import": asdict(result)}
    if not result.ok:
        return data
    import tensorflow_datasets as tfds  # pylint: disable=import-outside-toplevel

    data["version"] = getattr(tfds, "__version__", None)
    try:
        data["distribution_version"] = metadata.version("tensorflow-datasets")
    except metadata.PackageNotFoundError:
        data["distribution_version"] = None
    for attr in ["load", "builder", "data_source", "as_numpy", "ReadConfig", "Split"]:
        data[f"has_{attr}"] = hasattr(tfds, attr)
    return data


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--check-cli", action="store_true", help="Also run `tfds --version` and `tfds --help`.")
    parser.add_argument("--tfds-bin", default="tfds", help="tfds executable for --check-cli.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Seconds per CLI command.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "tfds": check_tfds_metadata(),
        "optional_modules": {
            name: {**asdict(import_module(name)), "purpose": purpose}
            for name, purpose in OPTIONAL_MODULES.items()
        },
    }
    if args.check_cli:
        exe = shutil.which(args.tfds_bin) or args.tfds_bin
        report["cli"] = {
            "version": run_command([exe, "--version"], args.timeout),
            "help": run_command([exe, "--help"], args.timeout),
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        tfds_report = report["tfds"]
        tfds_import = tfds_report["import"]  # type: ignore[index]
        print(f"tensorflow_datasets import: {'OK' if tfds_import['ok'] else 'FAIL'}")
        print(f"TFDS version: {tfds_report.get('version')}")
        print("Optional modules:")
        for name, item in report["optional_modules"].items():  # type: ignore[union-attr]
            status = "OK" if item["ok"] else "MISSING"
            version = f" ({item['version']})" if item.get("version") else ""
            print(f"  - {name}: {status}{version} - {item['purpose']}")
        if args.check_cli:
            cli = report["cli"]  # type: ignore[index]
            print(f"tfds --version: {'OK' if cli['version']['ok'] else 'FAIL'}")
            print(f"tfds --help: {'OK' if cli['help']['ok'] else 'FAIL'}")

    tfds_ok = bool(report["tfds"]["import"]["ok"])  # type: ignore[index]
    cli_ok = True
    if args.check_cli:
        cli = report["cli"]  # type: ignore[index]
        cli_ok = bool(cli["version"]["ok"] and cli["help"]["ok"])
    return 0 if tfds_ok and cli_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
