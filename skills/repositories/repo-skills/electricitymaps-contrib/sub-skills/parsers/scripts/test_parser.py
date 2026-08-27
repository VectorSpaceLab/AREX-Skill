#!/usr/bin/env python3
"""Inspect or execute Electricity Maps live parsers with explicit repo-root paths.

Safe examples:
    python scripts/test_parser.py --repo-root /path/to/electricitymaps-contrib --list
    python scripts/test_parser.py --repo-root . --describe FR production

Live execution examples (network/API tokens may be required):
    python scripts/test_parser.py --repo-root . --execute FR production
    python scripts/test_parser.py --repo-root . --execute "NO-NO3->SE" exchange
"""

from __future__ import annotations

import argparse
import inspect
import logging
import pprint
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def add_repo_paths(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    for candidate in reversed([root, root / "electricitymap" / "contrib", root / "libs" / "types" / "src"]):
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def import_runtime():
    try:
        from electricitymap.contrib.parsers.lib.parsers import PARSER_DATA_TYPE_TO_DICT
        from electricitymap.contrib.parsers.lib.quality import (
            ValidationError,
            validate_consumption,
            validate_exchange,
        )
        from electricitymap.contrib.types import EXCHANGE_DATA_TYPES, ParserDataType, ZoneKey
    except Exception as exc:
        raise SystemExit(
            "Failed to import parser runtime. Install parser dependencies and pass "
            f"--repo-root if needed. Root cause: {exc.__class__.__name__}: {exc}"
        ) from exc
    return PARSER_DATA_TYPE_TO_DICT, ValidationError, validate_consumption, validate_exchange, EXCHANGE_DATA_TYPES, ParserDataType, ZoneKey


def infer_data_type(zone: str, data_type: str | None, parser_data_type_cls, exchange_data_types) -> Any:
    if data_type:
        try:
            return parser_data_type_cls(data_type)
        except ValueError as exc:
            valid = ", ".join(dt.value for dt in parser_data_type_cls)
            raise SystemExit(f"Unknown data type {data_type!r}. Valid values: {valid}") from exc
    return parser_data_type_cls.EXCHANGE if "->" in zone else parser_data_type_cls.PRODUCTION


def list_registry(parser_maps, data_type_filter: str | None, parser_data_type_cls) -> None:
    print("Parser registry counts:")
    for data_type in parser_data_type_cls:
        mapping = parser_maps.get(data_type, {})
        if data_type_filter and data_type.value != data_type_filter:
            continue
        print(f"- {data_type.value}: {len(mapping)}")
        if data_type_filter:
            for key in sorted(mapping):
                fn = mapping[key]
                print(f"  {key}: {fn.__module__}.{fn.__name__}")


def describe_parser(zone: str, data_type: Any, parser_maps) -> Callable[..., Any]:
    mapping = parser_maps[data_type]
    if zone not in mapping:
        available = ", ".join(sorted(str(k) for k in mapping)[:40])
        suffix = " ..." if len(mapping) > 40 else ""
        raise SystemExit(
            f"No {data_type.value} parser registered for {zone!r}. "
            f"First available keys: {available}{suffix}"
        )
    fn = mapping[zone]
    print(f"zone/exchange key: {zone}")
    print(f"data type: {data_type.value}")
    print(f"function: {fn.__module__}.{fn.__name__}")
    try:
        print(f"signature: {inspect.signature(fn)}")
    except Exception as exc:
        print(f"signature: unavailable ({exc})")
    doc = inspect.getdoc(fn)
    if doc:
        print("doc: " + doc.splitlines()[0])
    return fn


def execute_parser(
    zone: str,
    data_type: Any,
    target_datetime: str | None,
    parser_maps,
    exchange_data_types,
    validation_error_cls,
    validate_consumption,
    validate_exchange,
) -> None:
    if data_type.value == "productionCapacity":
        raise SystemExit("productionCapacity is not supported here; use the capacity sub-skill.")

    parsed_target_datetime = datetime.fromisoformat(target_datetime) if target_datetime else None
    fn = describe_parser(zone, data_type, parser_maps)
    args = zone.split("->") if data_type in exchange_data_types else [zone]

    logger = logging.getLogger("electricitymaps-contrib.parser-smoke")
    start = time.time()
    res = fn(*args, target_datetime=parsed_target_datetime, logger=logger)
    elapsed_time = time.time() - start

    if not res:
        raise SystemExit(f"Error: parser returned nothing ({res!r})")

    res_list = list(res) if isinstance(res, list | tuple) else [res]
    try:
        dts = [event["datetime"] for event in res_list]
    except KeyError as exc:
        raise SystemExit(f"Parser output lacks `datetime` key. Full output:\n{res!r}") from exc

    if not all(type(dt) is datetime for dt in dts):
        raise SystemExit("Datetimes must be native datetime.datetime objects")
    if any(dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None for dt in dts):
        raise SystemExit("Datetimes must be timezone aware")

    first_dt = min(dts).astimezone(timezone.utc)
    last_dt = max(dts).astimezone(timezone.utc)

    print("\nParser result:")
    pprint.PrettyPrinter(width=120).pprint(res)
    print("---------------------")
    print(f"took {elapsed_time:.2f}s")
    print(f"min returned datetime: {first_dt} UTC")
    print(f"max returned datetime: {last_dt} UTC")

    for event in res_list:
        try:
            if data_type.value == "consumption":
                validate_consumption(event, zone)
            elif data_type.value == "exchange":
                validate_exchange(event, zone)
        except validation_error_cls as exc:
            logger.warning("Validation failed @ %s: %s", event.get("datetime"), exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zone", nargs="?", help="Zone key or exchange key, e.g. FR or NO-NO3->SE.")
    parser.add_argument("data_type", nargs="?", help="ParserDataType value such as production or exchange.")
    parser.add_argument("--repo-root", help="Path to an electricitymaps-contrib checkout.")
    parser.add_argument("--list", action="store_true", help="List parser registry counts or keys.")
    parser.add_argument("--describe", action="store_true", help="Describe the resolved parser without executing it.")
    parser.add_argument("--execute", action="store_true", help="Actually call the parser; may use network/API tokens.")
    parser.add_argument("--target-datetime", help="ISO datetime passed to the parser, e.g. 2024-01-01T00:00:00+00:00.")
    parser.add_argument("--data-type", dest="data_type_filter", help="Filter --list output to one ParserDataType value.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s %(message)s")
    add_repo_paths(args.repo_root)
    runtime = import_runtime()
    parser_maps, validation_error_cls, validate_consumption, validate_exchange, exchange_data_types, parser_data_type_cls, _zone_key_cls = runtime

    if args.list:
        list_registry(parser_maps, args.data_type_filter, parser_data_type_cls)
        return 0

    if not args.zone:
        parser.error("zone is required unless --list is used")
    data_type = infer_data_type(args.zone, args.data_type, parser_data_type_cls, exchange_data_types)

    if args.execute:
        execute_parser(
            args.zone,
            data_type,
            args.target_datetime,
            parser_maps,
            exchange_data_types,
            validation_error_cls,
            validate_consumption,
            validate_exchange,
        )
    else:
        describe_parser(args.zone, data_type, parser_maps)
        if not args.describe:
            print("\nNo live call executed. Add --execute to run the parser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
