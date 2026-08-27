"""Render a skill-local provider coverage summary.

This helper is deliberately safe by default:
- no network calls
- no credential access
- no writes unless --output is supplied

It reads the verified inventory from provider_inventory.py and renders a compact
coverage summary that future agents can paste into the generated skill tree.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from provider_inventory import EXPECTED_PROVIDER_COUNT, PROVIDER_INVENTORY, ProviderRecord, validate_provider_count


def _coverage_token(record: ProviderRecord) -> str:
    counts = record.coverage_counts
    return f"{counts['timeseries']}/{counts['workout_fields']}/{counts['sleep_fields']}/{counts['menstrual_cycle_fields']}/{counts['health_scores']}"


def render_summary() -> str:
    lines = [
        "# Provider Coverage Summary",
        "",
        f"Verified provider count: {len(PROVIDER_INVENTORY)}",
        "",
        "| Provider | Strategy | Capabilities | Coverage (ts/wo/sl/mc/hs) | Notes |",
        "|---|---|---|---|---|",
    ]
    for record in PROVIDER_INVENTORY:
        capabilities = ", ".join(f"`{flag}`" for flag in record.capabilities) or "—"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record.provider}`",
                    f"`{record.strategy}`",
                    capabilities,
                    _coverage_token(record),
                    record.notes or "—",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Sync and delivery notes",
            "",
            "- `PULL` is the default live-sync mode for every REST-backed provider.",
            "- `None` is the default for SDK/file-import-only providers.",
            "- `WEBHOOK` is the default for Garmin-style push/backfill providers.",
            "- This helper does not call provider APIs or require credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the provider coverage summary used by the provider-integrations skill.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to write. If omitted, the summary is printed to stdout.",
    )
    parser.add_argument(
        "--check",
        type=Path,
        help="Compare the generated summary against an existing file and exit non-zero on drift.",
    )
    parser.add_argument(
        "--check-count",
        action="store_true",
        help="Exit non-zero unless the verified provider count still matches the expected inventory.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=EXPECTED_PROVIDER_COUNT,
        help="Expected provider count used by --check-count (default: 12).",
    )
    return parser.parse_args(argv)


def _write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.check_count:
        validate_provider_count(args.expected_count)

    summary = render_summary()

    if args.check and args.output:
        raise SystemExit("Use only one of --output or --check.")

    if args.check:
        current = args.check.read_text()
        if current != summary:
            raise SystemExit(f"Coverage summary drift detected in {args.check}")
        return 0

    if args.output:
        _write_output(args.output, summary)
        return 0

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
