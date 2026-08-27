#!/usr/bin/env python3
"""Python 3 safe downloader for Tencent ML-Images URL-list rows.

Adapted from the repository's Python 2 downloader. Defaults are explicit and
safe to inspect; use --dry-run before allowing network writes.

Example dry run:
  python download_urls.py --url-list train_urls_tiny.txt --im-list out.txt --save-dir images --limit 5 --dry-run
"""

import argparse
import concurrent.futures as futures
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-list", required=True, type=Path, help="Input rows: URL followed by label tokens.")
    parser.add_argument("--im-list", required=True, type=Path, help="Output local image-list file to write.")
    parser.add_argument("--save-dir", required=True, type=Path, help="Directory for downloaded images.")
    parser.add_argument("--invalid-url-file", type=Path, default=Path("invalid_url.txt"), help="File to record failed URLs.")
    parser.add_argument("--num-threads", type=int, default=8, help="Concurrent download workers.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum rows to process; 0 means all rows.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned filenames without network or writes.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing downloaded image files.")
    return parser.parse_args()


def read_rows(path: Path, limit: int) -> List[Tuple[int, str, List[str]]]:
    rows: List[Tuple[int, str, List[str]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, raw in enumerate(handle, start=1):
            if limit and len(rows) >= limit:
                break
            parts = [part for part in raw.rstrip("\n").split("\t") if part]
            if not parts:
                continue
            if not parts[0].startswith(("http://", "https://")):
                raise ValueError(f"line {lineno}: first field is not an http(s) URL: {parts[0]}")
            rows.append((lineno, parts[0], parts[1:]))
    return rows


def derive_name(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    pieces = [p for p in parsed.path.split("/") if p]
    if not pieces:
        return "downloaded_image"
    if len(pieces) >= 2:
        name = f"{pieces[-2]}_{pieces[-1]}"
    else:
        name = pieces[-1]
    # Avoid path traversal or shell-sensitive names.
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)


def download_one(row, save_dir: Path, timeout: float, overwrite: bool):
    lineno, url, labels = row
    name = derive_name(url)
    target = save_dir / name
    if target.exists() and not overwrite:
        return {"ok": True, "line": lineno, "url": url, "name": name, "labels": labels, "status": "exists"}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read()
        target.write_bytes(data)
        return {"ok": True, "line": lineno, "url": url, "name": name, "labels": labels, "status": "downloaded"}
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        return {"ok": False, "line": lineno, "url": url, "name": name, "error": str(exc)}


def main() -> int:
    args = parse_args()
    if args.num_threads < 1:
        print("--num-threads must be >= 1", file=sys.stderr)
        return 2
    rows = read_rows(args.url_list, args.limit)
    print(f"Loaded {len(rows)} URL rows from {args.url_list}")
    if args.dry_run:
        for lineno, url, labels in rows:
            print(f"DRY-RUN line={lineno} url={url} -> {derive_name(url)} labels={len(labels)}")
        return 0

    args.save_dir.mkdir(parents=True, exist_ok=True)
    args.im_list.parent.mkdir(parents=True, exist_ok=True)
    args.invalid_url_file.parent.mkdir(parents=True, exist_ok=True)

    lock = threading.Lock()
    ok_count = 0
    bad_count = 0
    with args.im_list.open("w", encoding="utf-8") as im_handle, args.invalid_url_file.open("w", encoding="utf-8") as invalid_handle:
        with futures.ThreadPoolExecutor(max_workers=args.num_threads) as pool:
            future_map = {pool.submit(download_one, row, args.save_dir, args.timeout, args.overwrite): row for row in rows}
            for fut in futures.as_completed(future_map):
                result = fut.result()
                with lock:
                    if result["ok"]:
                        ok_count += 1
                        im_handle.write(result["name"] + "\t" + "\t".join(result["labels"]) + "\n")
                        print(f"OK {ok_count}/{len(rows)} line={result['line']} {result['status']} {result['name']}")
                    else:
                        bad_count += 1
                        invalid_handle.write(result["url"] + "\n")
                        print(f"INVALID line={result['line']} url={result['url']} error={result['error']}")
    print(f"Finished: downloaded_or_existing={ok_count}, invalid={bad_count}, total={len(rows)}")
    return 0 if bad_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
