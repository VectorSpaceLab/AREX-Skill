#!/usr/bin/env python3
"""Render MMDetection3D inference demo commands without executing models.

This helper is intentionally side-effect free: it only validates arguments and
prints a shell command. It does not import mmdet3d, load configs, load
checkpoints, download weights, open a display, or touch a GPU.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from typing import Iterable, List, Optional


DEMO_SCRIPTS = {
    "lidar-det": "pcd_demo.py",
    "mono-det": "mono_det_demo.py",
    "multi-modality-det": "multi_modality_demo.py",
    "lidar-seg": "pcd_seg_demo.py",
}


COMMON_EPILOG = """
Safety notes:
  * This helper prints a command only; it never executes inference.
  * Demo CLIs are file-path workflows. For numpy.ndarray inputs, use the
    Python inferencer classes documented in ../references/api-reference.md.
  * Actual execution may need a CUDA-capable OpenMMLab environment, compatible
    sparse/CUDA ops, and a local or downloadable checkpoint.
  * On remote or no-display hosts, omit --show and keep --out-dir so JSON
    predictions can be inspected later.
"""


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                    argparse.RawDescriptionHelpFormatter):
    """Keep wrapped defaults and epilog paragraphs readable."""


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_common_options(parser: argparse.ArgumentParser,
                       *,
                       detection: bool) -> None:
    parser.add_argument(
        "--config",
        required=True,
        help="MMDetection3D config file or config path used by the demo.",
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Checkpoint file or URL. URLs may download during actual execution.",
    )
    parser.add_argument(
        "--device",
        default="cuda:0",
        help="Device argument rendered into the demo command.",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs",
        help="Output directory for predictions and visualizations.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Render --show for online visualization. Avoid on headless hosts.",
    )
    parser.add_argument(
        "--remote-no-display",
        action="store_true",
        help="Assert the target run is headless; refuses --show.",
    )
    parser.add_argument(
        "--wait-time",
        type=float,
        default=None,
        help="Optional wait time for online visualization.",
    )
    parser.add_argument(
        "--no-save-vis",
        action="store_true",
        help="Render flag to suppress saved visualization output.",
    )
    parser.add_argument(
        "--no-save-pred",
        action="store_true",
        help="Render flag to suppress saved JSON prediction output.",
    )
    parser.add_argument(
        "--print-result",
        action="store_true",
        help="Render flag to print prediction results to stdout during actual execution.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable token to place at the front of the rendered command.",
    )
    parser.add_argument(
        "--demo-root",
        default="demo",
        help="Directory containing the MMDetection3D demo scripts, usually 'demo'.",
    )
    parser.add_argument(
        "--notes",
        action="store_true",
        help="Print explanatory comments after the command.",
    )
    if detection:
        parser.add_argument(
            "--pred-score-thr",
            "--score-thr",
            dest="pred_score_thr",
            type=float,
            default=None,
            help=(
                "Detection score threshold. The rendered v1.4.x demo flag is "
                "--pred-score-thr; --score-thr is accepted as a helper alias."
            ),
        )


def add_lidar_det(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "lidar-det",
        formatter_class=HelpFormatter,
        description="Render a LiDAR/point-cloud 3D detection demo command.",
        epilog=COMMON_EPILOG,
    )
    parser.add_argument("--pcd", required=True, help="Point-cloud file path.")
    add_common_options(parser, detection=True)
    parser.set_defaults(task="lidar-det")


def add_mono_det(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "mono-det",
        formatter_class=HelpFormatter,
        description="Render a monocular 3D detection demo command.",
        epilog=COMMON_EPILOG,
    )
    parser.add_argument("--img", required=True, help="Image file path.")
    parser.add_argument(
        "--ann-file",
        "--infos",
        dest="ann_file",
        required=True,
        help=(
            "Info/annotation file with data_list and camera calibration. "
            "The image basename and cam-type key must match this file."
        ),
    )
    parser.add_argument(
        "--cam-type",
        default=None,
        help=(
            "Camera key to render, for example CAM2, CAM_FRONT, CAM_BACK, or "
            "a dataset-specific key present in the info file."
        ),
    )
    add_common_options(parser, detection=True)
    parser.set_defaults(task="mono-det")


def add_multi_modality_det(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "multi-modality-det",
        formatter_class=HelpFormatter,
        description="Render a LiDAR + image multi-modality 3D detection demo command.",
        epilog=COMMON_EPILOG,
    )
    parser.add_argument("--pcd", required=True, help="Point-cloud file path.")
    parser.add_argument(
        "--img",
        required=True,
        help="Image file path, or an image directory for validated multi-view workflows.",
    )
    parser.add_argument(
        "--ann-file",
        "--infos",
        dest="ann_file",
        required=True,
        help="Info/annotation file with data_list and camera calibration.",
    )
    parser.add_argument(
        "--cam-type",
        default=None,
        help="Camera key to render; use 'all' only when the selected config supports it.",
    )
    add_common_options(parser, detection=True)
    parser.set_defaults(task="multi-modality-det")


def add_lidar_seg(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "lidar-seg",
        formatter_class=HelpFormatter,
        description="Render a LiDAR point-cloud segmentation demo command.",
        epilog=COMMON_EPILOG,
    )
    parser.add_argument("--pcd", required=True, help="Point-cloud file path.")
    add_common_options(parser, detection=False)
    parser.set_defaults(task="lidar-seg")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=HelpFormatter,
        description=(
            "Render MMDetection3D demo commands for LiDAR detection, monocular "
            "detection, multi-modality detection, and LiDAR segmentation."
        ),
        epilog=COMMON_EPILOG,
    )
    subparsers = parser.add_subparsers(dest="task", required=True)
    add_lidar_det(subparsers)
    add_mono_det(subparsers)
    add_multi_modality_det(subparsers)
    add_lidar_seg(subparsers)
    return parser


def append_common_flags(command: List[str], args: argparse.Namespace) -> None:
    command.extend(["--device", args.device])
    if getattr(args, "pred_score_thr", None) is not None:
        command.extend(["--pred-score-thr", str(args.pred_score_thr)])
    command.extend(["--out-dir", args.out_dir])
    if args.show:
        command.append("--show")
    if args.wait_time is not None:
        command.extend(["--wait-time", str(args.wait_time)])
    if args.no_save_vis:
        command.append("--no-save-vis")
    if args.no_save_pred:
        command.append("--no-save-pred")
    if args.print_result:
        command.append("--print-result")


def render_command(args: argparse.Namespace) -> List[str]:
    script = f"{args.demo_root.rstrip('/')}/{DEMO_SCRIPTS[args.task]}"
    command: List[str] = [args.python, script]

    if args.task == "lidar-det":
        command.extend([args.pcd, args.config, args.checkpoint])
    elif args.task == "mono-det":
        command.extend([args.img, args.ann_file, args.config, args.checkpoint])
    elif args.task == "multi-modality-det":
        command.extend([args.pcd, args.img, args.ann_file, args.config, args.checkpoint])
    elif args.task == "lidar-seg":
        command.extend([args.pcd, args.config, args.checkpoint])
    else:  # pragma: no cover - argparse prevents this.
        raise ValueError(f"unknown task: {args.task}")

    append_common_flags(command, args)

    cam_type: Optional[str] = getattr(args, "cam_type", None)
    if cam_type:
        command.extend(["--cam-type", cam_type])

    return command


def collect_notes(args: argparse.Namespace) -> List[str]:
    notes: List[str] = []

    notes.append("rendered command only; no model execution has occurred")
    if args.remote_no_display:
        notes.append("remote/no-display mode selected; --show was not rendered")
    elif args.show and not os.environ.get("DISPLAY"):
        notes.append(
            "DISPLAY is not set in the current shell; actual demo execution may force --show off"
        )

    if args.no_save_vis and args.no_save_pred:
        notes.append(
            "both visualization and prediction saving are disabled; demos may ignore out-dir"
        )
    elif args.no_save_pred:
        notes.append("JSON predictions will not be saved during actual execution")

    if str(args.checkpoint).startswith(("http://", "https://")):
        notes.append("checkpoint is a URL; actual execution may perform a network download")

    if args.task in {"mono-det", "multi-modality-det"}:
        if not getattr(args, "cam_type", None):
            notes.append("no cam-type was rendered; actual demo/inferencer defaults will apply")
        notes.append("ann-file must contain data_list entries aligned with the requested sample(s)")

    if args.task == "multi-modality-det" and getattr(args, "cam_type", None) == "all":
        notes.append("cam-type 'all' requires a config/pipeline that truly supports multi-view input")

    return notes


def validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.remote_no_display and args.show:
        parser.error("--remote-no-display cannot be combined with --show")
    if args.no_save_vis and args.no_save_pred and args.out_dir:
        # Not fatal: demo scripts intentionally clear out_dir in this case.
        return


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate(args, parser)
    command = render_command(args)
    print(shell_join(command))

    if args.notes:
        for note in collect_notes(args):
            print(f"# note: {note}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
