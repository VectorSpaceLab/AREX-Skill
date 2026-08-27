#!/usr/bin/env python3
"""Run a bounded synthetic DeepCTR DIN/BST/DSIN sequence smoke.

This script uses only generated NumPy arrays; it does not read repository data,
write model files, or require the original DeepCTR checkout at runtime. It is
intended to verify input names, shapes, model construction, one tiny fit, and
prediction. DIEN is intentionally excluded because its custom dynamic-GRU and
negative-sampling paths are legacy/version-sensitive; use the API/reference
notes for a separately bounded DIEN check.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Tuple

# Keep a tiny smoke from claiming all host CPU threads. These must be set before
# TensorFlow is imported.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")

import numpy as np
import tensorflow as tf

# DeepCTR 0.9.4's sequence implementations include TensorFlow 1.x-compatible
# graph code. Graph mode is the conservative compatibility choice for this
# bounded check when running under TensorFlow 2.x.
if tf.executing_eagerly():
    tf.compat.v1.disable_eager_execution()

from deepctr.feature_column import (  # noqa: E402
    DenseFeat,
    SparseFeat,
    VarLenSparseFeat,
    get_feature_names,
)
from deepctr.models import BST, DIN, DSIN  # noqa: E402


ArrayDict = Dict[str, np.ndarray]


def _din_data() -> Tuple[ArrayDict, np.ndarray, List[object], List[str]]:
    """Return a three-row DIN/BST fixture with hist_ fields and seq_length."""
    feature_columns = [
        SparseFeat("user", 3, embedding_dim=4),
        SparseFeat("gender", 2, embedding_dim=2),
        SparseFeat("item_id", 4, embedding_dim=4),
        SparseFeat("cate_id", 3, embedding_dim=2),
        DenseFeat("pay_score", 1),
        VarLenSparseFeat(
            SparseFeat("hist_item_id", 4, embedding_dim=4, embedding_name="item_id"),
            maxlen=4,
            length_name="seq_length",
        ),
        VarLenSparseFeat(
            SparseFeat("hist_cate_id", 3, embedding_dim=2, embedding_name="cate_id"),
            maxlen=4,
            length_name="seq_length",
        ),
    ]
    values = {
        "user": np.array([0, 1, 2], dtype="int32"),
        "gender": np.array([0, 1, 0], dtype="int32"),
        "item_id": np.array([1, 2, 3], dtype="int32"),
        "cate_id": np.array([1, 2, 2], dtype="int32"),
        "pay_score": np.array([0.1, 0.2, 0.3], dtype="float32"),
        "hist_item_id": np.array(
            [[1, 2, 3, 0], [3, 2, 1, 0], [1, 2, 0, 0]], dtype="int32"
        ),
        "hist_cate_id": np.array(
            [[1, 2, 2, 0], [2, 2, 1, 0], [1, 2, 0, 0]], dtype="int32"
        ),
        "seq_length": np.array([3, 3, 2], dtype="int32"),
    }
    x = {name: values[name] for name in get_feature_names(feature_columns)}
    return x, np.array([1.0, 0.0, 1.0], dtype="float32"), feature_columns, [
        "item_id",
        "cate_id",
    ]


def _dsin_data() -> Tuple[ArrayDict, np.ndarray, List[object], List[str]]:
    """Return a two-session, three-row DSIN fixture with sess_length."""
    feature_columns = [
        SparseFeat("user", 3, embedding_dim=4),
        SparseFeat("gender", 2, embedding_dim=2),
        SparseFeat("item", 4, embedding_dim=4),
        SparseFeat("cate_id", 3, embedding_dim=4),
        DenseFeat("pay_score", 1),
    ]
    for index in range(2):
        feature_columns.extend(
            [
                VarLenSparseFeat(
                    SparseFeat(
                        "sess_%d_item" % index,
                        4,
                        embedding_dim=4,
                        embedding_name="item",
                    ),
                    maxlen=4,
                ),
                VarLenSparseFeat(
                    SparseFeat(
                        "sess_%d_cate_id" % index,
                        3,
                        embedding_dim=4,
                        embedding_name="cate_id",
                    ),
                    maxlen=4,
                ),
            ]
        )
    values = {
        "user": np.array([0, 1, 2], dtype="int32"),
        "gender": np.array([0, 1, 0], dtype="int32"),
        "item": np.array([1, 2, 3], dtype="int32"),
        "cate_id": np.array([1, 2, 2], dtype="int32"),
        "pay_score": np.array([0.1, 0.2, 0.3], dtype="float32"),
        "sess_0_item": np.array(
            [[1, 2, 3, 0], [3, 2, 1, 0], [0, 0, 0, 0]], dtype="int32"
        ),
        "sess_0_cate_id": np.array(
            [[1, 2, 2, 0], [2, 2, 1, 0], [0, 0, 0, 0]], dtype="int32"
        ),
        "sess_1_item": np.array(
            [[1, 2, 3, 0], [0, 0, 0, 0], [0, 0, 0, 0]], dtype="int32"
        ),
        "sess_1_cate_id": np.array(
            [[1, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0]], dtype="int32"
        ),
        "sess_length": np.array([2, 1, 0], dtype="int32"),
    }
    x = {name: values[name] for name in get_feature_names(feature_columns)}
    # DSIN creates sess_length as an additional model input rather than from a
    # VarLenSparseFeat, so add it after get_feature_names().
    x["sess_length"] = values["sess_length"]
    return x, np.array([1.0, 0.0, 1.0], dtype="float32"), feature_columns, [
        "item",
        "cate_id",
    ]


def _run_one(name: str, epochs: int, batch_size: int, verbose: int) -> Dict[str, object]:
    tf.keras.backend.clear_session()
    if name in ("din", "bst"):
        x, y, feature_columns, behavior = _din_data()
        if name == "din":
            # sigmoid avoids the Dice compatibility surface on newer TF.
            model = DIN(
                feature_columns,
                behavior,
                dnn_hidden_units=(4, 4),
                att_hidden_size=(4, 2),
                att_activation="sigmoid",
                dnn_dropout=0.0,
            )
        else:
            model = BST(
                feature_columns,
                behavior,
                transformer_num=1,
                att_head_num=2,
                dnn_hidden_units=(4, 4),
                dnn_dropout=0.0,
            )
    elif name == "dsin":
        x, y, feature_columns, behavior = _dsin_data()
        # Two 4-wide session features give hist_emb_size=8; 2*4 is valid.
        model = DSIN(
            feature_columns,
            behavior,
            sess_max_count=2,
            bias_encoding=False,
            att_embedding_size=2,
            att_head_num=4,
            dnn_hidden_units=(4, 4),
            dnn_dropout=0.0,
        )
    else:
        raise ValueError("unsupported smoke model: %s" % name)

    model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
    model.fit(x, y, batch_size=batch_size, epochs=epochs, verbose=verbose)
    prediction = np.asarray(model.predict(x, batch_size=batch_size, verbose=0))
    if prediction.shape != (len(y), 1):
        raise AssertionError("%s prediction shape is %r, expected (%d, 1)" % (name, prediction.shape, len(y)))
    if not np.isfinite(prediction).all():
        raise AssertionError("%s produced non-finite predictions" % name)
    if name != "dsin" and not ((prediction >= 0).all() and (prediction <= 1).all()):
        raise AssertionError("%s binary predictions are outside [0, 1]" % name)
    return {
        "model": name,
        "rows": int(len(y)),
        "prediction_shape": list(prediction.shape),
        "prediction_min": float(prediction.min()),
        "prediction_max": float(prediction.max()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=("din", "bst", "dsin", "all"),
        default="all",
        help="bounded model check to run (default: all; DIEN is intentionally not included)",
    )
    parser.add_argument("--epochs", type=int, default=1, help="tiny fit epochs (default: 1)")
    parser.add_argument("--batch-size", type=int, default=3, help="batch size (default: 3)")
    parser.add_argument("--verbose", type=int, choices=(0, 1, 2), default=0)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("--epochs and --batch-size must be positive")
    names = ("din", "bst", "dsin") if args.model == "all" else (args.model,)
    results = [_run_one(name, args.epochs, args.batch_size, args.verbose) for name in names]
    print(json.dumps({"status": "ok", "tensorflow": tf.__version__, "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
