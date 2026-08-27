#!/usr/bin/env python3
"""Run a safe DeepDanbooru import, dependency, and CLI-help smoke check.

This helper performs no downloads, credentials, model loads, training, or file
writes. Run it from any working directory in an environment where the package
is installed.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-cli", action="store_true", help="Skip Click CLI help checks.")
    args = parser.parse_args()
    failures = 0

    try:
        version = importlib.metadata.version("deepdanbooru")
        import deepdanbooru  # noqa: F401
        print(f"deepdanbooru distribution: {version}")
    except Exception as exc:
        print(f"ERROR: deepdanbooru import failed: {exc}", file=sys.stderr)
        failures += 1

    for module_name in ("tensorflow", "tensorflow_io", "numpy", "skimage", "click"):
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "available")
            print(f"{module_name}: {version}")
        except Exception as exc:
            print(f"ERROR: {module_name} import failed: {exc}", file=sys.stderr)
            failures += 1

    try:
        import tensorflow as tf
        print("TensorFlow GPUs visible:", len(tf.config.list_physical_devices("GPU")))
        print("GPU status is informational; this helper does not claim GPU readiness.")
    except Exception:
        pass

    if not args.no_cli:
        try:
            from click.testing import CliRunner
            import deepdanbooru.__main__ as cli
            runner = CliRunner()
            for command in (cli.main, cli.evaluate):
                result = runner.invoke(command, ["--help"])
                if result.exit_code != 0 or not result.output:
                    print(f"ERROR: CLI help failed for {command.name}", file=sys.stderr)
                    failures += 1
                else:
                    print(f"CLI help OK: {command.name}")
        except Exception as exc:
            print(f"ERROR: CLI help check failed: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"Smoke failed with {failures} issue(s).", file=sys.stderr)
        return 1
    print("Smoke OK: no network, credentials, model, or training run was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
