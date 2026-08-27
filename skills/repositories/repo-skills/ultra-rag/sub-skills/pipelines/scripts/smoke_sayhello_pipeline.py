#!/usr/bin/env python3
"""Run a tiny UltraRAG pipeline smoke check.

This helper writes a temporary pipeline that points at the checkout's
`servers/sayhello` server, then runs `ultrarag build` and `ultrarag run`.

Usage:
  python smoke_sayhello_pipeline.py --repo-root /path/to/UltraRAG
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CLI_CODE = """
from ultrarag.client import main
import sys
sys.argv = ['ultrarag', *sys.argv[1:]]
main()
"""


def _run_ultrarag(
    args: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-c", CLI_CODE, *args]
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _make_temp_root(keep_temp: bool) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if keep_temp:
        return Path(tempfile.mkdtemp(prefix="ultrarag-sayhello-")), None
    ctx = tempfile.TemporaryDirectory(prefix="ultrarag-sayhello-")
    return Path(ctx.name), ctx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the UltraRAG checkout that contains servers/sayhello.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary pipeline directory after the smoke check.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    sayhello_dir = repo_root / "servers" / "sayhello"
    sayhello_py = sayhello_dir / "src" / "sayhello.py"
    parameter_yaml = sayhello_dir / "parameter.yaml"

    if not sayhello_py.exists():
        print(f"Missing sayhello server: {sayhello_py}", file=sys.stderr)
        return 2
    if not parameter_yaml.exists():
        print(f"Missing sayhello parameter file: {parameter_yaml}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env_bin = str(Path(sys.executable).resolve().parent)
    env["PATH"] = env_bin + os.pathsep + env.get("PATH", "")
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )

    temp_root, temp_ctx = _make_temp_root(args.keep_temp)
    try:
        pipeline_file = temp_root / "sayhello_smoke.yaml"
        pipeline_file.write_text(
            "\n".join(
                [
                    "servers:",
                    f"  sayhello: {sayhello_dir}",
                    "pipeline:",
                    "  - sayhello.greet",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        build = _run_ultrarag(["build", str(pipeline_file)], cwd=temp_root, env=env)
        print(build.stdout, end="")
        print(build.stderr, end="", file=sys.stderr)
        if build.returncode != 0:
            return build.returncode

        run = _run_ultrarag(["run", str(pipeline_file)], cwd=temp_root, env=env)
        print(run.stdout, end="")
        print(run.stderr, end="", file=sys.stderr)
        if run.returncode != 0:
            return run.returncode

        combined = run.stdout + run.stderr
        if "Hello, UltraRAG" not in combined or "v3!" not in combined:
            print(
                "Expected greeting fragments not found in output: "
                "'Hello, UltraRAG' and 'v3!'",
                file=sys.stderr,
            )
            return 3

        print(f"Smoke check passed for {pipeline_file}")
        if args.keep_temp:
            print(f"Temporary files kept at {temp_root}")
        return 0
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()
        elif not args.keep_temp and temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
