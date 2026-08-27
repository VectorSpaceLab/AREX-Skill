#!/usr/bin/env python3
"""Safely check optional Biotite application wrapper imports and binaries.

This diagnostic performs no network requests and no molecular analyses. It only
imports Biotite wrapper modules and probes executable discovery/version-help
commands with short timeouts.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ImportCheck:
    module: str
    status: str
    detail: str | None = None


@dataclass(frozen=True)
class ExecutableCheck:
    name: str
    purpose: str
    executable: str
    status: str
    path: str | None = None
    probe: str | None = None
    detail: str | None = None


MODULES = [
    "biotite",
    "biotite.database.rcsb",
    "biotite.database.entrez",
    "biotite.database.uniprot",
    "biotite.database.pubchem",
    "biotite.database.afdb",
    "biotite.application",
    "biotite.application.blast",
    "biotite.application.clustalo",
    "biotite.application.mafft",
    "biotite.application.muscle",
    "biotite.application.dssp",
    "biotite.application.sra",
    "biotite.application.tantan",
    "biotite.application.autodock",
    "biotite.application.viennarna",
]

EXECUTABLES = [
    ("blastp", "NCBI BLAST protein executable", ["-version"]),
    ("blastn", "NCBI BLAST nucleotide executable", ["-version"]),
    ("clustalo", "Clustal Omega MSA wrapper", ["--version"]),
    ("mafft", "MAFFT MSA wrapper", ["--version"]),
    ("muscle", "MUSCLE 3 or 5 MSA wrapper", ["-version"]),
    ("mkdssp", "DSSP secondary-structure wrapper", ["--version"]),
    ("vina", "AutoDock Vina docking wrapper", ["--version"]),
    ("prefetch", "SRA prefetch helper", ["--version"]),
    ("fasterq-dump", "SRA FASTQ/FASTA dump helper", ["--version"]),
    ("tantan", "Tantan repeat masking wrapper", ["--version"]),
    ("RNAfold", "ViennaRNA single-sequence folding wrapper", ["--version"]),
    ("RNAplot", "ViennaRNA RNA plot coordinate wrapper", ["--version"]),
    ("RNAalifold", "ViennaRNA consensus folding wrapper", ["--version"]),
]


def check_imports(modules: Iterable[str]) -> list[ImportCheck]:
    checks = []
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure
            checks.append(ImportCheck(module_name, "failed", f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(ImportCheck(module_name, "ok"))
    return checks


def _summarize_output(process: subprocess.CompletedProcess[str]) -> str:
    text = (process.stdout or process.stderr or "").strip().replace("\n", " | ")
    if len(text) > 240:
        return text[:237] + "..."
    return text


def check_executable(
    executable: str,
    purpose: str,
    probe_args: list[str],
    timeout: float,
) -> ExecutableCheck:
    path = shutil.which(executable)
    if path is None:
        return ExecutableCheck(executable, purpose, executable, "missing")

    try:
        process = subprocess.run(
            [path, *probe_args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ExecutableCheck(
            executable,
            purpose,
            executable,
            "found-version-probe-timeout",
            path=path,
            probe=" ".join([executable, *probe_args]),
            detail=f"probe exceeded {timeout:g}s",
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic should report any probe failure
        return ExecutableCheck(
            executable,
            purpose,
            executable,
            "found-version-probe-failed",
            path=path,
            probe=" ".join([executable, *probe_args]),
            detail=f"{type(exc).__name__}: {exc}",
        )

    detail = _summarize_output(process) or f"exit code {process.returncode}"
    status = "found" if process.returncode == 0 else "found-version-probe-failed"
    return ExecutableCheck(
        executable,
        purpose,
        executable,
        status,
        path=path,
        probe=" ".join([executable, *probe_args]),
        detail=detail,
    )


def check_executables(timeout: float) -> list[ExecutableCheck]:
    return [
        check_executable(executable, purpose, probe_args, timeout)
        for executable, purpose, probe_args in EXECUTABLES
    ]


def print_text(imports: list[ImportCheck], executables: list[ExecutableCheck]) -> None:
    print("Biotite optional database/application diagnostic")
    print("No network requests or analyses were run.\n")

    print("Wrapper imports:")
    for check in imports:
        suffix = f" ({check.detail})" if check.detail else ""
        print(f"  {check.status:6} {check.module}{suffix}")

    print("\nExternal executables:")
    for check in executables:
        location = check.path if check.path is not None else "not on PATH"
        detail = f"; {check.detail}" if check.detail else ""
        print(f"  {check.status:28} {check.name:12} {location}{detail}")

    missing = [check.name for check in executables if check.status == "missing"]
    if missing:
        print("\nMissing executables:")
        print("  " + ", ".join(missing))
        print("Install the relevant external tool or pass an explicit bin_path to the wrapper.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Biotite database/application wrapper imports and optional "
            "external executable availability without network or analyses."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="seconds allowed for each executable version/help probe",
    )
    args = parser.parse_args()

    imports = check_imports(MODULES)
    executables = check_executables(args.timeout)

    if args.json:
        print(
            json.dumps(
                {
                    "note": "No network requests or analyses were run.",
                    "imports": [asdict(check) for check in imports],
                    "executables": [asdict(check) for check in executables],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(imports, executables)

    import_failures = any(check.status == "failed" for check in imports)
    missing_executables = any(check.status == "missing" for check in executables)
    return 2 if import_failures else 1 if missing_executables else 0


if __name__ == "__main__":
    sys.exit(main())
