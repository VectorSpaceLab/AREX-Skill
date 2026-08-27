#!/usr/bin/env python3
"""List or optionally download the public DragGAN checkpoint manifest.

The helper is intentionally dry-run by default. It uses atomic ``.part`` files
when --execute is requested and never writes into the generated skill tree
unless the user explicitly chooses that directory.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

MANIFEST = {
    "stylegan2_lions_512_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/lions_512_pytorch.pkl",
    "stylegan2_dogs_1024_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/dogs_1024_pytorch.pkl",
    "stylegan2_horses_256_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/horses_256_pytorch.pkl",
    "stylegan2_elephants_512_pytorch.pkl": "https://storage.googleapis.com/self-distilled-stylegan/elephants_512_pytorch.pkl",
    "stylegan2-ffhq-512x512.pkl": "https://api.ngc.nvidia.com/v2/models/nvidia/research/stylegan2/versions/1/files/stylegan2-ffhq-512x512.pkl",
    "stylegan2-afhqcat-512x512.pkl": "https://api.ngc.nvidia.com/v2/models/nvidia/research/stylegan2/versions/1/files/stylegan2-afhqcat-512x512.pkl",
    "stylegan2-car-config-f.pkl": "http://d36zk2xti64re0.cloudfront.net/stylegan2/networks/stylegan2-car-config-f.pkl",
    "stylegan2-cat-config-f.pkl": "http://d36zk2xti64re0.cloudfront.net/stylegan2/networks/stylegan2-cat-config-f.pkl",
}


def download(url: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "disco-draggan-checkpoint-helper/1"})
    written = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, part.open("wb") as handle:
            expected = response.headers.get("Content-Length")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
        if expected and written != int(expected):
            raise RuntimeError(f"size mismatch: wrote {written} bytes, expected {expected}")
        part.replace(dest)
    except Exception:
        part.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="List or download DragGAN checkpoint manifest entries.")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"), help="Destination directory.")
    parser.add_argument("--model", action="append", choices=sorted(MANIFEST), help="Download/list one manifest name; repeatable.")
    parser.add_argument("--execute", action="store_true", help="Actually download selected files. Default is a dry run.")
    parser.add_argument("--force", action="store_true", help="Redownload files that already exist.")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    dest_dir = args.checkpoint_dir.expanduser().resolve()
    names = args.model or sorted(MANIFEST)
    rows = []
    failures = 0
    for name in names:
        dest = dest_dir / name
        row = {"name": name, "url": MANIFEST[name], "path": str(dest), "exists": dest.exists(), "action": "skip"}
        if dest.exists() and not args.force:
            row["action"] = "skip-existing"
        elif not args.execute:
            row["action"] = "would-download"
        else:
            try:
                download(MANIFEST[name], dest, args.timeout)
                row["action"] = "downloaded"
                row["exists"] = True
            except Exception as exc:  # noqa: BLE001 - report all network failures
                row["action"] = "failed"
                row["error"] = f"{type(exc).__name__}: {exc}"
                failures += 1
        rows.append(row)

    if args.json:
        print(json.dumps({"checkpoint_dir": str(dest_dir), "dry_run": not args.execute, "files": rows}, indent=2, sort_keys=True))
    else:
        print(f"Destination: {dest_dir}")
        for row in rows:
            print(f"{row['action']}: {row['name']} <- {row['url']}")
            if row.get("error"):
                print(f"  ERROR: {row['error']}", file=sys.stderr)
        if not args.execute:
            print("Dry run only. Add --execute to download; review URLs, disk space, and licensing first.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
