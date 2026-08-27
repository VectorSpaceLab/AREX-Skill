#!/usr/bin/env python3
"""Print a compact Chainer runtime report.

This is a read-only health check. It does not modify the checkout or any
package state.
"""

from __future__ import annotations

import importlib.util
import sys


def _module_status(name: str) -> str:
    return "present" if importlib.util.find_spec(name) is not None else "missing"


def main() -> int:
    try:
        import chainer
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"chainer import failed: {exc}")
        return 1

    print(f"chainer {chainer.__version__}")
    print(f"cuda.available={chainer.backends.cuda.available}")
    print(f"cuda.cudnn_enabled={chainer.backends.cuda.cudnn_enabled}")
    print(f"intel64.available={chainer.backends.intel64.is_ideep_available()}")

    try:
        import chainerx
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"chainerx import failed: {exc}")
    else:
        print(f"chainerx.available={chainerx.is_available()}")

    try:
        import chainermn
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"chainermn import failed: {exc}")
    else:
        print(f"chainermn {chainermn.__version__}")

    try:
        import onnx_chainer
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"onnx_chainer import failed: {exc}")
    else:
        print(
            "onnx_chainer opset="
            f"{onnx_chainer.MINIMUM_OPSET_VERSION}-{onnx_chainer.MAXIMUM_OPSET_VERSION}"
        )

    print(f"h5py={_module_status('h5py')}")
    print(f"mpi4py={_module_status('mpi4py')}")
    print(f"onnx={_module_status('onnx')}")

    print("-- chainer.print_runtime_info() --")
    chainer.print_runtime_info()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
