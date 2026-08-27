#!/usr/bin/env python3
"""Run a tiny img2dataset download against a local HTTP image fixture.

The default path avoids external network access and W&B. It creates a few tiny
PPM images, serves them on 127.0.0.1, writes a temporary URL list, calls
img2dataset.download(), and prints simple validation signals.
"""

from __future__ import annotations

import argparse
import functools
import json
import shutil
import sys
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator


PPM_FIXTURES = {
    "red.ppm": b"P6\n2 2\n255\n" + bytes([255, 0, 0] * 4),
    "green.ppm": b"P6\n2 2\n255\n" + bytes([0, 255, 0] * 4),
    "blue.ppm": b"P6\n2 2\n255\n" + bytes([0, 0, 255] * 4),
}


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with concise stderr-free request logging."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - inherited name
        return


def positive_int(value: str) -> int:
    """argparse type for positive integers."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny local HTTP image fixture and run img2dataset.download "
            "with safe small defaults. No external network or W&B is used by default."
        )
    )
    parser.add_argument(
        "--output-folder",
        default="tiny-img2dataset-output",
        help="Folder where img2dataset should write the tiny output (default: %(default)s).",
    )
    parser.add_argument(
        "--output-format",
        choices=["files", "webdataset", "parquet", "dummy"],
        default="files",
        help="img2dataset output_format to exercise (default: %(default)s).",
    )
    parser.add_argument(
        "--image-size",
        type=positive_int,
        default=32,
        help="Resize target passed to img2dataset.download (default: %(default)s).",
    )
    parser.add_argument(
        "--thread-count",
        type=positive_int,
        default=4,
        help="Small downloader thread_count passed to img2dataset.download (default: %(default)s).",
    )
    parser.add_argument(
        "--processes-count",
        type=positive_int,
        default=1,
        help="Small processes_count passed to img2dataset.download (default: %(default)s).",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary fixture directory and URL list for inspection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned download call without importing or running img2dataset.",
    )
    return parser.parse_args(argv)


def write_fixture_files(root: Path) -> Path:
    """Create local image fixtures and a URL-list placeholder file."""
    image_dir = root / "http-root"
    image_dir.mkdir(parents=True, exist_ok=True)
    for filename, data in PPM_FIXTURES.items():
        (image_dir / filename).write_bytes(data)
    return image_dir


def write_url_list(root: Path, base_url: str) -> Path:
    """Write one URL per fixture image."""
    url_list = root / "urls.txt"
    urls = [f"{base_url}/{name}" for name in sorted(PPM_FIXTURES)]
    url_list.write_text("\n".join(urls) + "\n", encoding="utf-8")
    return url_list


@contextmanager
def local_http_server(directory: Path) -> Iterator[str]:
    """Serve a directory from localhost and yield its base URL."""
    handler = functools.partial(QuietHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, name="tiny-img2dataset-http", daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def print_plan(args: argparse.Namespace) -> None:
    output = Path(args.output_folder).expanduser()
    print("Planned tiny img2dataset run:")
    print(f"  output_folder: {output}")
    print(f"  output_format: {args.output_format}")
    print(f"  image_size: {args.image_size}")
    print(f"  thread_count: {args.thread_count}")
    print(f"  processes_count: {args.processes_count}")
    print("  input_format: txt")
    print("  number_sample_per_shard: 10")
    print("  timeout: 5")
    print("  retries: 0")
    print("  max_shard_retry: 0")
    print("  compute_hash: sha256")
    print("  extract_exif: False")
    print("  enable_wandb: False")
    print("  disallowed_header_directives: [] (local fixture only)")
    print("  network: local 127.0.0.1 HTTP fixture only")


def summarize_output(output: Path, output_format: str) -> int:
    """Print simple output validation signals. Return process exit status."""
    stats = sorted(output.glob("*_stats.json"))
    parquets = sorted(output.glob("*.parquet"))
    jpgs = sorted(output.rglob("*.jpg"))
    tars = sorted(output.glob("*.tar"))

    print("\nValidation summary:")
    print(f"  output folder: {output}")
    print(f"  stats json files: {[p.name for p in stats]}")
    print(f"  metadata parquet files: {[p.name for p in parquets]}")
    if output_format == "files":
        print(f"  jpg files: {[str(p.relative_to(output)) for p in jpgs]}")
    elif output_format == "webdataset":
        print(f"  tar files: {[p.name for p in tars]}")
    elif output_format == "dummy":
        print("  dummy output: no image payload files are expected")

    if stats:
        try:
            first_stats = json.loads(stats[0].read_text(encoding="utf-8"))
            print(
                "  first stats:",
                {k: first_stats.get(k) for k in ["count", "successes", "failed_to_download", "failed_to_resize"]},
            )
            print("  first status_dict:", first_stats.get("status_dict"))
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  warning: could not parse stats JSON: {exc}", file=sys.stderr)

    if parquets:
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel

            df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
            print("  metadata statuses:", df["status"].value_counts(dropna=False).to_dict())
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  warning: could not inspect metadata parquet: {exc}", file=sys.stderr)

    if output_format == "files" and not jpgs:
        print("ERROR: no JPG files were created for output_format=files", file=sys.stderr)
        return 2
    if output_format == "webdataset" and not tars:
        print("ERROR: no TAR shard was created for output_format=webdataset", file=sys.stderr)
        return 2
    if output_format == "parquet" and not parquets:
        print("ERROR: no Parquet shard was created for output_format=parquet", file=sys.stderr)
        return 2
    if output_format == "dummy" and not stats:
        print("ERROR: no stats JSON was created for output_format=dummy", file=sys.stderr)
        return 2
    return 0


def run_demo(args: argparse.Namespace) -> int:
    output = Path(args.output_folder).expanduser()
    if output.exists() and any(output.iterdir()):
        print(
            "Note: output folder already exists and is not empty. "
            "img2dataset's default incremental mode may skip completed shards. "
            "Choose a new --output-folder for a fresh demo.",
            file=sys.stderr,
        )

    temp_root = Path(tempfile.mkdtemp(prefix="img2dataset-tiny-"))
    try:
        image_dir = write_fixture_files(temp_root)
        with local_http_server(image_dir) as base_url:
            url_list = write_url_list(temp_root, base_url)
            print("Running tiny img2dataset demo against local HTTP fixture")
            print(f"  URL count: {len(PPM_FIXTURES)}")
            print(f"  output folder: {output}")
            print(f"  output format: {args.output_format}")

            from img2dataset import download  # pylint: disable=import-outside-toplevel

            download(
                url_list=str(url_list),
                image_size=args.image_size,
                output_folder=str(output),
                processes_count=args.processes_count,
                output_format=args.output_format,
                input_format="txt",
                thread_count=args.thread_count,
                number_sample_per_shard=10,
                extract_exif=False,
                timeout=5,
                enable_wandb=False,
                compute_hash="sha256",
                distributor="multiprocessing",
                retries=0,
                incremental_mode="incremental",
                max_shard_retry=0,
                disallowed_header_directives=[],
                ignore_ssl_certificate=False,
            )
    finally:
        if args.keep_temp:
            print(f"Kept temporary fixture directory: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)

    return summarize_output(output, args.output_format)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print_plan(args)
    if args.dry_run:
        print("Dry run only; no files created and img2dataset was not imported.")
        return 0
    return run_demo(args)


if __name__ == "__main__":
    raise SystemExit(main())
