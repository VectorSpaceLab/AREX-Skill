#!/usr/bin/env python3
"""List installed dm_control task registries without reading a source checkout."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict


def _print_suite(filter_domain: str | None, benchmarking_only: bool) -> None:
    from dm_control import suite

    tasks = suite.BENCHMARKING if benchmarking_only else suite.ALL_TASKS
    by_domain: dict[str, list[str]] = defaultdict(list)
    for domain, task in tasks:
        if filter_domain and domain != filter_domain:
            continue
        by_domain[domain].append(task)

    print(f"Control Suite tasks: {sum(len(v) for v in by_domain.values())}")
    for domain in sorted(by_domain):
        print(f"  {domain}: {', '.join(by_domain[domain])}")


def _print_manipulation(filter_tag: str | None) -> None:
    from dm_control import manipulation

    print(f"Manipulation tags: {', '.join(manipulation.TAGS)}")
    if filter_tag:
        if filter_tag not in manipulation.TAGS:
            raise ValueError(f"unknown manipulation tag {filter_tag!r}; choose one of {manipulation.TAGS}")
        names = manipulation.get_environments_by_tag(filter_tag)
        print(f"Manipulation tasks tagged {filter_tag!r}: {len(names)}")
    else:
        names = manipulation.ALL
        print(f"Manipulation tasks: {len(names)}")
    for name in names:
        print(f"  {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="store_true", help="list Control Suite tasks")
    parser.add_argument("--manipulation", action="store_true", help="list manipulation tasks")
    parser.add_argument("--domain", help="restrict suite listing to one domain")
    parser.add_argument("--benchmarking-only", action="store_true", help="list only suite.BENCHMARKING")
    parser.add_argument("--manipulation-tag", help="restrict manipulation listing to one tag")
    args = parser.parse_args(argv)

    if not args.suite and not args.manipulation:
        args.suite = args.manipulation = True

    try:
        if args.suite:
            _print_suite(args.domain, args.benchmarking_only)
        if args.manipulation:
            _print_manipulation(args.manipulation_tag)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
