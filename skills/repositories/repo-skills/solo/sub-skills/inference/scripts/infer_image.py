#!/usr/bin/env python3
"""Run one explicit, local SOLO/MMDetection inference and save an image.

This helper intentionally imports the legacy package only after validating its
CLI inputs. It does not locate files relative to a source checkout, download
anything, open a GUI window, or mutate a config/checkpoint.
"""

import argparse
import os
import sys
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run one local SOLO/MMDetection image inference.")
    parser.add_argument("--config", required=True, help="local model config")
    parser.add_argument(
        "--checkpoint", required=True, help="local model checkpoint")
    parser.add_argument("--image", required=True, help="local input image")
    parser.add_argument(
        "--output", required=True, help="path for the saved visualization")
    parser.add_argument(
        "--device",
        default="cuda:0",
        help="model device, for example cuda:0 or cpu (default: cuda:0)")
    parser.add_argument(
        "--score-thr",
        type=float,
        default=0.3,
        help="visualization score threshold in [0, 1] (default: 0.3)")
    parser.add_argument(
        "--visualizer",
        choices=("auto", "detection", "instance"),
        default="auto",
        help="result renderer; auto detects SOLO-style instance output")
    parser.add_argument(
        "--sort-by-density",
        action="store_true",
        help="sort SOLO instance masks by density before rendering")
    return parser


def _require_file(value, label):
    path = Path(value).expanduser()
    if not path.is_file():
        raise SystemExit("{} does not exist or is not a file: {}".format(
            label, path))
    return path.resolve()


def _validate_device(device):
    if device == "cpu":
        return
    if not device.startswith("cuda"):
        raise SystemExit(
            "Unsupported device {!r}; use 'cpu' or an explicit 'cuda:N'.".format(
                device))
    if device != "cuda" and not device.startswith("cuda:"):
        raise SystemExit(
            "Use an explicit CUDA device such as 'cuda:0', not {!r}.".format(
                device))
    try:
        import torch
    except Exception as exc:
        raise SystemExit(
            "Cannot validate {} because PyTorch is unavailable: {}".format(
                device, exc))
    if not torch.cuda.is_available():
        raise SystemExit(
            "Requested {} but torch.cuda.is_available() is false. Install or "
            "activate a compatible CUDA/PyTorch environment; this helper "
            "does not fall back to CPU automatically.".format(device))
    if device != "cuda":
        try:
            index = int(device.split(":", 1)[1])
        except (IndexError, ValueError):
            raise SystemExit(
                "CUDA device must have a numeric index, for example cuda:0.")
        count = torch.cuda.device_count()
        if index < 0 or index >= count:
            raise SystemExit(
                "Requested {} but only {} CUDA device(s) are visible.".format(
                    device, count))


def _looks_like_solo_result(result):
    """Recognize the one-image SOLO tuple without importing implementation code."""
    if not isinstance(result, (list, tuple)) or len(result) != 1:
        return False
    item = result[0]
    if item is None:
        return True
    return (isinstance(item, (list, tuple)) and len(item) == 3 and
            all(hasattr(value, "cpu") for value in item))


def _is_empty_result(result):
    if result is None:
        return True
    return isinstance(result, (list, tuple)) and len(result) == 1 and result[0] is None


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not 0.0 <= args.score_thr <= 1.0:
        raise SystemExit("--score-thr must be between 0 and 1.")

    config = _require_file(args.config, "config")
    checkpoint = _require_file(args.checkpoint, "checkpoint")
    image = _require_file(args.image, "image")
    output = Path(args.output).expanduser()
    if output.exists() and output.resolve() == image:
        raise SystemExit("--output must not overwrite --image.")
    if not output.parent.is_dir():
        raise SystemExit(
            "Output directory does not exist; create it explicitly first: {}".format(
                output.parent))
    if output.exists() and not os.access(str(output), os.W_OK):
        raise SystemExit("Output is not writable: {}".format(output))
    if not os.access(str(output.parent), os.W_OK):
        raise SystemExit("Output directory is not writable: {}".format(
            output.parent))

    _validate_device(args.device)
    try:
        from mmdet.apis import (inference_detector, init_detector,
                                 show_result, show_result_ins)
    except Exception as exc:
        raise SystemExit(
            "Cannot import the legacy SOLO/MMDetection inference API. Verify "
            "PyTorch, mmcv==0.2.16, pycocotools, SciPy/OpenCV, and the "
            "installed package environment. Original error: {}".format(exc))

    try:
        model = init_detector(str(config), str(checkpoint), device=args.device)
        result = inference_detector(model, str(image))
        visualizer = args.visualizer
        if visualizer == "auto":
            visualizer = ("instance" if _looks_like_solo_result(result)
                          else "detection")
        if visualizer == "instance":
            if _is_empty_result(result):
                # Legacy show_result_ins returns the untouched image without
                # writing out_file for [None]; preserve a useful artifact.
                import mmcv
                mmcv.imwrite(mmcv.imread(str(image)), str(output))
                print("No instances passed the model filters; saved the "
                      "unmodified input image.")
            else:
                show_result_ins(
                    str(image),
                    result,
                    model.CLASSES,
                    score_thr=args.score_thr,
                    sort_by_density=args.sort_by_density,
                    out_file=str(output))
        else:
            show_result(
                str(image),
                result,
                model.CLASSES,
                score_thr=args.score_thr,
                show=False,
                out_file=str(output))
    except Exception as exc:
        raise SystemExit(
            "Inference failed after model initialization. Check config and "
            "checkpoint family, image format, device, and compiled custom "
            "ops. Original error: {}".format(exc))

    if not output.is_file():
        raise SystemExit(
            "The renderer returned without creating the requested output: {}".format(
                output))
    print("Saved {} visualization using the {} renderer.".format(
        output, visualizer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
