#!/usr/bin/env python3
"""Preview ManiSkill demo/asset download IDs and commands without downloading."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


def sample(items: Iterable[str], limit: int) -> list[str]:
    values = sorted(items)
    if limit <= 0 or len(values) <= limit:
        return values
    return values[:limit] + [f"... {len(values) - limit} more"]


def shell_join(cmd: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["demo", "asset", "both"], default="both")
    parser.add_argument("--category", help="Asset category to list, e.g. scene, robot, task_assets, objects")
    parser.add_argument("--uid", help="Demo or asset UID to print a download command for")
    parser.add_argument("--output-dir", help="Optional output/cache directory to include in the printed command")
    parser.add_argument("--limit", type=int, default=30, help="Maximum IDs to print per list; 0 means all")
    args = parser.parse_args()

    print("No downloads are performed by this helper. It only reads installed package registries.\n")

    if args.kind in {"demo", "both"}:
        try:
            from mani_skill.utils.download_demo import DATASET_SOURCES
        except Exception as exc:
            print(f"Could not import demo registry: {exc}")
        else:
            print("Demo dataset UIDs:")
            for item in sample(DATASET_SOURCES.keys(), args.limit):
                print(f"  {item}")
            if args.uid and args.uid in DATASET_SOURCES:
                cmd = ["python", "-m", "mani_skill.utils.download_demo", args.uid]
                if args.output_dir:
                    cmd.extend(["-o", args.output_dir])
                print(f"Planned demo download command: {shell_join(cmd)}")
            elif args.uid:
                print(f"UID {args.uid!r} was not found in the demo registry.")
            print()

    if args.kind in {"asset", "both"}:
        try:
            from mani_skill.utils import assets
        except Exception as exc:
            print(f"Could not import asset registry: {exc}")
        else:
            categories = sorted({v.source_type for v in assets.DATA_SOURCES.values()})
            print("Asset categories:")
            for cat in categories:
                print(f"  {cat}")
            if args.category:
                matching = [k for k, v in assets.DATA_SOURCES.items() if v.source_type == args.category]
                print(f"\nAsset UIDs in category {args.category!r}:")
                for item in sample(matching, args.limit):
                    print(f"  {item}")
            else:
                print("\nAsset group UIDs:")
                for item in sample(assets.DATA_GROUPS.keys(), args.limit):
                    print(f"  {item}")
            if args.uid and (args.uid in assets.DATA_GROUPS or args.uid in assets.DATA_SOURCES):
                cmd = ["python", "-m", "mani_skill.utils.download_asset", args.uid]
                if args.output_dir:
                    cmd.extend(["-o", args.output_dir])
                cmd.append("-y")
                print(f"Planned asset download command: {shell_join(cmd)}")
                print("Remove -y if the user wants interactive prompts instead of non-interactive mode.")
            elif args.uid:
                print(f"UID {args.uid!r} was not found in asset groups or sources.")

    print("\nAsk the user before running any printed download command; downloads require network and may alter cache directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
