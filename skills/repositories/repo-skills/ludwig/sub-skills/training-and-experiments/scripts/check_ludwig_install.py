#!/usr/bin/env python3
"""Safe Ludwig training/install smoke helper.

Default mode checks import and prints the tiny train command. Use --run-tiny-train
only when a short local training run is acceptable.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Ludwig import and optionally run a tiny local train smoke.")
    parser.add_argument("--project-dir", required=True, help="Directory containing dataset.csv and config.yaml.")
    parser.add_argument("--run-tiny-train", action="store_true", help="Actually run a short ludwig train command.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")
    args = parser.parse_args()
    try:
        import ludwig
        print(f"ludwig {ludwig.__version__} imports")
    except Exception as exc:
        print(f"ERROR: cannot import ludwig: {exc}", file=sys.stderr)
        return 2
    project = Path(args.project_dir)
    cmd = [
        "ludwig", "train",
        "--config", str(project / "config.yaml"),
        "--dataset", str(project / "dataset.csv"),
        "--output_directory", str(project / "results"),
        "--skip_save_processed_input",
        "--skip_save_log",
    ]
    print(" ".join(cmd))
    if args.dry_run or not args.run_tiny_train:
        return 0
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    print(proc.stdout)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
