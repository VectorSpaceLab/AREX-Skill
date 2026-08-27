#!/usr/bin/env python3
"""Static validator for a video-understanding plan.

This script is intentionally conservative:
- it checks only local file shape and tool/prerequisite consistency
- it does not import model modules
- it does not touch checkpoints, GPUs, or external services
"""

import argparse
import pathlib
import re
import sys

SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
PREFERRED_VIDEO_SUFFIX = ".mp4"

CANONICAL_TOOLS = [
    "upload_video",
    "VideoCaption",
    "ActionRecognition",
    "DenseCaption",
    "GenerateTikTokVideo",
]

NORMALIZED_TOOL_MAP = {
    "uploadvideo": "upload_video",
    "conversationbotuploadvideo": "upload_video",
    "videocaption": "VideoCaption",
    "caption": "VideoCaption",
    "actionrecognition": "ActionRecognition",
    "action": "ActionRecognition",
    "densecaption": "DenseCaption",
    "dense": "DenseCaption",
    "generatetiktokvideo": "GenerateTikTokVideo",
    "generateticktokvideo": "GenerateTikTokVideo",
    "tiktok": "GenerateTikTokVideo",
}
NORMALIZED_TOOL_MAP.update(
    {re.sub(r"[^a-z0-9]+", "", name.lower()): name for name in CANONICAL_TOOLS}
)

TIKTOK_BASE_TOOLS = ["VideoCaption", "ActionRecognition", "DenseCaption"]


def normalize_key(value):
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def split_csv_values(values):
    items = []
    for value in values:
        if not value:
            continue
        for part in value.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


