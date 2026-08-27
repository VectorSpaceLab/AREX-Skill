#!/usr/bin/env python
"""Tiny Dask Array smoke check for the array-workflows skill."""

from __future__ import annotations

import argparse


def run_smoke() -> None:
    import numpy as np
    import dask.array as da

    source = np.arange(36, dtype=np.int64).reshape(6, 6)
    x = da.from_array(source, chunks=(3, 2))
    assert x.shape == (6, 6)
    assert x.chunks == ((3, 3), (2, 2, 2))

    y = x.map_blocks(lambda block: block + 1, dtype=x.dtype)
    np.testing.assert_array_equal(y[:2, :3].compute(), source[:2, :3] + 1)

    overlapped = x.map_overlap(lambda block: block, depth={0: 1, 1: 1}, boundary="reflect")
    assert overlapped.chunks == x.chunks
    np.testing.assert_array_equal(overlapped.compute(), source)

    rechunked = x.rechunk((2, 3))
    assert rechunked.chunks == ((2, 2, 2), (3, 3))
    assert int(rechunked.sum().compute()) == int(source.sum())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny fixture-free Dask Array smoke check.")
    parser.parse_args()
    run_smoke()
    print("Dask Array smoke check passed")


if __name__ == "__main__":
    main()
