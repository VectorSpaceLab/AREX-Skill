#!/usr/bin/env python3
"""Safe CLI smoke checks for installed Astropy console entry points.

By default this script checks ``--help`` for public Astropy commands. With
``--with-fixtures`` it also creates temporary FITS/ECSV files and exercises a
small read-only subset. It never writes outside a temporary directory unless the
caller supplies one explicitly.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(argv: list[str], timeout: int) -> dict[str, object]:
    proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
    return {
        "command": argv,
        "returncode": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
    }


def command_path(command: str) -> str:
    found = shutil.which(command)
    if not found:
        raise RuntimeError(f"command not found on PATH: {command}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Astropy CLI smoke checks.")
    parser.add_argument("--with-fixtures", action="store_true", help="Create tiny temp FITS/ECSV fixtures for read-only command checks.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout per command in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON results.")
    args = parser.parse_args()

    commands = [
        "fitsinfo",
        "fitsheader",
        "fitscheck",
        "fitsdiff",
        "fits2bitmap",
        "showtable-astropy",
        "volint",
        "wcslint",
        "samp_hub",
    ]
    results: list[dict[str, object]] = []

    for command in commands:
        path = command_path(command)
        result = run_command([path, "--help"], args.timeout)
        results.append(result)
        if result["returncode"] != 0:
            raise SystemExit(f"{command} --help failed: {result}")

    if args.with_fixtures:
        import numpy as np
        from astropy import units as u
        from astropy.io import fits
        from astropy.table import QTable

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fits_path = tmp / "tiny.fits"
            fits.PrimaryHDU(np.arange(4, dtype=np.float32).reshape(2, 2)).writeto(fits_path)
            table_path = tmp / "tiny.ecsv"
            QTable({"wave": [500, 600] * u.nm, "flux": [1.2, 2.3] * u.Jy}).write(table_path, format="ascii.ecsv")

            fixture_commands = [
                [command_path("fitsinfo"), str(fits_path)],
                [command_path("fitsheader"), str(fits_path)],
                [command_path("fitsdiff"), str(fits_path), str(fits_path)],
                [command_path("showtable-astropy"), str(table_path), "--format", "ascii.ecsv", "--max-lines", "5"],
            ]
            for argv in fixture_commands:
                result = run_command(argv, args.timeout)
                results.append(result)
                if result["returncode"] != 0:
                    raise SystemExit(f"fixture command failed: {result}")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"ok rc={result['returncode']}: {' '.join(result['command'])}")
        print("astropy cli smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