def ordered_unique(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def canonical_tool_name(raw_name):
    key = normalize_key(raw_name.replace("ConversationBot.", ""))
    if key not in NORMALIZED_TOOL_MAP:
        raise ValueError(
            "unknown video tool %r; expected one of: %s"
            % (raw_name, ", ".join(CANONICAL_TOOLS))
        )
    return NORMALIZED_TOOL_MAP[key]


def parse_tools(raw_tools):
    parsed = []
    for raw in split_csv_values(raw_tools):
        parsed.append(canonical_tool_name(raw))
    return ordered_unique(parsed)


def validate_video_path(video_path, warnings, errors):
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", video_path):
        errors.append("video path must be a local filesystem path, not a URL")
        return

    path = pathlib.Path(video_path)
    suffix = path.suffix.lower()
    if not suffix:
        errors.append("video path needs a file extension")
        return

    if suffix not in SUPPORTED_VIDEO_SUFFIXES:
        errors.append(
            "unsupported video extension %r; allowed extensions: %s"
            % (suffix, ", ".join(sorted(SUPPORTED_VIDEO_SUFFIXES)))
        )
    elif suffix != PREFERRED_VIDEO_SUFFIX:
        warnings.append("preferred extension is .mp4; continuing with %s" % suffix)

    if path.exists() and not path.is_file():
        errors.append("video path exists but is not a regular file")
    elif not path.exists():
        warnings.append("video file does not exist yet; suffix-only validation passed")


def add_requirement(errors, tool_name, flag_name, enabled, detail):
    if not enabled:
        errors.append("%s requires %s (%s)" % (tool_name, flag_name, detail))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Static validator for video-understanding plans.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/validate_video_plan.py --video samples/demo.mp4 --tool ActionRecognition --uniformerv2-ready\n"
            "  python scripts/validate_video_plan.py --video samples/demo.mp4 --tool VideoCaption --tool ActionRecognition --tool DenseCaption --tool GenerateTikTokVideo --prompt 'cut the most exciting part' --tag2text-ready --uniformerv2-ready --detectron2-ready --grit-checkpoint-ready --openai-key-present --ffmpeg-present --bark-present"
        ),
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Local video path to validate.",
    )
    parser.add_argument(
        "--tool",
        action="append",
        required=True,
        help=(
            "Requested video capability. Repeat this flag or pass a comma-separated list. "
            "Recognized names: upload_video, VideoCaption, ActionRecognition, DenseCaption, GenerateTikTokVideo."
        ),
    )
    parser.add_argument(
        "--prompt",
        help="Text prompt required when GenerateTikTokVideo is part of the plan.",
    )
    parser.add_argument(
        "--tag2text-ready",
        action="store_true",
        help="Mark the Tag2Text caption stack as available.",
    )
    parser.add_argument(
        "--uniformerv2-ready",
        action="store_true",
        help="Mark the uniformerv2 action stack as available.",
    )
    parser.add_argument(
        "--detectron2-ready",
        action="store_true",
        help="Mark the Detectron2 runtime as available.",
    )
    parser.add_argument(
        "--grit-checkpoint-ready",
        action="store_true",
        help="Mark the GRiT dense-caption checkpoint as available.",
    )
    parser.add_argument(
        "--openai-key-present",
        action="store_true",
        help="Mark an OpenAI key as available for TikTok timestamping and narration.",
    )
    parser.add_argument(
        "--ffmpeg-present",
        action="store_true",
        help="Mark the ffmpeg binary as available for clipping and muxing.",
    )
    parser.add_argument(
        "--bark-present",
        action="store_true",
        help="Mark the Bark audio stack as available for narration synthesis.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser


def validate_plan(args):
    warnings = []
    errors = []

    validate_video_path(args.video, warnings, errors)
    requested_tools = parse_tools(args.tool)

    if not requested_tools:
        errors.append("at least one tool is required")
        return requested_tools, warnings, errors

    if "GenerateTikTokVideo" in requested_tools:
        missing_base = [tool for tool in TIKTOK_BASE_TOOLS if tool not in requested_tools]
        if missing_base:
            errors.append(
                "GenerateTikTokVideo requires the base tools in the same plan: %s"
                % ", ".join(missing_base)
            )
        if not args.prompt or not args.prompt.strip():
            errors.append("GenerateTikTokVideo requires --prompt")

    if "VideoCaption" in requested_tools:
        add_requirement(
            errors,
            "VideoCaption",
            "--tag2text-ready",
            args.tag2text_ready,
            "Tag2Text checkpoint",
        )

    if "ActionRecognition" in requested_tools:
        add_requirement(
            errors,
            "ActionRecognition",
            "--uniformerv2-ready",
            args.uniformerv2_ready,
            "uniformerv2 checkpoint",
        )

    if "DenseCaption" in requested_tools:
        add_requirement(
            errors,
            "DenseCaption",
            "--detectron2-ready",
            args.detectron2_ready,
            "Detectron2 runtime",
        )
        add_requirement(
            errors,
            "DenseCaption",
            "--grit-checkpoint-ready",
            args.grit_checkpoint_ready,
            "GRiT checkpoint",
        )

    if "GenerateTikTokVideo" in requested_tools:
        add_requirement(
            errors,
            "GenerateTikTokVideo",
            "--openai-key-present",
            args.openai_key_present,
            "timestamp and narration generation",
        )
        add_requirement(
            errors,
            "GenerateTikTokVideo",
            "--ffmpeg-present",
            args.ffmpeg_present,
            "clip trimming and muxing",
        )
        add_requirement(
            errors,
            "GenerateTikTokVideo",
            "--bark-present",
            args.bark_present,
            "audio synthesis",
        )

    if args.strict and warnings:
        errors.extend(warnings)
        warnings = []

    return requested_tools, warnings, errors


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    requested_tools, warnings, errors = validate_plan(args)

    if errors:
        print("video-understanding plan: invalid", file=sys.stderr)
        for item in errors:
            print("- %s" % item, file=sys.stderr)
        if warnings:
            print("warnings:", file=sys.stderr)
            for item in warnings:
                print("- %s" % item, file=sys.stderr)
        return 2

    print("video-understanding plan: OK")
    print("tools: %s" % ", ".join(requested_tools))
    if warnings:
        print("warnings:")
        for item in warnings:
            print("- %s" % item)
    if "GenerateTikTokVideo" in requested_tools:
        print(
            "composite flow: analysis tools -> timestamp selection -> narration -> clip muxing"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
