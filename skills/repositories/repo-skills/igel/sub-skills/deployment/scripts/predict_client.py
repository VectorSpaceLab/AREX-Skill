#!/usr/bin/env python3
"""Small, safe client for igel's FastAPI /predict endpoint.

Examples:
  python predict_client.py --host localhost --port 8080 \
    --json '{"preg": 1, "plas": 180, "pres": 50}'

  python predict_client.py --host localhost --port 8080 --json-file payload.json
  python predict_client.py --host localhost --port 8080 --csv rows_to_score.csv
  python predict_client.py --csv rows_to_score.csv --dry-run

Payload contract:
  - JSON must be an object mapping feature column names to values.
  - Use all scalars for a single row, or all equal-length lists for a batch.
  - CSV input must have a header row; it is converted to column-oriented lists.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

Payload = Dict[str, Any]


def _parse_scalar(value: str) -> Any:
    """Infer a JSON-friendly scalar from a CSV string value."""
    text = value.strip()
    lower = text.lower()
    if lower == "null" or lower == "none":
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        return value


def _non_empty_columns(payload: Payload) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("payload must be a non-empty JSON object")
    for key in payload:
        if not isinstance(key, str) or not key:
            raise ValueError("all payload keys must be non-empty feature names")


def validate_payload(payload: Payload, *, broadcast_scalars: bool = False) -> Payload:
    """Validate igel's scalar-or-equal-length-list request convention."""
    _non_empty_columns(payload)

    list_lengths = []
    for key, value in payload.items():
        if isinstance(value, list):
            if not value:
                raise ValueError(f"column {key!r} has an empty list")
            list_lengths.append(len(value))

    if not list_lengths:
        return payload

    expected = list_lengths[0]
    bad_lengths = sorted({length for length in list_lengths if length != expected})
    if bad_lengths:
        raise ValueError(
            "all list-valued columns must have the same length; "
            f"expected {expected}, also saw {bad_lengths}"
        )

    has_scalar = any(not isinstance(value, list) for value in payload.values())
    if has_scalar and not broadcast_scalars:
        raise ValueError(
            "mixed scalar/list payload detected. Use all scalars for one row, "
            "all equal-length lists for a batch, or pass --broadcast-scalars."
        )

    if has_scalar and broadcast_scalars:
        payload = {
            key: value if isinstance(value, list) else [value] * expected
            for key, value in payload.items()
        }

    return payload


def payload_from_json_text(text: str) -> Payload:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON input must be an object mapping feature names to values")
    return payload


def payload_from_json_file(path: Path) -> Payload:
    try:
        return payload_from_json_text(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read JSON file {path}: {exc}") from exc


def payload_from_csv(path: Path, *, fill_empty: Optional[str] = None) -> Payload:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV input must have a header row")

            columns = {name: [] for name in reader.fieldnames}
            row_count = 0
            for row_number, row in enumerate(reader, start=2):
                row_count += 1
                for name in reader.fieldnames:
                    raw = row.get(name, "")
                    if raw is None or raw == "":
                        if fill_empty is None:
                            raise ValueError(
                                f"empty value in column {name!r} on CSV line {row_number}; "
                                "fill it before sending or pass --fill-empty VALUE"
                            )
                        raw = fill_empty
                    columns[name].append(_parse_scalar(raw))
    except OSError as exc:
        raise ValueError(f"could not read CSV file {path}: {exc}") from exc

    if row_count == 0:
        raise ValueError("CSV input has no data rows")
    return columns


def build_url(scheme: str, host: str, port: int, path: str) -> str:
    endpoint = path if path.startswith("/") else f"/{path}"
    return f"{scheme}://{host}:{port}{endpoint}"


class IgelPredictClient:
    """Minimal stdlib HTTP client for igel's /predict endpoint."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        scheme: str = "http",
        path: str = "/predict",
        timeout: float = 30.0,
    ) -> None:
        self.url = build_url(scheme, host, port, path)
        self.timeout = timeout

    def post_payload(self, payload: Payload) -> Tuple[int, str]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return response.getcode(), text
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return exc.code, text
        except urllib.error.URLError as exc:
            raise RuntimeError(f"could not reach {self.url}: {exc}") from exc


def _choose_payload(args: argparse.Namespace) -> Payload:
    if args.json_text is not None:
        payload = payload_from_json_text(args.json_text)
    elif args.json_file is not None:
        payload = payload_from_json_file(Path(args.json_file))
    elif args.csv_file is not None:
        payload = payload_from_csv(Path(args.csv_file), fill_empty=args.fill_empty)
    else:
        raise ValueError("choose one input: --json, --json-file, or --csv")

    return validate_payload(payload, broadcast_scalars=args.broadcast_scalars)


def _print_json_or_text(text: str) -> None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        print(text)
    else:
        print(json.dumps(parsed, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format a payload and call an igel FastAPI /predict endpoint."
    )
    parser.add_argument("--scheme", default="http", help="URL scheme (default: http)")
    parser.add_argument("--host", default="localhost", help="server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="server port (default: 8080)")
    parser.add_argument("--path", default="/predict", help="endpoint path (default: /predict)")
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")
    parser.add_argument(
        "--broadcast-scalars",
        action="store_true",
        help="repeat scalar JSON values to match batch list length instead of rejecting mixed shapes",
    )
    parser.add_argument(
        "--fill-empty",
        help="value used for empty CSV cells; by default empty cells are rejected",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the validated JSON payload and do not send an HTTP request",
    )

    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--json", dest="json_text", help="inline JSON object payload")
    inputs.add_argument("--json-file", help="path to a JSON object payload file")
    inputs.add_argument("--csv", dest="csv_file", help="headered CSV file to convert to column lists")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = _choose_payload(args)
    except ValueError as exc:
        parser.error(str(exc))

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    client = IgelPredictClient(
        host=args.host,
        port=args.port,
        scheme=args.scheme,
        path=args.path,
        timeout=args.timeout,
    )

    try:
        status, text = client.post_payload(payload)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if status < 200 or status >= 300:
        print(f"HTTP {status} from {client.url}", file=sys.stderr)
        _print_json_or_text(text)
        return 1

    _print_json_or_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
