#!/usr/bin/env python3
"""Smoke-check WebDataset reading pipelines on a tiny local fixture.

The helper writes one tiny tar shard locally, then verifies:
- fluent `WebDataset` loading,
- explicit `DataPipeline` construction,
- `batched()` / `unbatched()` round-trips,
- optional torch DataLoader and WebLoader integration.

It never touches the original repository data and should run entirely offline.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List

EXPECTED_ROWS = [("hello", 3), ("world", 7)]
EXPECTED_TRANSFORMED = [("HELLO", 4), ("WORLD", 8)]


def normalize(value: Any) -> Any:
    """Convert loader outputs into plain Python values for comparison."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        value = value.tolist()
    if isinstance(value, tuple):
        return tuple(normalize(item) for item in value)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def collect(iterable) -> List[Any]:
    return [normalize(item) for item in iterable]


def build_fixture(tar_path: Path) -> None:
    import webdataset as wds

    with wds.TarWriter(str(tar_path), mtime=0) as sink:
        sink.write({"__key__": "sample000", "txt": "hello", "cls": 3})
        sink.write({"__key__": "sample001", "txt": "world", "cls": 7})


def fluid_pipeline(tar_path: Path, *, empty_check: bool = True):
    import webdataset as wds

    return (
        wds.WebDataset(str(tar_path), shardshuffle=False, empty_check=empty_check)
        .decode()
        .to_tuple("txt", "cls")
    )


def explicit_pipeline(tar_path: Path):
    import webdataset as wds

    return wds.DataPipeline(
        wds.SimpleShardList(str(tar_path)),
        wds.tarfile_to_samples(),
        wds.decode(),
        wds.to_tuple("txt", "cls"),
    )


def transformed_pipeline(tar_path: Path):
    import webdataset as wds

    return wds.FluidWrapper(explicit_pipeline(tar_path)).map_tuple(str.upper, lambda n: n + 1)


def record(summary: Dict[str, Any], name: str, func: Callable[[], Any]) -> None:
    try:
        result = func()
        status = result.get("status", "ok") if isinstance(result, dict) else "ok"
        summary["checks"][name] = {"status": status, "result": result}
    except Exception as exc:  # pragma: no cover - surfaced in JSON output
        summary["ok"] = False
        summary["checks"][name] = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }


def check_fluid(tar_path: Path) -> Dict[str, Any]:
    rows = collect(fluid_pipeline(tar_path))
    if rows != EXPECTED_ROWS:
        raise AssertionError(f"fluid rows mismatch: {rows!r}")
    return {"rows": rows}


def check_explicit(tar_path: Path) -> Dict[str, Any]:
    rows = collect(explicit_pipeline(tar_path))
    if rows != EXPECTED_ROWS:
        raise AssertionError(f"explicit rows mismatch: {rows!r}")
    return {"rows": rows}


def check_batch_roundtrip(tar_path: Path) -> Dict[str, Any]:
    rows = collect(transformed_pipeline(tar_path))
    if rows != EXPECTED_TRANSFORMED:
        raise AssertionError(f"transformed rows mismatch: {rows!r}")

    batch = normalize(next(iter(transformed_pipeline(tar_path).batched(2))))
    if batch != (["HELLO", "WORLD"], [4, 8]):
        raise AssertionError(f"batched output mismatch: {batch!r}")

    roundtrip = collect(transformed_pipeline(tar_path).batched(2).unbatched())
    if roundtrip != EXPECTED_TRANSFORMED:
        raise AssertionError(f"unbatched output mismatch: {roundtrip!r}")

    return {"rows": rows, "batch": batch, "roundtrip": roundtrip}


def check_torch_loader(tar_path: Path, workers: int) -> Dict[str, Any]:
    try:
        import torch
    except Exception as exc:
        return {"status": "skipped", "reason": f"torch unavailable: {exc}"}

    dataset = fluid_pipeline(tar_path, empty_check=False)
    loader = torch.utils.data.DataLoader(dataset, num_workers=workers, batch_size=None)
    rows = collect(loader)
    expected = [list(row) for row in EXPECTED_ROWS]
    if rows != expected:
        raise AssertionError(f"torch DataLoader rows mismatch: {rows!r}")
    return {"rows": rows, "workers": workers}


def check_webloader(tar_path: Path, workers: int) -> Dict[str, Any]:
    try:
        import webdataset as wds
    except Exception as exc:
        return {"status": "skipped", "reason": f"webdataset unavailable: {exc}"}

    dataset = fluid_pipeline(tar_path, empty_check=False)
    loader = wds.WebLoader(dataset, num_workers=workers, batch_size=2, shuffle=False).unbatched()
    rows = collect(loader)
    if rows != EXPECTED_ROWS:
        raise AssertionError(f"WebLoader rows mismatch: {rows!r}")
    return {"rows": rows, "workers": workers}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=2, help="Number of worker processes for loader checks.")
    args = parser.parse_args(argv)

    summary: Dict[str, Any] = {"ok": True, "checks": {}, "workers": args.workers}

    with tempfile.TemporaryDirectory(prefix="wds-reading-smoke-") as tmpdir:
        tar_path = Path(tmpdir) / "tiny.tar"
        build_fixture(tar_path)
        summary["fixture"] = str(tar_path)

        record(summary, "fluid_webdataset", lambda: check_fluid(tar_path))
        record(summary, "explicit_pipeline", lambda: check_explicit(tar_path))
        record(summary, "batched_roundtrip", lambda: check_batch_roundtrip(tar_path))
        record(summary, "torch_loader", lambda: check_torch_loader(tar_path, args.workers))
        record(summary, "webloader", lambda: check_webloader(tar_path, args.workers))

    for check in summary["checks"].values():
        if check["status"] == "failed":
            summary["ok"] = False

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
