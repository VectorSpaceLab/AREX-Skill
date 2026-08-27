#!/usr/bin/env python3
"""Safe MMAction2 inference smoke helper.

The default mode parses a local config and builds a recognizer on CPU without
loading weights. Supplying --video runs a local inference forward pass. Remote
checkpoint and media URLs are rejected so this script does not download files.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse


def _is_remote(value: Optional[str]) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ftp"}


def _package_version(dist_name: str) -> str:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return "unknown"


def _print_signatures() -> None:
    from mmaction.apis.inference import (
        detection_inference,
        inference_recognizer,
        inference_skeleton,
        init_recognizer,
        pose_inference,
    )
    from mmaction.apis.inferencers.actionrecog_inferencer import (
        ActionRecogInferencer,
    )
    from mmaction.apis.inferencers.mmaction2_inferencer import MMAction2Inferencer

    objects: Iterable[Any] = (
        init_recognizer,
        inference_recognizer,
        inference_skeleton,
        detection_inference,
        pose_inference,
        ActionRecogInferencer,
        ActionRecogInferencer.__call__,
        MMAction2Inferencer,
        MMAction2Inferencer.__call__,
    )
    print(f"mmaction2 distribution version: {_package_version('mmaction2')}")
    for obj in objects:
        owner = getattr(obj, "__qualname__", getattr(obj, "__name__", str(obj)))
        print(f"{owner}{inspect.signature(obj)}")


def _load_config(config_path: str):
    from mmengine import Config

    path = Path(config_path).expanduser()
    if _is_remote(config_path):
        raise ValueError("--config must be a local file path; remote configs are not used by this smoke helper")
    if not path.is_file():
        raise FileNotFoundError(f"config file does not exist: {path}")
    return Config.fromfile(path)


def _validate_local_optional_path(parser: argparse.ArgumentParser, flag: str, value: Optional[str]) -> None:
    if value is None:
        return
    if _is_remote(value):
        parser.error(f"{flag} must be a local path; this smoke helper never downloads remote files")


def _summarize_prediction(result: Any) -> None:
    if not hasattr(result, "pred_score"):
        print("inference completed, but result has no pred_score attribute")
        print(f"result type: {type(result).__name__}")
        return

    scores = result.pred_score
    if hasattr(scores, "detach"):
        scores = scores.detach().cpu()
        num_scores = int(scores.numel())
        k = min(5, num_scores)
        values, indices = scores.topk(k)
        pairs = list(zip(indices.tolist(), [float(x) for x in values.tolist()]))
    else:
        score_list = list(scores)
        pairs = sorted(enumerate(score_list), key=lambda item: item[1], reverse=True)[:5]
        num_scores = len(score_list)

    print(f"inference result type: {type(result).__name__}")
    print(f"pred_score length: {num_scores}")
    print("top indices and scores:")
    for class_id, score in pairs:
        print(f"  {class_id}: {score:.6f}")


def _explain_exception(exc: BaseException) -> None:
    message = str(exc)
    print(f"ERROR: {exc.__class__.__name__}: {message}", file=sys.stderr)
    lower = message.lower()
    if "decord" in lower:
        print("Hint: the selected video pipeline or visualizer requires Decord. Install decord or use a different compatible decode pipeline.", file=sys.stderr)
    if "mmdet" in lower:
        print("Hint: detection_inference is optional and requires a compatible mmdet installation.", file=sys.stderr)
    if "mmpose" in lower:
        print("Hint: pose_inference is optional and requires a compatible mmpose installation.", file=sys.stderr)
    if "cuda" in lower:
        print("Hint: retry with --device cpu unless a CUDA-enabled PyTorch/MMCV stack is verified.", file=sys.stderr)


def _build_model(cfg: Any, checkpoint: Optional[str], device: str):
    import numpy as np
    import torch
    from mmaction.apis import init_recognizer

    np.random.seed(0)
    torch.manual_seed(0)
    model = init_recognizer(cfg, checkpoint=checkpoint, device=device)
    print(f"built model: {model.__class__.__name__}")
    print(f"device requested: {device}")
    print(f"checkpoint loaded: {'yes' if checkpoint else 'no'}")
    return model


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe MMAction2 config/model/inference smoke helper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        help="Local MMAction2 config file. Required for build or inference modes.",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Optional local checkpoint path. Remote URLs are rejected to avoid downloads.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device passed to init_recognizer. CPU is the safe default.",
    )
    parser.add_argument(
        "--video",
        default=None,
        help="Optional local video path or audio .npy path passed to inference_recognizer.",
    )
    parser.add_argument(
        "--check-build-only",
        action="store_true",
        help="Parse config and build init_recognizer(checkpoint=None), ignoring --checkpoint and --video.",
    )
    parser.add_argument(
        "--print-signatures",
        action="store_true",
        help="Print verified public API signatures. Can be combined with build/inference modes.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    _validate_local_optional_path(parser, "--checkpoint", args.checkpoint)
    _validate_local_optional_path(parser, "--video", args.video)

    try:
        import mmaction  # noqa: F401
    except Exception as exc:  # pragma: no cover - diagnostic path
        _explain_exception(exc)
        return 2

    try:
        if args.print_signatures:
            _print_signatures()
            if not args.config and not args.check_build_only and not args.video:
                return 0

        if not args.config:
            parser.error("--config is required for --check-build-only or inference")

        cfg = _load_config(args.config)

        if args.check_build_only:
            if args.checkpoint:
                print("--check-build-only ignores --checkpoint to avoid loading weights")
            _build_model(cfg, checkpoint=None, device=args.device)
            print("build-only smoke passed")
            return 0

        checkpoint = args.checkpoint
        if args.video:
            video_path = Path(args.video).expanduser()
            if not video_path.exists():
                parser.error(f"--video path does not exist: {video_path}")
        elif checkpoint is None:
            print("No --video and no --checkpoint supplied; performing random-weight build smoke only.")

        model = _build_model(cfg, checkpoint=checkpoint, device=args.device)

        if args.video:
            from mmaction.apis import inference_recognizer

            if checkpoint is None:
                print("No checkpoint supplied; running inference with random weights for pipeline smoke only.")
            result = inference_recognizer(model, str(Path(args.video).expanduser()))
            _summarize_prediction(result)
            print("inference smoke passed")
        else:
            print("model build smoke passed")
        return 0
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - diagnostic path
        _explain_exception(exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
