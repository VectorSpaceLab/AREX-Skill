from __future__ import annotations

import argparse
import json
from pathlib import Path

from mlx_audio.stt.eval.wer import aggregate_wer, compute_wer


def _read_lines(path: str | Path) -> list[str]:
    return [line.rstrip("\n") for line in Path(path).read_text(encoding="utf-8").splitlines()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize one or more WER pairs")
    parser.add_argument("--reference")
    parser.add_argument("--hypothesis")
    parser.add_argument("--reference-file")
    parser.add_argument("--hypothesis-file")
    parser.add_argument("--json", action="store_true", help="Kept for compatibility; output is always JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.reference_file or args.hypothesis_file:
        if not args.reference_file or not args.hypothesis_file:
            raise SystemExit("--reference-file and --hypothesis-file must be paired")
        refs = _read_lines(args.reference_file)
        hyps = _read_lines(args.hypothesis_file)
        if len(refs) != len(hyps):
            raise SystemExit("reference and hypothesis files must have the same number of lines")
        results = [compute_wer(r, h) for r, h in zip(refs, hyps)]
        payload = aggregate_wer(results)
        payload["num_pairs"] = len(results)
    else:
        if args.reference is None or args.hypothesis is None:
            raise SystemExit("provide either --reference/--hypothesis or the file pair")
        result = compute_wer(args.reference, args.hypothesis)
        payload = result.to_dict()

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
