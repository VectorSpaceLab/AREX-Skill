#!/usr/bin/env python3
"""Run a tiny TorchGeo GeoDataset and RandomPatchSampler smoke test.

This script creates an in-memory custom GeoDataset with one rectangular footprint.
It does not read or download external data.
"""

from __future__ import annotations

from datetime import datetime

import geopandas as gpd
import pandas as pd
import shapely
import torch

from torchgeo.datasets import GeoDataset
from torchgeo.datasets.utils import GeoSlice, Sample
from torchgeo.samplers import RandomPatchSampler


class TinyGeoDataset(GeoDataset):
    """Small in-memory GeoDataset for sampler verification."""

    def __init__(self) -> None:
        interval = pd.Interval(datetime(2020, 1, 1), datetime(2020, 12, 31), closed='both')
        self.index = gpd.GeoDataFrame(
            {'geometry': [shapely.box(0, 0, 64, 64)]},
            index=pd.IntervalIndex([interval], name='datetime'),
            crs='EPSG:3857',
        )
        self._res = (1.0, 1.0)

    @property
    def crs(self):  # noqa: ANN201 - mirrors TorchGeo dataset API
        return self.index.crs

    @property
    def res(self) -> tuple[float, float]:
        return self._res

    def __getitem__(self, query: GeoSlice) -> Sample:
        x, y, _t = query
        width = int(round((x.stop - x.start) / self.res[0]))
        height = int(round((y.stop - y.start) / self.res[1]))
        return {'image': torch.zeros(3, height, width), 'crs': self.crs, 'bounds': query}


def main() -> int:
    """Construct a dataset, draw one patch, and validate sample shape."""
    dataset = TinyGeoDataset()
    sampler = RandomPatchSampler(dataset, size=16, length=1)
    query = next(iter(sampler))
    sample = dataset[query]
    assert sample['image'].shape == (3, 16, 16), sample['image'].shape
    print('ok', query, tuple(sample['image'].shape))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
