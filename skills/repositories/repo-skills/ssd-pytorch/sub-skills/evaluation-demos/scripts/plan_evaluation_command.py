#!/usr/bin/env python3
"""Print safe ssd.pytorch eval/test command templates without executing them."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List


EVAL_DEFAULT_WEIGHT = "weights/ssd300_mAP_77.43_v2.pth"
TEST_DEFAULT_WEIGHT = "weights/ssd_300_VOC0712.pth"
DEFAULT_VOC_ROOT = "<VOCDEVKIT_ROOT>/"


def bool_token(value: str) -> str:
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return "true"
    if text in {"0", "false", "f", "no", "n"}:
        return "false"
    raise argparse.ArgumentTypeError("expected true or false")


def quote_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def maybe_trailing_separator(path_text: str) -> str:
    if not path_text:
        return path_text
    if path_text.endswith(("/", "\\", ">")):
        return path_text
    return path_text + "/"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a reviewed ssd.pytorch eval.py or test.py command template. "
            "No repository script is executed."
        )
    )
    parser.add_argument("--mode", choices=("eval", "test"), required=True)
    parser.add_argument("--trained-model", default=None, help="Path to SSD300 VOC .pth weights")
    parser.add_argument("--voc-root", default=DEFAULT_VOC_ROOT, help="VOCdevkit root, preferably with trailing separator")
    parser.add_argument("--save-folder", default="eval/", help="Output folder template")
    parser.add_argument("--cuda", type=bool_token, default="false", help="true or false")
    parser.add_argument("--confidence-threshold", type=float, default=0.01, help="eval.py confidence threshold")
    parser.add_argument("--top-k", type=int, default=5, help="eval.py top_k parser value")
    parser.add_argument("--visual-threshold", type=float, default=0.6, help="test.py visual threshold")
    parser.add_argument("--cleanup", type=bool_token, default="true", help="eval.py cleanup parser value")
    return parser


def eval_plan(args: argparse.Namespace) -> tuple[List[str], List[str], List[str]]:
    weight = args.trained_model or EVAL_DEFAULT_WEIGHT
    voc_root = maybe_trailing_separator(args.voc_root)
    command = [
        "python",
        "eval.py",
        "--trained_model",
        weight,
        "--voc_root",
        voc_root,
        "--save_folder",
        args.save_folder,
        "--cuda",
        args.cuda,
        "--confidence_threshold",
        str(args.confidence_threshold),
        "--top_k",
        str(args.top_k),
        "--cleanup",
        args.cleanup,
    ]
    requirements = [
        "VOC2007 test split under the VOCdevkit root",
        "compatible SSD300 VOC trained_model state_dict",
        "PyTorch, NumPy, OpenCV, and repository imports available",
        "model-forward compatibility for the legacy Detect layer",
    ]
    warnings = [
        "Full mAP is not reproducible without VOC2007 test data and compatible weights.",
        "eval.py creates --save_folder, but primary artifacts are also written under ssd300_120000/test and VOC2007/results.",
        "--cleanup is exposed by the parser; observed source does not rely on it for automatic result deletion.",
    ]
    if args.top_k < 5:
        warnings.append("Small --top-k values can hide detections and are risky for recall-oriented AP evaluation.")
    if args.confidence_threshold > 0.05:
        warnings.append("High confidence thresholds can reduce recall and depress mAP.")
    return command, requirements, warnings


def test_plan(args: argparse.Namespace) -> tuple[List[str], List[str], List[str]]:
    weight = args.trained_model or TEST_DEFAULT_WEIGHT
    voc_root = maybe_trailing_separator(args.voc_root)
    save_folder = maybe_trailing_separator(args.save_folder)
    command = [
        "python",
        "test.py",
        "--trained_model",
        weight,
        "--voc_root",
        voc_root,
        "--save_folder",
        save_folder,
        "--visual_threshold",
        str(args.visual_threshold),
        "--cuda",
        args.cuda,
    ]
    requirements = [
        "VOC2007 test split under the VOCdevkit root",
        "compatible SSD300 VOC trained_model state_dict",
        "PyTorch, TorchVision/PIL, OpenCV, NumPy, and repository imports available",
        "model-forward compatibility for the legacy Detect layer",
    ]
    warnings = [
        "test.py writes qualitative eval/test1.txt-style output, not mAP.",
        "test.py appends to test1.txt; delete or rotate old output before a fresh run.",
        "test.py uses legacy argparse type=bool, so strings such as 'false' may parse as true in unmodified code.",
        "The observed prediction loop uses a hardcoded 0.6 threshold even though --visual_threshold is exposed.",
    ]
    if save_folder != args.save_folder:
        warnings.append("A trailing separator was added to --save-folder because test.py concatenates save_folder + 'test1.txt'.")
    return command, requirements, warnings


def print_plan(mode: str, command: List[str], requirements: List[str], warnings: List[str]) -> None:
    print(f"Mode: {mode}")
    print("Command template:")
    print("  " + quote_join(command))
    print("\nRequirements before execution:")
    for item in requirements:
        print(f"  - {item}")
    print("\nWarnings and legacy caveats:")
    for item in warnings:
        print(f"  - {item}")
    print("\nNo command was executed.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "eval":
        command, requirements, warnings = eval_plan(args)
    else:
        command, requirements, warnings = test_plan(args)
    print_plan(args.mode, command, requirements, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
