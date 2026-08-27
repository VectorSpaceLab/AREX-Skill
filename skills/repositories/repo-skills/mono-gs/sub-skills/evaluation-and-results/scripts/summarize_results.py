#!/usr/bin/env python3
"""Summarize MonoGS result directories without importing MonoGS."""

import argparse
import json
from pathlib import Path


def rel(root, path):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def summarize(root):
    root = root.resolve()
    rows = []
    configs = sorted(
        root.rglob("config.yml"),
        key=lambda p: p.parent.stat().st_mtime if p.parent.exists() else 0,
        reverse=True,
    )
    for config in configs:
        run_dir = config.parent
        stats = sorted(run_dir.glob("plot/stats_*.json"))
        traj = sorted(run_dir.glob("plot/trj_*.json"))
        psnr = sorted(
            run_dir.glob("psnr/*/final_result.json"),
            key=lambda p: (0 if p.parent.name == "before_opt" else 1 if p.parent.name == "after_opt" else 2, p.parent.name),
        )
        plys = sorted(run_dir.glob("point_cloud/**/point_cloud.ply"))
        rows.append(
            {
                "run_dir": rel(root, run_dir),
                "config": rel(root, config),
                "stats": [rel(root, p) for p in stats],
                "trajectories": [rel(root, p) for p in traj],
                "psnr_summaries": [rel(root, p) for p in psnr],
                "point_clouds": [rel(root, p) for p in plys],
                "stats_preview": {rel(root, p): read_json(p) for p in stats[:3]},
                "psnr_preview": {rel(root, p): read_json(p) for p in psnr[:3]},
            }
        )
    return rows


def print_list(label, items):
    print(f"  {label}: {len(items)}")
    for item in items:
        print(f"    - {item}")


def main():
    parser = argparse.ArgumentParser(
        description="Summarize MonoGS result runs under a result root."
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        required=True,
        help="Result directory or a parent that contains timestamped MonoGS runs",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    rows = summarize(args.result_root)
    if args.json:
        print(json.dumps({"result_root": str(args.result_root), "runs": rows}, indent=2))
    else:
        print(f"Result root: {args.result_root}")
        if not rows:
            print("No MonoGS runs found: no config.yml files under result root.")
            return 1
        for row in rows:
            print(f"\nRun: {row['run_dir']}")
            print(f"  config: {row['config']}")
            print_list("stats files", row["stats"])
            print_list("trajectory files", row["trajectories"])
            print_list("psnr summaries", row["psnr_summaries"])
            print_list("point clouds", row["point_clouds"])
            for path, data in row["stats_preview"].items():
                print(f"  stats preview {path}: {json.dumps(data, sort_keys=True)}")
            for path, data in row["psnr_preview"].items():
                print(f"  psnr preview {path}: {json.dumps(data, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
