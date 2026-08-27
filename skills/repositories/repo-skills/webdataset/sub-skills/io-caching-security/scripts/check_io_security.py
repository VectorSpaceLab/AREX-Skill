#!/usr/bin/env python3
"""Local smoke checks for the io-caching-security WebDataset sub-skill.

The helper stays offline: it probes local files, trusted pipe execution,
secure-mode blocking, cache naming, and cache cleanup without credentials or
network access.
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import pickle
import shlex
import shutil
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict
from unittest.mock import patch

utils = importlib.import_module("webdataset.utils")
autodecode = importlib.import_module("webdataset.autodecode")
cache = importlib.import_module("webdataset.cache")
gopen_mod = importlib.import_module("webdataset.gopen")
handlers = importlib.import_module("webdataset.handlers")


def expect_raises(exc_type: type[BaseException], fn: Callable[[], Any], message_substring: str | None = None) -> str:
    """Assert that calling fn raises the expected exception type."""

    try:
        fn()
    except exc_type as exn:
        if message_substring is not None and message_substring not in str(exn):
            raise AssertionError(f"expected '{message_substring}' in {exn!r}") from exn
        return str(exn)
    except Exception as exn:  # pragma: no cover - defensive mismatch reporting
        raise AssertionError(f"expected {exc_type.__name__}, got {type(exn).__name__}: {exn}") from exn
    raise AssertionError(f"expected {exc_type.__name__} to be raised")


def make_tiny_tar(path: Path, member_name: str = "sample.txt", payload: bytes = b"hello") -> None:
    """Create a tiny tar archive at path."""

    with tarfile.open(path, "w") as tar:
        info = tarfile.TarInfo(member_name)
        info.size = len(payload)
        info.mtime = 0
        tar.addfile(info, io.BytesIO(payload))


def probe_local_files(workdir: Path) -> Dict[str, Any]:
    """Probe direct local-file access in non-secure mode."""

    local_path = workdir / "local.txt"
    local_path.write_text("local-content", encoding="utf-8")

    with gopen_mod.gopen(str(local_path), "rb") as stream:
        local_bytes = stream.read()
    with gopen_mod.gopen(f"file://{local_path}", "rb") as stream:
        file_url_bytes = stream.read()

    return {
        "path": str(local_path),
        "local_bytes": local_bytes.decode("utf-8"),
        "file_url_bytes": file_url_bytes.decode("utf-8"),
    }


def probe_pipe(workdir: Path) -> Dict[str, Any]:
    """Probe trusted pipe reads and writes."""

    out_path = workdir / "pipe.txt"
    payload = b"pipe-content"

    with gopen_mod.gopen(f"pipe:cat > {shlex.quote(str(out_path))}", "wb") as stream:
        stream.write(payload)
    with gopen_mod.gopen(f"pipe:cat {shlex.quote(str(out_path))}", "rb") as stream:
        round_trip = stream.read()

    return {
        "path": str(out_path),
        "round_trip": round_trip.decode("utf-8"),
    }


def probe_secure_mode(workdir: Path) -> Dict[str, Any]:
    """Probe the security guardrails in secure mode."""

    local_path = workdir / "secure.txt"
    local_path.write_text("secure-content", encoding="utf-8")
    previous_flag = utils.enforce_security
    previous_rewrite = os.environ.pop("GOPEN_REWRITE", None)

    try:
        utils.enforce_security = True

        local_block = expect_raises(
            ValueError,
            lambda: gopen_mod.gopen(str(local_path), "rb"),
            "unsafe_gopen is False",
        )
        file_block = expect_raises(
            ValueError,
            lambda: gopen_mod.gopen(f"file://{local_path}", "rb"),
            "unsafe_gopen is False",
        )
        pipe_block = expect_raises(
            ValueError,
            lambda: gopen_mod.gopen(f"pipe:cat {shlex.quote(str(local_path))}", "rb"),
            "unsafe_gopen is False",
        )

        os.environ["GOPEN_REWRITE"] = "http://example.com/=http://mirror.example/"
        rewrite_block = expect_raises(
            ValueError,
            lambda: gopen_mod.rewrite_url("http://example.com/data.tar"),
            "unsafe_gopen is False",
        )
        pickle_block = expect_raises(
            ValueError,
            lambda: autodecode.unpickle_loads(pickle.dumps({"a": 1})),
            "Unpickling is not allowed",
        )

        torch_block = None
        try:
            import torch

            buffer = io.BytesIO()
            torch.save(torch.tensor([1, 2, 3]), buffer)
            torch_block = expect_raises(
                ValueError,
                lambda: autodecode.torch_loads(buffer.getvalue()),
                "torch.loads is not allowed",
            )
        except Exception:
            torch_block = "torch unavailable, skipped"

        stdin_stream = gopen_mod.gopen("-", "rb")
        stdout_stream = gopen_mod.gopen("-", "wb")

        return {
            "local_block": local_block,
            "file_block": file_block,
            "pipe_block": pipe_block,
            "rewrite_block": rewrite_block,
            "pickle_block": pickle_block,
            "torch_block": torch_block,
            "stdin_available": stdin_stream is not None,
            "stdout_available": stdout_stream is not None,
        }
    finally:
        utils.enforce_security = previous_flag
        if previous_rewrite is None:
            os.environ.pop("GOPEN_REWRITE", None)
        else:
            os.environ["GOPEN_REWRITE"] = previous_rewrite


def probe_cache(workdir: Path) -> Dict[str, Any]:
    """Probe cache naming, validation, and LRU cleanup."""

    src_tar = workdir / "source.tar"
    cache_dir = workdir / "cache"
    cache_dir.mkdir()
    make_tiny_tar(src_tar)

    name_samples = {
        "http": cache.url_to_cache_name("http://example.com/path/to/file.txt"),
        "file": cache.url_to_cache_name("file:///path/to/file.txt"),
        "unknown": cache.url_to_cache_name("unknown://example.com/path/to/file.txt"),
    }
    expect_raises(AssertionError, lambda: cache.url_to_cache_name(123))

    def fake_download(url: str, dest: str, chunk_size: int = 1024**2, verbose: bool = False) -> None:
        del url, chunk_size, verbose
        shutil.copyfile(src_tar, dest)

    with patch.object(cache, "download", side_effect=fake_download):
        opener = cache.FileCache(
            cache_dir=str(cache_dir),
            validator=cache.check_tar_format,
            handler=handlers.reraise_exception,
            cache_size=0,
            url_to_name=cache.url_to_cache_name,
        )

        urls = [
            "https://example.com/shards/shard-000000.tar",
            "https://example.com/shards/shard-000001.tar",
            "https://example.com/shards/shard-000002.tar",
        ]
        cached_paths = []
        for url in urls:
            cached_paths.append(Path(opener.get_file(url)))
            time.sleep(0.05)

        before_cleanup = sorted(p.name for p in cache_dir.iterdir())
        total_before = sum(p.stat().st_size for p in cache_dir.iterdir())
        target_size = src_tar.stat().st_size + 1
        cleaner = cache.LRUCleanup(str(cache_dir), cache_size=target_size, interval=None)
        cleaner.cleanup()
        after_cleanup = sorted(p.name for p in cache_dir.iterdir())

    return {
        "name_samples": name_samples,
        "cached_paths": [str(path) for path in cached_paths],
        "before_cleanup": before_cleanup,
        "after_cleanup": after_cleanup,
        "total_before": total_before,
        "target_size": target_size,
        "verified_flat_name": all("/" not in name for name in name_samples.values()),
    }


def probe_handlers() -> Dict[str, Any]:
    """Probe the return-value contract of the basic handlers."""

    continue_ok = handlers.ignore_and_continue(RuntimeError("boom"))
    stop_ok = handlers.ignore_and_stop(RuntimeError("boom"))
    try:
        handlers.reraise_exception(RuntimeError("boom"))
    except RuntimeError:
        reraise_ok = True
    else:  # pragma: no cover - defensive
        reraise_ok = False

    return {
        "ignore_and_continue": continue_ok,
        "ignore_and_stop": stop_ok,
        "reraise_exception": reraise_ok,
    }


def run_checks(workdir: Path) -> Dict[str, Any]:
    """Run all offline probes and collect a summary."""

    return {
        "workdir": str(workdir),
        "gopen_schemes": sorted(name for name in gopen_mod.gopen_schemes.keys()),
        "local_files": probe_local_files(workdir),
        "pipe": probe_pipe(workdir),
        "secure_mode": probe_secure_mode(workdir),
        "cache": probe_cache(workdir),
        "handlers": probe_handlers(),
    }


def main() -> int:
    """Run the smoke check helper."""

    parser = argparse.ArgumentParser(description="Smoke-test WebDataset IO, caching, and security behaviors.")
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary work directory for inspection.",
    )
    args = parser.parse_args()

    if args.keep_temp:
        workdir = Path(tempfile.mkdtemp(prefix="webdataset-io-security-"))
        summary = run_checks(workdir)
        summary["kept_temp"] = True
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    with tempfile.TemporaryDirectory(prefix="webdataset-io-security-") as tmp:
        workdir = Path(tmp)
        summary = run_checks(workdir)
        summary["kept_temp"] = False
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
