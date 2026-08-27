#!/usr/bin/env python3
"""Safe no-network smoke for Headroom's Python compression API.

The default smoke uses `optimize=False` so it never downloads models or calls a
provider. Pass `--optimize` only when the current environment already has the
needed optional compression/runtime assets and you want to exercise real
compression.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass


@dataclass
class SmokeReport:
    ok: bool
    optimized: bool
    tokens_before: int
    tokens_after: int
    tokens_saved: int
    transforms_applied: list[str]
    error: str | None = None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe Headroom compress() smoke.")
    parser.add_argument("--optimize", action="store_true", help="Run real compression instead of passthrough smoke.")
    parser.add_argument("--target-ratio", type=float, default=None, help="Optional CompressConfig target_ratio.")
    parser.add_argument("--min-tokens", type=int, default=250, help="CompressConfig min_tokens_to_compress.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def run_smoke(args: argparse.Namespace) -> SmokeReport:
    try:
        from headroom import CompressConfig, compress

        rows = [
            {"id": i, "status": "ok", "message": "normal background record"}
            for i in range(80)
        ]
        rows[17] = {
            "id": 17,
            "status": "ERROR",
            "message": "payment-db connection refused",
            "trace_id": "trace-payment-001",
        }
        messages = [
            {"role": "user", "content": "Find production payment errors."},
            {"role": "tool", "content": json.dumps({"rows": rows}, indent=2)},
        ]
        cfg = CompressConfig(
            target_ratio=args.target_ratio,
            min_tokens_to_compress=args.min_tokens,
            protect_recent=0 if args.optimize else 4,
        )
        result = compress(messages, optimize=args.optimize, config=cfg, model="gpt-4o")
        return SmokeReport(
            ok=True,
            optimized=bool(args.optimize),
            tokens_before=result.tokens_before,
            tokens_after=result.tokens_after,
            tokens_saved=result.tokens_saved,
            transforms_applied=list(result.transforms_applied),
        )
    except Exception as exc:  # noqa: BLE001 - report cleanly for diagnostics
        return SmokeReport(
            ok=False,
            optimized=bool(args.optimize),
            tokens_before=0,
            tokens_after=0,
            tokens_saved=0,
            transforms_applied=[],
            error=f"{type(exc).__name__}: {exc}",
        )


def print_text(report: SmokeReport) -> None:
    print("Headroom compress smoke")
    print(f"optimized: {report.optimized}")
    print(f"ok: {report.ok}")
    if report.error:
        print(f"error: {report.error}")
    print(f"tokens: {report.tokens_before} -> {report.tokens_after} (saved {report.tokens_saved})")
    print(f"transforms: {', '.join(report.transforms_applied) or 'none'}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = run_smoke(args)
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
