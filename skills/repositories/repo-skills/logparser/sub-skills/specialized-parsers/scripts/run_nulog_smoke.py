#!/usr/bin/env python
"""Run a tiny NuLog smoke.

NuLog is sensitive to NumPy/Pandas compatibility and expects `outdir` to end
with a slash. This helper uses a tiny fixture and conservative model settings.

Example:
    python scripts/run_nulog_smoke.py
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import sys



def _bootstrap_repo_root() -> None:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "setup.py").exists() and (candidate / "logparser").is_dir():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not locate the repository root for Logparser")

_bootstrap_repo_root()

from logparser.NuLog import LogParser

DEFAULT_SAMPLE = """2026-01-01 12:00:00 INFO start service
2026-01-01 12:00:01 INFO start worker
2026-01-01 12:00:02 INFO stop worker
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, help="log file to parse; a tiny sample is used when omitted")
    parser.add_argument("--log-name", default="sample.log", help="log file name when creating a tiny sample")
    parser.add_argument("--output-dir", type=Path, default=Path("./nulog_result/"), help="output directory")
    parser.add_argument("--log-format", default="<Date> <Time> <Level> <Content>", help="NuLog log format string")
    parser.add_argument("--filters", default=r"(\s+)|(:)", help="tokenizer filters regex")
    parser.add_argument("--k", type=int, default=5, help="NuLog k parameter")
    parser.add_argument("--nr-epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--pad-len", type=int, default=16)
    parser.add_argument("--d-model", type=int, default=16)
    parser.add_argument("--N", type=int, default=1)
    parser.add_argument("--step-size", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.input_file is None:
        root = Path(tempfile.mkdtemp(prefix="logparser-nulog-"))
        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        log_name = args.log_name
        (input_dir / log_name).write_text(DEFAULT_SAMPLE, encoding="utf-8")
    else:
        input_dir = args.input_file.parent
        log_name = args.input_file.name

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outdir = str(args.output_dir)
    if not outdir.endswith("/"):
        outdir += "/"

    parser = LogParser(str(input_dir), outdir, args.filters, args.k, args.log_format)
    parser.parse(
        log_name,
        nr_epochs=args.nr_epochs,
        batch_size=args.batch_size,
        pad_len=args.pad_len,
        d_model=args.d_model,
        N=args.N,
        step_size=args.step_size,
        num_samples=0,
    )

    print(args.output_dir / f"{log_name}_structured.csv")
    print("checkpoints:", sorted(p.name for p in args.output_dir.glob(f"model_parser_{log_name}*.pt")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
