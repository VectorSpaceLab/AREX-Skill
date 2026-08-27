#!/usr/bin/env python3
"""Build deterministic, no-dispatch ObsPy acquisition plans.

This helper uses only the Python standard library. It emits JSON that can be
reviewed before a caller dispatches an ObsPy client. It never contacts a URL,
opens a database, reads an archive, or writes output files.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import urlencode, urlparse

MAX_WINDOW_SECONDS = 7 * 24 * 3600
SERVICES = {"waveforms": "dataselect", "stations": "station", "events": "event"}


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            "time must be ISO-8601, for example 2020-01-01T00:00:00Z"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError("time must include an explicit UTC offset or Z")
    return parsed.astimezone(timezone.utc)


def fdsn_time(value: str) -> str:
    return parse_utc(value).isoformat(timespec="microseconds").replace(
        "+00:00", ""
    )


def normalize_selector(value: str, *, location: bool = False) -> str:
    value = value.strip()
    if not value:
        return "--" if location else value
    if location:
        # Match ObsPy's FDSN representation for blank location members.
        value = value.replace(" ", "")
        value = value.replace(",,", ",--,")
        if value.startswith(","):
            value = "--" + value
        if value.endswith(","):
            value += "--"
    return value


def validate_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base-url must be a complete http(s) URL")
    return value.rstrip("/")


def build_fdsn_plan(args: argparse.Namespace) -> dict:
    service = SERVICES[args.service]
    base = validate_base_url(args.base_url)
    start = parse_utc(args.start)
    end = parse_utc(args.end)
    if end <= start:
        raise ValueError("end must be after start")
    duration = (end - start).total_seconds()
    if duration > args.max_seconds:
        raise ValueError("time window exceeds --max-seconds")
    params = {"starttime": fdsn_time(args.start), "endtime": fdsn_time(args.end)}
    selectors = {}
    if service in {"dataselect", "station"}:
        for key in ("network", "station", "location", "channel"):
            raw = getattr(args, key)
            if raw is None:
                continue
            selectors[key] = normalize_selector(raw, location=key == "location")
        params.update(selectors)
    else:
        for key in ("minmagnitude", "maxmagnitude", "limit", "orderby"):
            raw = getattr(args, key)
            if raw is not None:
                params[key] = str(raw)
    url = f"{base}/fdsnws/{service}/1/query?{urlencode(params)}"
    return {
        "dispatch": False,
        "kind": "fdsn",
        "service": args.service,
        "endpoint_service": service,
        "base_url": base,
        "query_url": url,
        "starttime_utc": start.isoformat().replace("+00:00", "Z"),
        "endtime_utc": end.isoformat().replace("+00:00", "Z"),
        "duration_seconds": duration,
        "selectors": selectors,
        "parameters": params,
        "validation": [
            "review provider and service",
            "keep exact UTC bounds",
            "inspect result gaps/counts",
        ],
    }


def split_sds_path(
    root: str,
    network: str,
    station: str,
    location: str,
    channel: str,
    when: datetime,
    sds_type: str = "D",
) -> str:
    """Return the conventional SDS day-file path for one NSLC and date."""
    doy = when.timetuple().tm_yday
    # SDS uses an empty field for a blank location, unlike FDSN's '--'.
    filename = (
        f"{network}.{station}.{location}.{channel}.{sds_type}."
        f"{when.year}.{doy:03d}"
    )
    relative = PurePosixPath(
        str(when.year), network, station, f"{channel}.{sds_type}", filename
    )
    return str(PurePosixPath(root) / relative)


def build_sds_plan(args: argparse.Namespace) -> dict:
    start = parse_utc(args.start)
    end = parse_utc(args.end)
    if end <= start:
        raise ValueError("end must be after start")
    duration = (end - start).total_seconds()
    if duration > args.max_seconds:
        raise ValueError("time window exceeds --max-seconds")
    candidates = [
        split_sds_path(
            args.root,
            args.network,
            args.station,
            args.location,
            args.channel,
            start,
            args.sds_type,
        )
    ]
    if start.date() != end.date():
        candidates.append(
            split_sds_path(
                args.root,
                args.network,
                args.station,
                args.location,
                args.channel,
                end,
                args.sds_type,
            )
        )
    return {
        "dispatch": False,
        "kind": "sds",
        "root": args.root,
        "sds_type": args.sds_type,
        "selectors": {
            "network": args.network,
            "station": args.station,
            "location": args.location,
            "channel": args.channel,
        },
        "starttime_utc": start.isoformat().replace("+00:00", "Z"),
        "endtime_utc": end.isoformat().replace("+00:00", "Z"),
        "duration_seconds": duration,
        "candidate_day_files": candidates,
        "missing_day_policy": "report local gaps; never use implicit network fallback",
        "validation": [
            "confirm root is local",
            "check availability percentage",
            "inspect Stream.get_gaps()",
        ],
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--self-test", action="store_true", help="run deterministic checks and exit"
    )
    sub = p.add_subparsers(dest="kind")
    f = sub.add_parser("fdsn", help="plan an FDSN query without dispatch")
    f.add_argument("--service", choices=sorted(SERVICES), required=True)
    f.add_argument("--base-url", required=True)
    f.add_argument("--start", required=True)
    f.add_argument("--end", required=True)
    f.add_argument("--network")
    f.add_argument("--station")
    f.add_argument("--location", default="")
    f.add_argument("--channel")
    f.add_argument("--minmagnitude")
    f.add_argument("--maxmagnitude")
    f.add_argument("--limit")
    f.add_argument("--orderby")
    f.add_argument("--max-seconds", type=float, default=MAX_WINDOW_SECONDS)
    s = sub.add_parser("sds", help="plan local SDS day-file inspection without reading")
    s.add_argument("--root", required=True)
    s.add_argument("--network", required=True)
    s.add_argument("--station", required=True)
    s.add_argument("--location", default="")
    s.add_argument("--channel", required=True)
    s.add_argument("--sds-type", default="D")
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--max-seconds", type=float, default=MAX_WINDOW_SECONDS)
    return p


def self_test() -> None:
    assert normalize_selector("", location=True) == "--"
    assert normalize_selector(",00", location=True) == "--,00"
    assert normalize_selector("00,", location=True) == "00,--"
    fdsn = build_fdsn_plan(
        argparse.Namespace(
            service="waveforms",
            base_url="https://example.invalid",
            start="2020-01-01T00:00:00Z",
            end="2020-01-01T00:01:00Z",
            network="IU",
            station="A*",
            location="",
            channel="BH?",
            minmagnitude=None,
            maxmagnitude=None,
            limit=None,
            orderby=None,
            max_seconds=3600,
        )
    )
    assert "station=A%2A" in fdsn["query_url"]
    assert "location=--" in fdsn["query_url"]
    plan = build_sds_plan(
        argparse.Namespace(
            root="/archive",
            network="IU",
            station="ANMO",
            location="",
            channel="BHZ",
            sds_type="D",
            start="2020-01-01T23:59:00Z",
            end="2020-01-02T00:01:00Z",
            max_seconds=3600,
        )
    )
    assert len(plan["candidate_day_files"]) == 2
    assert ".ANMO..BHZ.D." in plan["candidate_day_files"][0]
    print("query_plan self-test: ok")


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    try:
        if args.kind == "fdsn":
            result = build_fdsn_plan(args)
        elif args.kind == "sds":
            result = build_sds_plan(args)
        else:
            parser().error("choose a plan type or --self-test")
    except ValueError as exc:
        parser().error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
