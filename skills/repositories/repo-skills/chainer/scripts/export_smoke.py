#!/usr/bin/env python3
"""Export a tiny model to ONNX and/or Caffe and verify the outputs."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np

import chainer
import chainer.functions as F
import chainer.links as L
from chainer.exporters import caffe
from onnx_chainer import export_testcase


class TinyModel(chainer.Chain):
    def __init__(self) -> None:
        super().__init__()
        with self.init_scope():
            self.l1 = L.Linear(4, 3)
            self.l2 = L.Linear(3, 2)

    def __call__(self, x):
        return self.l2(F.relu(self.l1(x)))


def _build_inputs():
    x = np.zeros((1, 4), dtype=np.float32)
    return x, chainer.Variable(x.copy())


def _export_onnx(model: TinyModel, x: np.ndarray, out_dir: Path) -> None:
    export_testcase(model, (x,), str(out_dir))
    onnx_path = out_dir / "model.onnx"
    try:
        import onnx
    except Exception as exc:
        raise SystemExit(f"onnx export wrote {onnx_path} but onnx import failed: {exc}")
    onnx.checker.check_model(onnx.load(str(onnx_path)))
    print(f"onnx={onnx_path}")


def _export_caffe(model: TinyModel, x_var: chainer.Variable, out_dir: Path) -> None:
    caffe.export(model, [x_var], str(out_dir))
    prototxt = out_dir / "chainer_model.prototxt"
    caffemodel = out_dir / "chainer_model.caffemodel"
    if not prototxt.exists() or not caffemodel.exists():
        raise SystemExit("caffe export did not create the expected output files")
    print(f"caffe={prototxt}")
    print(f"caffemodel={caffemodel}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("onnx", "caffe", "both"),
        default="both",
        help="Which export path to exercise",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory for the export artifacts",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir or tempfile.mkdtemp(prefix="chainer-export-smoke-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    model = TinyModel()
    x, x_var = _build_inputs()

    if args.format in ("onnx", "both"):
        onnx_dir = out_dir / "onnx"
        onnx_dir.mkdir(parents=True, exist_ok=True)
        _export_onnx(model, x, onnx_dir)

    if args.format in ("caffe", "both"):
        caffe_dir = out_dir / "caffe"
        caffe_dir.mkdir(parents=True, exist_ok=True)
        _export_caffe(model, x_var, caffe_dir)

    print(f"output_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
