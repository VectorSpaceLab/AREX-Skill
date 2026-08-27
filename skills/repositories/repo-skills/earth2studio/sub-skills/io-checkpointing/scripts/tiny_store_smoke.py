#!/usr/bin/env python3
"""Exercise a tiny local Earth2Studio Zarr store without network or models."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--async-zarr", action="store_true", help="also exercise AsyncZarrBackend")
    parser.add_argument("--shard-size", type=int, default=None)
    parser.add_argument("--keep", type=Path, help="optional output directory; otherwise use a temporary directory")
    args = parser.parse_args(argv)
    if args.shard_size is not None and args.shard_size < 1:
        parser.error("shard-size must be >= 1")
    try:
        from earth2studio.io import ZarrBackend
        import torch
        coords = {"time": np.array([np.datetime64("2024-01-01")]), "lead_time": np.array([np.timedelta64(0, "h"), np.timedelta64(1, "h")]), "lat": np.array([0, 1])}
        root = args.keep or Path(tempfile.mkdtemp(prefix="earth2studio-io-"))
        path = root / "tiny.zarr"
        io = ZarrBackend(str(path))
        io.add_array(coords, "t2m")
        io.write(torch.ones((1, 1, 2)), {"time": coords["time"], "lead_time": coords["lead_time"][:1], "lat": coords["lat"]}, "t2m")
        if args.async_zarr:
            from earth2studio.io import AsyncZarrBackend
            parallel = {"time": coords["time"], "lead_time": coords["lead_time"]}
            kwargs = {"chunked_coords": {"lat": 2}}
            if args.shard_size is not None: kwargs["shard_coords"] = {"lead_time": args.shard_size}
            async_io = AsyncZarrBackend(str(root / "tiny-async.zarr"), parallel_coords=parallel, **kwargs)
            async_io.add_array(coords, "t2m")
            async_io.close()
        print(f"tiny store smoke: PASS ({root})")
        return 0
    except ImportError as exc:
        print(f"required optional IO dependency missing: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
