#!/usr/bin/env python3
"""Preview AlphaGPT data-pipeline SQL schema without network or database access.

This helper is deterministic and uses only the Python standard library. It does
not import AlphaGPT modules, read environment variables, open sockets, or connect
to Postgres. Use it to review the `tokens` and `ohlcv` DDL before authorizing a
live pipeline run.

Examples:
    python alpha_gpt_schema_preview.py --format text
    python alpha_gpt_schema_preview.py --format sql --output alphagpt_schema.sql
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

TOKENS_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS tokens (
        address TEXT PRIMARY KEY,
        symbol TEXT,
        name TEXT,
        decimals INT,
        chain TEXT,
        last_updated TIMESTAMP DEFAULT NOW()
    );
    """
).strip()

OHLCV_DDL = dedent(
    """
    CREATE TABLE IF NOT EXISTS ohlcv (
        time TIMESTAMP NOT NULL,
        address TEXT NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume DOUBLE PRECISION,
        liquidity DOUBLE PRECISION,
        fdv DOUBLE PRECISION,
        source TEXT,
        PRIMARY KEY (time, address)
    );
    """
).strip()

HYPERTABLE_SQL = "SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);"
INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_ohlcv_address ON ohlcv (address);"

SQL_BLOCK = "\n\n".join([TOKENS_DDL, OHLCV_DDL, HYPERTABLE_SQL, INDEX_SQL]) + "\n"

TEXT_BLOCK = f"""AlphaGPT data-pipeline schema preview
=====================================

Safety: this script performs no network calls and opens no database connection.

Tables created by DBManager.init_schema:

1. tokens
   - address TEXT PRIMARY KEY
   - symbol TEXT
   - name TEXT
   - decimals INT
   - chain TEXT
   - last_updated TIMESTAMP DEFAULT NOW()

2. ohlcv
   - time TIMESTAMP NOT NULL
   - address TEXT NOT NULL
   - open/high/low/close DOUBLE PRECISION
   - volume DOUBLE PRECISION
   - liquidity DOUBLE PRECISION
   - fdv DOUBLE PRECISION
   - source TEXT
   - PRIMARY KEY (time, address)

Post-table actions:
   - Attempt TimescaleDB hypertable conversion for ohlcv on the time column.
   - Create idx_ohlcv_address on ohlcv(address).

SQL DDL:

{SQL_BLOCK}"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print AlphaGPT tokens/ohlcv schema DDL without importing the repo, "
            "contacting providers, or connecting to Postgres."
        )
    )
    parser.add_argument(
        "--format",
        choices=("text", "sql"),
        default="text",
        help="Output format: annotated text for humans or raw SQL DDL.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file to write. Parent directories must already exist.",
    )
    return parser


def render(format_name: str) -> str:
    if format_name == "sql":
        return SQL_BLOCK
    if format_name == "text":
        return TEXT_BLOCK
    raise ValueError(f"unsupported format: {format_name}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    content = render(args.format)

    if args.output is None:
        sys.stdout.write(content)
    else:
        args.output.write_text(content, encoding="utf-8")
        print(f"Wrote AlphaGPT schema preview to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
