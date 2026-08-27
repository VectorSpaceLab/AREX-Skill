#!/usr/bin/env python3
"""Validate integer RoboCasa scene/split selectors without importing RoboCasa.

This helper is intentionally stdlib-only and never downloads, imports MuJoCo,
or checks the asset tree. It catches ambiguous combinations before a caller
constructs a Kitchen environment. Custom dictionary selectors are out of scope.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import product


LAYOUT_GROUPS = {
    -1: list(range(1, 11)),
    -2: list(range(11, 61)),
    -3: list(range(1, 61)),
    -4: [1, 3, 5, 6, 8],
    -5: [2, 4, 7, 9, 10],
    -6: [2, 4, 7, 8, 9, 10],
}
STYLE_GROUPS = {
    -1: list(range(1, 11)),
    -2: list(range(11, 61)),
    -3: list(range(1, 61)),
}
REGISTRIES = {"objaverse", "lightwheel", "aigen"}


def _expand(values: list[int] | None, groups: dict[int, list[int]], label: str) -> list[int] | None:
    if values is None:
        return None
    result: list[int] = []
    for value in values:
        if value in groups:
            result.extend(groups[value])
        elif 1 <= value <= 60:
            result.append(value)
        else:
            raise ValueError(f"{label} id {value} is not 1..60 or a supported group sentinel")
    # Preserve caller order while removing duplicates.
    return list(dict.fromkeys(result))


def _parse(args: argparse.Namespace) -> dict:
    has_individual = args.layout_ids is not None or args.style_ids is not None
    has_pairs = args.layout_and_style_ids is not None
    if has_pairs and has_individual:
        raise ValueError(
            "layout_and_style_ids is mutually exclusive with layout_ids and style_ids"
        )

    if args.split is not None and (has_individual or has_pairs):
        raise ValueError(
            "do not combine split with explicit layout/style selectors; split would override them"
        )

    if args.split is not None and args.obj_instance_split is not None:
        if args.obj_instance_split != args.split and args.split != "all":
            raise ValueError(
                "obj_instance_split conflicts with the object split implied by split"
            )

    registries = args.obj_registries
    if registries is not None:
        if not registries:
            raise ValueError("obj_registries must contain at least one registry")
        unknown = sorted(set(registries) - REGISTRIES)
        if unknown:
            raise ValueError(f"unsupported object registry: {', '.join(unknown)}")
        if len(set(registries)) != len(registries):
            raise ValueError("obj_registries must not contain duplicates")

    if args.split == "target":
        layout_ids = list(range(1, 11))
        style_ids = list(range(1, 11))
        pairs = [[i, i] for i in range(1, 11)]
        object_split = "target"
    elif args.split == "pretrain":
        layout_ids = list(range(11, 61))
        style_ids = list(range(11, 61))
        pairs = [[layout, style] for layout, style in product(layout_ids, style_ids)]
        object_split = "pretrain"
    elif args.split == "all":
        layout_ids = list(range(1, 61))
        style_ids = list(range(1, 61))
        pairs = [[layout, style] for layout, style in product(layout_ids, style_ids)]
        object_split = None
    elif has_pairs:
        pairs = []
        for pair in args.layout_and_style_ids:
            layout, style = pair
            _expand([layout], LAYOUT_GROUPS, "layout")
            _expand([style], STYLE_GROUPS, "style")
            if not (1 <= layout <= 60 and 1 <= style <= 60):
                raise ValueError("explicit layout/style pairs must use positive ids 1..60")
            pairs.append([layout, style])
        layout_ids = sorted({pair[0] for pair in pairs})
        style_ids = sorted({pair[1] for pair in pairs})
        object_split = args.obj_instance_split
    else:
        layout_ids = _expand(args.layout_ids, LAYOUT_GROUPS, "layout")
        style_ids = _expand(args.style_ids, STYLE_GROUPS, "style")
        if layout_ids is None:
            layout_ids = list(range(1, 61))
        if style_ids is None:
            style_ids = list(range(1, 61))
        pairs = [[layout, style] for layout, style in product(layout_ids, style_ids)]
        object_split = args.obj_instance_split

    return {
        "split": args.split,
        "layout_ids": layout_ids,
        "style_ids": style_ids,
        "layout_and_style_ids": pairs if len(pairs) <= 100 else None,
        "layout_and_style_count": len(pairs),
        "pairs_omitted_from_output": len(pairs) > 100,
        "object_instance_split": object_split,
        "obj_registries": registries,
        "asset_check_performed": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate RoboCasa integer scene selectors; never downloads assets."
    )
    parser.add_argument("--split", choices=("pretrain", "target", "all"))
    parser.add_argument("--layout-ids", nargs="+", type=int)
    parser.add_argument("--style-ids", nargs="+", type=int)
    parser.add_argument(
        "--layout-and-style-ids",
        nargs=2,
        type=int,
        action="append",
        metavar=("LAYOUT", "STYLE"),
        help="repeat for explicit positive layout/style pairs",
    )
    parser.add_argument(
        "--obj-instance-split", choices=("pretrain", "target")
    )
    parser.add_argument(
        "--obj-registries",
        nargs="+",
        choices=sorted(REGISTRIES),
        help="one or more of objaverse, lightwheel, aigen",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = _parse(args)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
