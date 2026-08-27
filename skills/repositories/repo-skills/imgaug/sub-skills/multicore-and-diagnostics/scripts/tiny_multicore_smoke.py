#!/usr/bin/env python3
"""Tiny, bounded smoke for imgaug batch and explicit pool behavior.

The default uses one worker and three tiny batches. It does not open a GUI or
start an unbounded background loader. Use it before scaling to
``augment_batches(..., background=True)`` or ``BackgroundAugmenter``.

Example:
    python sub-skills/multicore-and-diagnostics/scripts/tiny_multicore_smoke.py
"""

from __future__ import annotations

import numpy as np


def main() -> int:
    import imgaug.augmenters as iaa
    from imgaug.augmentables.batches import UnnormalizedBatch

    seq = iaa.Sequential([iaa.Fliplr(0.5), iaa.Add(1)])
    batches = [
        UnnormalizedBatch(images=np.zeros((2, 8, 8, 3), dtype=np.uint8), data={"index": i})
        for i in range(3)
    ]

    synchronous = list(seq.augment_batches(batches, background=False))
    assert len(synchronous) == 3
    assert synchronous[0].images_aug is not None

    with seq.pool(processes=1, seed=1) as pool:
        mapped = pool.map_batches(batches, chunksize=1)
        assert len(mapped) == 3
        assert mapped[0].images_aug is not None
        assert mapped[0].data["index"] == 0

        streamed = list(pool.imap_batches((batch for batch in batches), chunksize=1))
        assert len(streamed) == 3
        assert streamed[0].images_aug is not None

    print("multicore pool smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
