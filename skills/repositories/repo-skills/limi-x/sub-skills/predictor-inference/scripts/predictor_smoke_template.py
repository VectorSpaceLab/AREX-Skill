#!/usr/bin/env python3
"""Safe LimiX predictor smoke/template helper.

Default behavior validates imports, an optional local config JSON, optional local
model-path existence, and tiny deterministic data fixture shapes. It never
attempts to download a model. It constructs LimiXPredictor and calls predict()
only when --run-inference is supplied together with a local --model-path and
--config.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a LimiXPredictor environment/config/data fixture safely. "
            "Full inference runs only with --run-inference plus --model-path and --config."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Path to an importable LimiX checkout/package root.")
    parser.add_argument("--config", type=Path, default=None, help="Local inference config JSON to validate/use.")
    parser.add_argument("--model-path", type=Path, default=None, help="Local LimiX checkpoint path. Never downloaded by this script.")
    parser.add_argument("--task", choices=["Classification", "Regression"], default="Classification", help="Task type for the tiny fixture.")
    parser.add_argument("--device", default="auto", help="torch device string: auto, cpu, cuda, cuda:0, ...")
    parser.add_argument("--run-inference", action="store_true", help="Actually instantiate LimiXPredictor and call predict().")
    parser.add_argument("--mask-prediction", action="store_true", help="Enable mask_prediction and add NaNs to the tiny test fixture.")
    parser.add_argument("--no-mix-precision", action="store_true", help="Disable mixed precision even on CUDA.")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic fixture seed.")
    parser.add_argument("--n-train", type=int, default=12, help="Tiny fixture training rows.")
    parser.add_argument("--n-test", type=int, default=5, help="Tiny fixture test rows.")
    parser.add_argument("--n-features", type=int, default=6, help="Tiny fixture feature columns.")
    parser.add_argument("--include-object-column", action="store_true", help="Use one object/string-like feature column in the fixture.")
    return parser.parse_args()


def load_config(path: Path | None) -> tuple[list[dict[str, Any]] | None, list[str]]:
    messages: list[str] = []
    if path is None:
        messages.append("No --config supplied; config validation skipped.")
        return None, messages
    if not path.is_file():
        raise FileNotFoundError(f"Config path does not exist or is not a file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, list) or not config:
        raise ValueError("Config JSON must be a non-empty list of pipeline dictionaries.")
    for idx, item in enumerate(config):
        if not isinstance(item, dict):
            raise ValueError(f"Config item {idx} is not a dictionary.")
        if "retrieval_config" not in item or not isinstance(item["retrieval_config"], dict):
            raise ValueError(f"Config item {idx} lacks a retrieval_config dictionary.")
    retrieval = bool(config[0]["retrieval_config"].get("use_retrieval", False))
    messages.append(f"Config OK: {len(config)} pipeline(s); first use_retrieval={retrieval}.")
    return config, messages


def build_fixture(args: argparse.Namespace):
    import numpy as np

    if args.n_train <= 1 or args.n_test <= 0 or args.n_features <= 0:
        raise ValueError("Require --n-train > 1, --n-test > 0, and --n-features > 0.")

    rng = np.random.default_rng(args.seed)
    base_x_train = rng.normal(size=(args.n_train, args.n_features)).astype(np.float32)
    base_x_test = rng.normal(size=(args.n_test, args.n_features)).astype(np.float32)
    x_train = base_x_train.copy()
    x_test = base_x_test.copy()

    if args.include_object_column:
        train_obj = x_train.astype(object)
        test_obj = x_test.astype(object)
        train_obj[:, 0] = np.where(np.arange(args.n_train) % 2 == 0, "group_a", "group_b")
        test_obj[:, 0] = np.where(np.arange(args.n_test) % 2 == 0, "group_a", "group_b")
        x_train, x_test = train_obj, test_obj

    if args.task == "Classification":
        y_train = (np.arange(args.n_train) % 2).astype(np.int64)
    else:
        weights = np.linspace(0.5, 1.5, args.n_features, dtype=np.float32)
        y_train = (base_x_train @ weights + rng.normal(0, 0.01, size=args.n_train)).astype(np.float32)

    if args.mask_prediction:
        x_test = x_test.copy()
        # Keep at least one observed value in every column for the tiny fixture.
        mask = rng.random(size=x_test.shape) < 0.2
        if mask.size:
            mask[0, :] = False
        x_test = x_test.astype(object if args.include_object_column else np.float32)
        for row, col in zip(*np.where(mask)):
            x_test[row, col] = np.nan

    return x_train, y_train, x_test


def validate_imports(repo_root: Path) -> tuple[type[Any] | None, list[str]]:
    messages: list[str] = []
    repo_root = repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    for module_name in ["numpy", "pandas", "sklearn", "torch"]:
        try:
            importlib.import_module(module_name)
            messages.append(f"Import OK: {module_name}")
        except Exception as exc:  # pragma: no cover - diagnostic helper
            messages.append(f"Import FAIL: {module_name}: {type(exc).__name__}: {exc}")

    try:
        module = importlib.import_module("inference.predictor")
        predictor_cls = getattr(module, "LimiXPredictor")
        messages.append(f"Import OK: inference.predictor.LimiXPredictor")
        messages.append(f"Constructor signature: {inspect.signature(predictor_cls.__init__)}")
        messages.append(f"Predict signature: {inspect.signature(predictor_cls.predict)}")
        return predictor_cls, messages
    except Exception as exc:  # pragma: no cover - diagnostic helper
        messages.append(f"Import FAIL: inference.predictor.LimiXPredictor: {type(exc).__name__}: {exc}")
        return None, messages


def choose_device(device_request: str):
    import torch

    if device_request == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    return torch.device(device_request)


def summarize_output(output: Any) -> str:
    if isinstance(output, tuple):
        parts = [summarize_output(part) for part in output]
        return "tuple(" + ", ".join(parts) + ")"
    shape = getattr(output, "shape", None)
    type_name = type(output).__name__
    return f"{type_name}(shape={shape})"


def main() -> int:
    args = parse_args()

    config, config_messages = load_config(args.config)
    for message in config_messages:
        print(message)

    if args.model_path is None:
        print("No --model-path supplied; checkpoint existence validation skipped.")
    elif args.model_path.is_file():
        print(f"Model path OK: {args.model_path}")
    else:
        raise FileNotFoundError(f"Model path does not exist or is not a file: {args.model_path}")

    device = None
    try:
        device = choose_device(args.device)
        print(f"Selected device: {device}")
        if config is not None and device.type == "cpu" and bool(config[0]["retrieval_config"].get("use_retrieval", False)):
            raise ValueError("CPU device cannot use a retrieval config; choose a *_noretrieval config or a CUDA device.")
    except Exception as exc:
        print(f"Device validation unavailable: {type(exc).__name__}: {exc}")

    x_train, y_train, x_test = build_fixture(args)
    print(f"Fixture OK: x_train={x_train.shape}, y_train={y_train.shape}, x_test={x_test.shape}, task={args.task}")
    print(f"Fixture dtypes: x_train={getattr(x_train, 'dtype', None)}, y_train={getattr(y_train, 'dtype', None)}, x_test={getattr(x_test, 'dtype', None)}")

    predictor_cls, import_messages = validate_imports(args.repo_root)
    for message in import_messages:
        print(message)

    if not args.run_inference:
        print("Dry run complete. To run full inference, rerun with --run-inference, --model-path, and --config.")
        return 0

    if predictor_cls is None:
        raise RuntimeError("Cannot run inference because LimiXPredictor import failed.")
    if args.model_path is None:
        raise ValueError("--run-inference requires --model-path.")
    if config is None:
        raise ValueError("--run-inference requires --config.")
    if device is None:
        raise RuntimeError("Cannot run inference because device selection failed.")

    predictor = predictor_cls(
        device=device,
        model_path=str(args.model_path),
        inference_config=config,
        mix_precision=(device.type == "cuda" and not args.no_mix_precision),
        mask_prediction=args.mask_prediction,
        seed=args.seed,
    )
    output = predictor.predict(x_train, y_train, x_test, task_type=args.task)
    print(f"Inference output: {summarize_output(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
