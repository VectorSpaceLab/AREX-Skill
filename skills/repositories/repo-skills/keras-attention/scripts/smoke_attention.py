#!/usr/bin/env python3
"""Tiny self-contained smoke check for the Keras Attention Layer package.

This script intentionally avoids the original repository checkout. It validates
that the installed `attention` package can build Luong/Bahdanau TensorFlow/Keras
models, produce the expected output shape, preserve layer config, and optionally
round-trip through model save/load with custom_objects.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the installed attention package.")
    parser.add_argument(
        "--score",
        choices=["luong", "bahdanau", "both"],
        default="both",
        help="Attention score branch to test. Default: both.",
    )
    parser.add_argument("--units", type=int, default=4, help="Attention output units for the smoke model.")
    parser.add_argument("--timesteps", type=int, default=5, help="Sequence length for synthetic input.")
    parser.add_argument("--input-dim", type=int, default=2, help="Input feature width for synthetic input.")
    parser.add_argument("--lstm-units", type=int, default=3, help="Hidden units in the preceding LSTM.")
    parser.add_argument("--samples", type=int, default=4, help="Synthetic sample count.")
    parser.add_argument(
        "--save-format",
        choices=["h5", "keras"],
        default="h5",
        help="Model file format used for the save/load round trip. Default: h5.",
    )
    parser.add_argument(
        "--skip-save-load",
        action="store_true",
        help="Skip filesystem save/load round trip and only test construction/prediction/config.",
    )
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Set CUDA_VISIBLE_DEVICES='' before importing TensorFlow for CPU-only validation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    return parser.parse_args()


def scores_to_test(score: str) -> list[str]:
    return ["luong", "bahdanau"] if score == "both" else [score]


def run_one(score: str, args: argparse.Namespace) -> dict[str, object]:
    import numpy as np
    from tensorflow.keras import Input
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras.models import Model, load_model
    from attention import Attention

    rng = np.random.default_rng(7)
    x_data = rng.normal(size=(args.samples, args.timesteps, args.input_dim)).astype("float32")

    model_input = Input(shape=(args.timesteps, args.input_dim))
    x = LSTM(args.lstm_units, return_sequences=True)(model_input)
    x = Attention(units=args.units, score=score)(x)
    x = Dense(1)(x)
    model = Model(model_input, x)

    pred1 = model.predict(x_data, verbose=0)
    expected_shape = (args.samples, 1)
    if tuple(pred1.shape) != expected_shape:
        raise AssertionError(f"prediction shape {pred1.shape} != {expected_shape}")

    attention_layers = [layer for layer in model.layers if isinstance(layer, Attention)]
    if len(attention_layers) != 1:
        raise AssertionError(f"expected one Attention layer, found {len(attention_layers)}")
    attention_layer = attention_layers[0]

    config = attention_layer.get_config()
    if config.get("units") != args.units or config.get("score") != score:
        raise AssertionError(f"unexpected Attention config: {config}")

    save_load = "skipped"
    if not args.skip_save_load:
        suffix = ".h5" if args.save_format == "h5" else ".keras"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / f"attention_smoke_{score}{suffix}"
            if args.save_format == "h5":
                model.save(path, include_optimizer=False)
            else:
                # Native `.keras` format does not accept include_optimizer.
                model.save(path)
            loaded = load_model(path, custom_objects={"Attention": Attention}, compile=False)
            pred2 = loaded.predict(x_data, verbose=0)
            np.testing.assert_allclose(pred1, pred2, rtol=1e-5, atol=1e-5)
        save_load = "passed"

    return {
        "score": score,
        "prediction_shape": list(pred1.shape),
        "attention_output_shape": list(attention_layer.compute_output_shape((None, args.timesteps, args.lstm_units))),
        "config": {"units": config.get("units"), "score": config.get("score")},
        "save_load": save_load,
    }


def main() -> int:
    args = parse_args()
    if args.force_cpu:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    results = [run_one(score, args) for score in scores_to_test(args.score)]
    payload = {"status": "passed", "results": results}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Keras Attention smoke passed")
        for result in results:
            print(
                f"- {result['score']}: prediction_shape={result['prediction_shape']} "
                f"attention_output_shape={result['attention_output_shape']} "
                f"save_load={result['save_load']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
