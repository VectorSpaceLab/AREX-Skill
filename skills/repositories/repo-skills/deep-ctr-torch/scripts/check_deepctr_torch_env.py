#!/usr/bin/env python3
"""Check a Python environment for DeepCTR-Torch package use.

Default/--quick verifies import, metadata, representative API signatures, and
PyTorch CPU availability. Add --smoke to run tiny CPU training/prediction checks.
Add --cuda only when CUDA backend verification is required.
"""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import inspect
import sys
from typing import Iterable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify DeepCTR-Torch imports and optional tiny smokes.")
    parser.add_argument("--quick", action="store_true", help="Run import, metadata, signature, and torch CPU checks.")
    parser.add_argument("--smoke", action="store_true", help="Also run tiny DeepFM/DIN/MMOE CPU fit/predict checks.")
    parser.add_argument("--cuda", action="store_true", help="Also require torch.cuda.is_available() and allocate a tiny CUDA tensor.")
    parser.add_argument("--torch-threads", type=int, default=1, help="Torch intra-op threads for smoke checks. Default: 1")
    return parser


def print_signature(obj) -> None:
    print(f"{obj.__name__}{inspect.signature(obj)}")


def require_imports():
    try:
        import deepctr_torch
        from deepctr_torch.inputs import DenseFeat, SparseFeat, VarLenSparseFeat, get_feature_names
        from deepctr_torch.models import DeepFM, DIEN, DIN, ESMM, MMOE, PLE, SharedBottom
        from deepctr_torch.callbacks import EarlyStopping, ModelCheckpoint
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        if missing == "requests":
            raise SystemExit(
                "ERROR: deepctr_torch imports requests for its version check, but requests is missing. "
                "Run: python -m pip install requests"
            ) from exc
        raise SystemExit(
            f"ERROR: cannot import {missing}. Install DeepCTR-Torch and runtime dependencies in this Python."
        ) from exc
    return {
        "deepctr_torch": deepctr_torch,
        "SparseFeat": SparseFeat,
        "DenseFeat": DenseFeat,
        "VarLenSparseFeat": VarLenSparseFeat,
        "get_feature_names": get_feature_names,
        "DeepFM": DeepFM,
        "DIN": DIN,
        "DIEN": DIEN,
        "MMOE": MMOE,
        "PLE": PLE,
        "SharedBottom": SharedBottom,
        "ESMM": ESMM,
        "EarlyStopping": EarlyStopping,
        "ModelCheckpoint": ModelCheckpoint,
    }


def quick_check(symbols: dict) -> None:
    import torch

    dist_version = importlib_metadata.version("deepctr-torch")
    module_version = getattr(symbols["deepctr_torch"], "__version__", "unknown")
    print(f"deepctr-torch distribution={dist_version} module={module_version}")
    print(f"torch={torch.__version__} cuda_runtime={getattr(torch.version, 'cuda', None)}")
    for name in [
        "SparseFeat",
        "DenseFeat",
        "VarLenSparseFeat",
        "get_feature_names",
        "DeepFM",
        "DIN",
        "DIEN",
        "MMOE",
        "PLE",
        "SharedBottom",
        "ESMM",
        "EarlyStopping",
        "ModelCheckpoint",
    ]:
        print_signature(symbols[name])
    import torch.nn as nn

    tensor = torch.ones((2, 2), device="cpu")
    layer = nn.Linear(2, 1)
    out = layer(tensor)
    assert out.shape == (2, 1)
    print("cpu torch smoke=passed")


def cuda_check() -> None:
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("ERROR: --cuda requested, but torch.cuda.is_available() is False")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    print(f"cuda_device_0={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
    torch.empty((1,), device="cuda")
    print("cuda tensor smoke=passed")


def tiny_smoke(symbols: dict, torch_threads: int) -> None:
    import numpy as np
    import torch

    torch.set_num_threads(torch_threads)
    SparseFeat = symbols["SparseFeat"]
    DenseFeat = symbols["DenseFeat"]
    VarLenSparseFeat = symbols["VarLenSparseFeat"]
    DeepFM = symbols["DeepFM"]
    DIN = symbols["DIN"]
    MMOE = symbols["MMOE"]

    features = [SparseFeat("user", 4, embedding_dim=4), SparseFeat("item", 5, embedding_dim=4), DenseFeat("score", 1)]
    x = {"user": np.array([0, 1, 2, 3]), "item": np.array([1, 2, 3, 4]), "score": np.array([0.1, 0.2, 0.3, 0.4])}
    y = np.array([0, 1, 0, 1])
    model = DeepFM(features, features, dnn_hidden_units=(4,), device="cpu")
    model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
    model.fit(x, y, batch_size=2, epochs=1, verbose=0, validation_split=0.0)
    pred = model.predict(x, batch_size=2)
    assert pred.shape == (4, 1)
    print("deepfm tiny smoke=passed")

    seq_features = [
        SparseFeat("user", 3, embedding_dim=4),
        SparseFeat("item", 4, embedding_dim=4),
        VarLenSparseFeat(SparseFeat("hist_item", 4, embedding_dim=4, embedding_name="item"), maxlen=3, length_name="seq_length"),
    ]
    seq_x = {
        "user": np.array([0, 1, 2]),
        "item": np.array([1, 2, 3]),
        "hist_item": np.array([[1, 2, 0], [2, 3, 0], [1, 0, 0]]),
        "seq_length": np.array([2, 2, 1]),
    }
    din = DIN(seq_features, ["item"], dnn_hidden_units=(4,), device="cpu")
    din.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
    din.fit(seq_x, np.array([1, 0, 1]), batch_size=3, epochs=1, verbose=0, validation_split=0.0)
    assert din.predict(seq_x, batch_size=3).shape == (3, 1)
    print("din tiny smoke=passed")

    mtl_features = [SparseFeat("user", 4, embedding_dim=4), DenseFeat("duration", 1)]
    mtl_x = {"user": np.array([0, 1, 2, 3]), "duration": np.array([0.1, 0.4, 0.2, 0.8])}
    mtl_y = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
    mmoe = MMOE(mtl_features, task_types=["binary", "binary"], task_names=["finish", "like"], expert_dnn_hidden_units=(4,), tower_dnn_hidden_units=(4,), device="cpu")
    mmoe.compile("adam", ["binary_crossentropy", "binary_crossentropy"], metrics=["binary_crossentropy"])
    mmoe.fit(mtl_x, mtl_y, batch_size=2, epochs=1, verbose=0, validation_split=0.0)
    assert mmoe.predict(mtl_x, batch_size=2).shape == (4, 2)
    print("mmoe tiny smoke=passed")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.torch_threads < 1:
        raise SystemExit("ERROR: --torch-threads must be >= 1")
    symbols = require_imports()
    quick_check(symbols)
    if args.cuda:
        cuda_check()
    if args.smoke:
        tiny_smoke(symbols, args.torch_threads)
    print("deepctr_torch_env_check=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
