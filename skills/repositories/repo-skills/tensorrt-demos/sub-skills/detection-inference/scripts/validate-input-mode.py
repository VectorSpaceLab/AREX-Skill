#!/usr/bin/env python3
"""Validate detector/input arguments without opening files or devices.

This checker intentionally uses only Python's standard library. It does not
import the repository, inspect paths, open a camera, read an image/video, load
GStreamer, initialize CUDA, or deserialize TensorRT.
"""

from __future__ import annotations

import argparse
import re
import sys


SSD_MODELS = {
    "ssd_mobilenet_v1_coco",
    "ssd_mobilenet_v1_egohands",
    "ssd_mobilenet_v2_coco",
    "ssd_mobilenet_v2_egohands",
    "ssd_inception_v2_coco",
    "ssdlite_mobilenet_v2_coco",
}
YOLO_MODEL_RE = re.compile(r"^yolov[34].*-\d+(?:x\d+)?$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate TensorRT detection input arguments only; no files, "
            "devices, plugins, or CUDA resources are accessed."
        )
    )
    parser.add_argument("--detector", choices=("yolo", "ssd"), required=True)
    parser.add_argument(
        "--model", required=True,
        help="YOLOv3/YOLOv4 model name with dimensions, or a supported SSD name",
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--image", metavar="FILE")
    inputs.add_argument("--video", metavar="FILE")
    inputs.add_argument("--rtsp", metavar="URI")
    inputs.add_argument("--usb", metavar="N", type=int)
    inputs.add_argument("--gstr", metavar="PIPELINE")
    inputs.add_argument("--onboard", metavar="N", type=int)
    parser.add_argument("--video_looping", action="store_true")
    parser.add_argument("--rtsp_latency", type=int, default=200, metavar="MS")
    parser.add_argument("--copy_frame", action="store_true")
    parser.add_argument("--do_resize", action="store_true")
    parser.add_argument("--width", type=int, default=640, metavar="PX")
    parser.add_argument("--height", type=int, default=480, metavar="PX")
    parser.add_argument("--category_num", type=int, default=80, metavar="N")
    parser.add_argument("--conf_thresh", type=float, default=0.3, metavar="T")
    parser.add_argument("--letter_box", action="store_true")
    parser.add_argument("--mjpeg_port", type=int, metavar="PORT")
    return parser


def validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    if args.detector == "ssd":
        if args.model not in SSD_MODELS:
            parser.error(
                "SSD model must be one of: " + ", ".join(sorted(SSD_MODELS))
            )
        if args.letter_box:
            parser.error("--letter_box is a YOLO option, not an SSD option")
        if args.category_num != 80:
            parser.error("--category_num is not a native SSD option")
        if args.conf_thresh != 0.3:
            parser.error("--conf_thresh is not a native SSD CLI option for SSD")
        if args.mjpeg_port is not None:
            parser.error("--mjpeg_port is only valid for the YOLO MJPEG entrypoint")
    else:
        if not YOLO_MODEL_RE.fullmatch(args.model):
            parser.error(
                "YOLO model must start with yolov3 or yolov4 and end with "
                "a dimension such as 416 or 416x256"
            )

    if args.width <= 0 or args.height <= 0:
        parser.error("--width and --height must be positive")
    if args.rtsp_latency < 0:
        parser.error("--rtsp_latency must be non-negative")
    if args.category_num <= 0:
        parser.error("--category_num must be positive")
    if not 0.0 <= args.conf_thresh <= 1.0:
        parser.error("--conf_thresh must be between 0 and 1")
    if args.usb is not None and args.usb < 0:
        parser.error("--usb must be a non-negative device id")
    if args.onboard is not None and args.onboard < 0:
        parser.error("--onboard must be a non-negative camera id")
    if args.video_looping and args.video is None:
        parser.error("--video_looping requires --video")
    if args.mjpeg_port is not None and not 1 <= args.mjpeg_port <= 65535:
        parser.error("--mjpeg_port must be between 1 and 65535")

    modes = ("image", "video", "rtsp", "usb", "gstr", "onboard")
    selected = next(mode for mode in modes if getattr(args, mode) is not None)
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    mode = validate(args, parser)
    print(
        "valid arguments: detector={} model={} input={} width={} height={}".format(
            args.detector, args.model, mode, args.width, args.height
        )
    )
    print(
        "no files, devices, TensorRT plugins, GStreamer pipelines, or CUDA "
        "resources were accessed"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
