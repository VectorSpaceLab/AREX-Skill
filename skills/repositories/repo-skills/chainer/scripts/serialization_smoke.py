#!/usr/bin/env python3
"""Verify Chainer's NPZ and HDF5 serialization helpers on a tiny model."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np

import chainer
import chainer.links as L
from chainer import serializers


class TinyModel(chainer.Chain):
    def __init__(self) -> None:
        super().__init__()
        with self.init_scope():
            self.l1 = L.Linear(4, 3)
        self.add_persistent("scale", np.array([1.5], dtype=np.float32))

    def __call__(self, x):
        return self.l1(x) * self.scale[0]


def _copy_model() -> TinyModel:
    return TinyModel()


def _compare_models(lhs: TinyModel, rhs: TinyModel) -> None:
    np.testing.assert_allclose(lhs.l1.W.array, rhs.l1.W.array)
    np.testing.assert_allclose(lhs.l1.b.array, rhs.l1.b.array)
    np.testing.assert_allclose(lhs.scale, rhs.scale)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=None,
                        help="Directory for the smoke artifacts")
    parser.add_argument("--skip-hdf5", action="store_true",
                        help="Only verify NPZ serialization")
    args = parser.parse_args()

    out_dir = Path(args.out_dir or tempfile.mkdtemp(prefix="chainer-serialization-smoke-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    source = TinyModel()
    npz_path = out_dir / "model.npz"
    serializers.save_npz(str(npz_path), source)
    restored = _copy_model()
    serializers.load_npz(str(npz_path), restored)
    _compare_models(source, restored)

    print(f"npz={npz_path}")

    if not args.skip_hdf5:
        try:
            import h5py  # noqa: F401
        except Exception as exc:
            print(f"hdf5 skipped: {exc}")
        else:
            h5_path = out_dir / "model.h5"
            serializers.save_hdf5(str(h5_path), source)
            restored_h5 = _copy_model()
            serializers.load_hdf5(str(h5_path), restored_h5)
            _compare_models(source, restored_h5)
            print(f"hdf5={h5_path}")

    print("serialization_ok=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
