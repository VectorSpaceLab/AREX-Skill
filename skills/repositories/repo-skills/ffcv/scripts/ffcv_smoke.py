#!/usr/bin/env python3
"""Run a tiny, self-contained FFCV writer/loader smoke check.

The default mode hides visible CUDA devices so a CPU smoke does not accidentally
initialize a shared GPU. Use --cuda only with a reserved compatible device.
"""
from __future__ import annotations

import argparse
import os
import tempfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a tiny FFCV .beton round trip")
    parser.add_argument("--cuda", action="store_true", help="Move the decoded batch to CUDA (requires a reserved GPU)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.cuda:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

    import numpy as np
    import torch
    from ffcv.fields import IntField
    from ffcv.fields.basics import IntDecoder
    from ffcv.loader import Loader, OrderOption
    from ffcv.transforms import ToDevice, ToTensor
    from ffcv.writer import DatasetWriter

    class TinyDataset:
        def __len__(self) -> int:
            return 8

        def __getitem__(self, index: int):
            return (index,)

    if args.cuda and not torch.cuda.is_available():
        raise SystemExit("--cuda requested, but torch.cuda.is_available() is false")

    with tempfile.TemporaryDirectory(prefix="ffcv-smoke-") as directory:
        filename = os.path.join(directory, "tiny.beton")
        DatasetWriter(filename, {"index": IntField()}, num_workers=1).from_indexed_dataset(
            TinyDataset(), chunksize=2
        )
        transforms = [IntDecoder(), ToTensor()]
        if args.cuda:
            transforms.append(ToDevice(torch.device("cuda:0"), non_blocking=True))
        loader = Loader(
            filename,
            batch_size=4,
            num_workers=1,
            order=OrderOption.SEQUENTIAL,
            drop_last=False,
            pipelines={"index": transforms},
        )
        batches = []
        for (values,) in loader:
            values = values.detach().cpu().numpy() if hasattr(values, "detach") else np.asarray(values)
            batches.append(values.reshape(-1).tolist())
        expected = [[0, 1, 2, 3], [4, 5, 6, 7]]
        if batches != expected:
            raise AssertionError(f"unexpected batches: {batches!r}")
        print("ffcv smoke passed:", batches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
