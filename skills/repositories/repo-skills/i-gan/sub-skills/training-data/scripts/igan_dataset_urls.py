#!/usr/bin/env python3
"""Plan iGAN public HDF5 dataset archive URLs without network side effects.

This helper is a safe adaptation of the legacy dataset download shell pattern.
It prints deterministic URL, size, and target-path plans only. It never invokes
wget, unzip, rm, or any network API.
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import PurePosixPath

BASE_URL = "http://efrosgans.eecs.berkeley.edu/iGAN/datasets"

DATASETS = OrderedDict(
    [
        ("outdoor_64", dict(domain="outdoor natural images", resolution=64, channels=3, count="150K", size="1.4 GB", size_bytes=1_400_000_000)),
        ("outdoor_128", dict(domain="outdoor natural images", resolution=128, channels=3, count="150K", size="5.5 GB", size_bytes=5_500_000_000)),
        ("church_64", dict(domain="outdoor church images", resolution=64, channels=3, count="126K", size="1.3 GB", size_bytes=1_300_000_000)),
        ("church_128", dict(domain="outdoor church images", resolution=128, channels=3, count="126K", size="4.6 GB", size_bytes=4_600_000_000)),
        ("shoes_64", dict(domain="shoe product images", resolution=64, channels=3, count="50K", size="260 MB", size_bytes=260_000_000)),
        ("shoes_128", dict(domain="shoe product images", resolution=128, channels=3, count="50K", size="922 MB", size_bytes=922_000_000)),
        ("handbag_64", dict(domain="handbag product images", resolution=64, channels=3, count="137K", size="774 MB", size_bytes=774_000_000)),
        ("handbag_128", dict(domain="handbag product images", resolution=128, channels=3, count="137K", size="2.8 GB", size_bytes=2_800_000_000)),
        ("sketch_shoes_64", dict(domain="Photoshop shoe sketches", resolution=64, channels=1, count="50K", size="76 MB", size_bytes=76_000_000)),
        ("sketch_shoes_128", dict(domain="Photoshop shoe sketches", resolution=128, channels=1, count="50K", size="278 MB", size_bytes=278_000_000)),
        ("hed_shoes_64", dict(domain="HED shoe edges", resolution=64, channels=1, count="50K", size="69 MB", size_bytes=69_000_000)),
        ("hed_shoes_128", dict(domain="HED shoe edges", resolution=128, channels=1, count="50K", size="244 MB", size_bytes=244_000_000)),
    ]
)


def target_path(output_dir: str, filename: str) -> str:
    """Return a deterministic POSIX-style target path for command planning."""
    return str(PurePosixPath(output_dir) / filename)


def build_plan(name: str, output_dir: str) -> dict:
    """Build a dry-run plan for one known dataset."""
    meta = DATASETS[name].copy()
    zip_name = f"{name}.zip"
    hdf5_name = f"{name}.hdf5"
    size_bytes = meta["size_bytes"]
    plan = {
        "dataset": name,
        "url": f"{BASE_URL}/{zip_name}",
        "zip_target": target_path(output_dir, zip_name),
        "hdf5_target": target_path(output_dir, hdf5_name),
        "compressed_size": meta["size"],
        "compressed_size_bytes": size_bytes,
        "minimum_peak_disk_note": "reserve space for both the ZIP archive and extracted HDF5 during unzip",
        "suggested_peak_disk_bytes_at_least": size_bytes * 2,
        "domain": meta["domain"],
        "resolution": meta["resolution"],
        "channels": meta["channels"],
        "approximate_source_count": meta["count"],
        "network_side_effects": False,
    }
    return plan


def format_table(plans: list[dict]) -> str:
    """Format plans as a stable text table."""
    headers = ["dataset", "res", "ch", "size", "count", "url"]
    rows = []
    for plan in plans:
        rows.append(
            [
                plan["dataset"],
                str(plan["resolution"]),
                str(plan["channels"]),
                plan["compressed_size"],
                plan["approximate_source_count"],
                plan["url"],
            ]
        )
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]
    fmt = "  ".join(f"{{:<{width}}}" for width in widths)
    lines = [fmt.format(*headers), fmt.format(*["-" * width for width in widths])]
    lines.extend(fmt.format(*row) for row in rows)
    return "\n".join(lines)


def format_detail(plan: dict, show_shell_plan: bool = False) -> str:
    """Format one dry-run plan with optional commented shell recipe."""
    lines = [
        f"Dataset: {plan['dataset']}",
        f"Domain: {plan['domain']}",
        f"Resolution/channels: {plan['resolution']}x{plan['resolution']} / {plan['channels']}",
        f"Approximate source count: {plan['approximate_source_count']}",
        f"Compressed size: {plan['compressed_size']}",
        f"URL: {plan['url']}",
        f"ZIP target: {plan['zip_target']}",
        f"HDF5 target: {plan['hdf5_target']}",
        f"Peak disk note: {plan['minimum_peak_disk_note']}",
        "Side effects: none (dry-run planner)",
    ]
    if show_shell_plan:
        lines.extend(
            [
                "",
                "Commented shell plan (not executed by this helper):",
                f"# wget -N {plan['url']!r} -O {plan['zip_target']!r}",
                f"# unzip {plan['zip_target']!r} -d {str(PurePosixPath(plan['hdf5_target']).parent)!r}",
                f"# rm -f {plan['zip_target']!r}",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run iGAN public HDF5 dataset URL and target-path planner. No network calls are made."
    )
    parser.add_argument("--dataset", choices=list(DATASETS), help="single dataset name to plan")
    parser.add_argument("--list", action="store_true", help="list all known datasets as a table")
    parser.add_argument("--output-dir", default="datasets", help="directory that would receive ZIP/HDF5 targets (default: datasets)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON instead of text")
    parser.add_argument("--show-shell-plan", action="store_true", help="include commented wget/unzip/rm commands for manual execution")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dataset:
        plans = [build_plan(args.dataset, args.output_dir)]
    else:
        plans = [build_plan(name, args.output_dir) for name in DATASETS]

    if args.json:
        print(json.dumps(plans[0] if args.dataset else plans, indent=2, sort_keys=True))
    elif args.dataset:
        print(format_detail(plans[0], show_shell_plan=args.show_shell_plan))
    else:
        print(format_table(plans))
        print("\nUse --dataset NAME for target paths. This helper performs no downloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
