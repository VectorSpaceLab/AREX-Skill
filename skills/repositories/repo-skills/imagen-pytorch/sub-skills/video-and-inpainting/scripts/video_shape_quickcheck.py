#!/usr/bin/env python3
"""
Preflight Imagen-Pytorch video and inpainting shapes without importing the repo,
loading models, downloading text encoders, training, or sampling.

The checks mirror documented source assertions for Unet3D, Imagen.sample,
ElucidatedImagen.sample, and parent forward/training paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple


Shape = Tuple[int, ...]


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    inferred: dict = field(default_factory=dict)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def parse_int_list(value: Optional[str], *, name: str, report: Report) -> Optional[Tuple[int, ...]]:
    if value is None:
        return None

    parts = [part.strip() for part in value.replace("x", ",").split(",") if part.strip()]
    if not parts:
        report.error(f"{name} is empty")
        return None

    out: List[int] = []
    for part in parts:
        try:
            parsed = int(part)
        except ValueError:
            report.error(f"{name} must contain integers, got {part!r}")
            return None
        if parsed <= 0:
            report.error(f"{name} values must be positive, got {parsed}")
        out.append(parsed)
    return tuple(out)


def parse_shape(value: Optional[str], *, name: str, allowed_ranks: Sequence[int], report: Report) -> Optional[Shape]:
    shape = parse_int_list(value, name=name, report=report)
    if shape is None:
        return None
    if len(shape) not in allowed_ranks:
        ranks = ", ".join(str(rank) for rank in allowed_ranks)
        report.error(f"{name} rank must be one of {{{ranks}}}, got {len(shape)} from {shape}")
    return shape


def expand_tuple(values: Tuple[int, ...], *, length: int, name: str, report: Report) -> Tuple[int, ...]:
    if len(values) == length:
        return values
    if len(values) == 1:
        return values * length
    report.error(f"{name} must have length 1 or {length}, got {len(values)} values {values}")
    return values


def validate_temporal_factors(args: argparse.Namespace, report: Report) -> Tuple[int, ...]:
    raw = parse_int_list(args.temporal_downsample_factor, name="--temporal-downsample-factor", report=report)
    factors = raw or (1,)

    if args.num_unets is not None:
        if args.num_unets <= 0:
            report.error("--num-unets must be positive")
        else:
            factors = expand_tuple(factors, length=args.num_unets, name="--temporal-downsample-factor", report=report)

    if factors:
        if factors[-1] != 1:
            report.error("temporal_downsample_factor last stage must be 1")
        if tuple(sorted(factors, reverse=True)) != tuple(factors):
            report.error("temporal_downsample_factor must be in descending order")

    report.inferred["temporal_downsample_factor"] = list(factors)
    return tuple(factors)


def validate_unet_divisors(args: argparse.Namespace, stages: int, report: Report) -> Tuple[int, ...]:
    raw = parse_int_list(args.unet_temporal_divisor, name="--unet-temporal-divisor", report=report) or (1,)
    divisors = expand_tuple(raw, length=stages, name="--unet-temporal-divisor", report=report)
    report.inferred["unet_temporal_divisor"] = list(divisors)
    return tuple(divisors)


def ensure_square(shape: Optional[Shape], *, name: str, report: Report) -> None:
    if shape is None or len(shape) < 2:
        return
    if shape[-1] != shape[-2]:
        report.error(f"{name} height and width must be square for Imagen training/forward, got {shape[-2:]}" )


def batch_from_shapes(*shapes: Optional[Shape]) -> Optional[int]:
    for shape in shapes:
        if shape:
            return shape[0]
    return None


def channel_from_shapes(*shapes: Optional[Shape]) -> Optional[int]:
    for shape in shapes:
        if shape and len(shape) in (4, 5):
            return shape[1]
    return None


def validate_batch(name: str, shape: Optional[Shape], expected: Optional[int], report: Report) -> None:
    if shape is None or expected is None:
        return
    if shape[0] != expected:
        report.error(f"{name} batch {shape[0]} must match planned batch {expected}")


def validate_channels(name: str, shape: Optional[Shape], expected: Optional[int], report: Report) -> None:
    if shape is None or expected is None or len(shape) < 2:
        return
    if shape[1] != expected:
        report.error(f"{name} channels {shape[1]} must match planned channels {expected}")


def validate_stage_frames(
    frames: Optional[int],
    factors: Sequence[int],
    divisors: Sequence[int],
    *,
    ignore_time: bool,
    report: Report,
) -> List[Optional[int]]:
    if frames is None:
        return [None for _ in factors]

    stage_frames: List[Optional[int]] = []
    for index, (factor, divisor) in enumerate(zip(factors, divisors), start=1):
        if frames % factor != 0:
            report.error(
                f"video_frames {frames} must be divisible by temporal_downsample_factor "
                f"stage {index} value {factor}"
            )
            stage_frames.append(None)
            continue

        current = frames // factor
        stage_frames.append(current)

        if not ignore_time and current % divisor != 0:
            report.error(
                f"stage {index} frame count {current} must be divisible by "
                f"Unet3D total_temporal_divisor {divisor}; choose compatible frames or deliberate ignore_time"
            )

    report.inferred["stage_frame_counts"] = stage_frames
    return stage_frames


def validate_mask(
    *,
    mask: Optional[Shape],
    image_shape: Optional[Shape],
    video_shape: Optional[Shape],
    video_frames: Optional[int],
    planned_batch: Optional[int],
    operation: str,
    report: Report,
) -> None:
    if operation == "inpaint-image":
        if image_shape is None:
            report.error("--image-shape is required for image inpainting")
        if mask is None:
            report.error("--mask-shape is required with --operation inpaint-image")
        if mask is None or image_shape is None:
            return
        if len(mask) != 3:
            report.error(f"image inpaint mask must be (batch,height,width), got {mask}")
            return
        validate_batch("mask", mask, planned_batch, report)
        if mask[-2:] != image_shape[-2:]:
            report.warn(
                f"mask spatial shape {mask[-2:]} differs from image shape {image_shape[-2:]}; "
                "source code resizes masks per stage, but matching source resolution avoids surprises"
            )
        return

    if operation == "inpaint-video":
        if video_shape is None:
            report.error("--video-shape is required for video inpainting")
        if mask is None:
            report.error("--mask-shape is required with --operation inpaint-video")
        if mask is None or video_shape is None:
            return
        if len(mask) not in (3, 4):
            report.error(
                "video inpaint mask must be shared (batch,height,width) or per-frame "
                f"(batch,frames,height,width), got {mask}"
            )
            return
        validate_batch("mask", mask, planned_batch, report)
        if len(mask) == 4 and video_frames is not None and mask[1] != video_frames:
            report.error(f"per-frame mask frames {mask[1]} must match inpaint video frames {video_frames}")
        if len(mask) == 3:
            report.note("3D video mask will broadcast across all video frames in the sample path")
            mask_hw = mask[-2:]
        else:
            mask_hw = mask[-2:]
        if mask_hw != video_shape[-2:]:
            report.warn(
                f"mask spatial shape {mask_hw} differs from video shape {video_shape[-2:]}; "
                "source code resizes masks per stage, but matching source resolution avoids surprises"
            )


def validate_conditioning_video(
    *,
    name: str,
    shape: Optional[Shape],
    factors: Sequence[int],
    divisors: Sequence[int],
    planned_batch: Optional[int],
    planned_channels: Optional[int],
    resize_cond_video_frames: bool,
    report: Report,
) -> None:
    if shape is None:
        return
    if len(shape) != 5:
        report.error(f"{name} must be a 5D video tensor (batch,channels,frames,height,width), got {shape}")
        return

    validate_batch(name, shape, planned_batch, report)
    validate_channels(name, shape, planned_channels, report)
    frames = shape[2]

    for index, (factor, divisor) in enumerate(zip(factors, divisors), start=1):
        stage_frames = frames
        if resize_cond_video_frames:
            if frames % factor != 0:
                report.error(
                    f"{name} frames {frames} must be divisible by stage {index} "
                    f"temporal_downsample_factor {factor} when resize_cond_video_frames=True"
                )
                continue
            stage_frames = frames // factor
        if stage_frames % divisor != 0:
            report.error(
                f"{name} stage {index} frames {stage_frames} must be divisible by "
                f"Unet3D total_temporal_divisor {divisor}"
            )


def validate_text_batch(args: argparse.Namespace, planned_batch: Optional[int], report: Report) -> None:
    if args.texts is None:
        return
    if args.texts <= 0:
        report.error("--texts must be positive when supplied")
        return
    if planned_batch is not None and args.texts != planned_batch:
        report.error(f"text count {args.texts} must match planned batch {planned_batch}")
    if args.batch_size != args.texts:
        report.note(
            f"text-conditioned sample paths use text batch {args.texts}; "
            f"explicit --batch-size {args.batch_size} would be overridden"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight Imagen-Pytorch video/inpainting tensor shapes.")
    parser.add_argument("--operation", choices=["sample", "train", "inpaint-image", "inpaint-video"], default="sample")
    parser.add_argument("--video-model", action="store_true", help="Set when any cascade stage is Unet3D.")
    parser.add_argument("--image-shape", help="Image tensor shape as B,C,H,W")
    parser.add_argument("--video-shape", help="Video tensor shape as B,C,F,H,W")
    parser.add_argument("--mask-shape", help="Inpainting mask shape as B,H,W or B,F,H,W")
    parser.add_argument("--cond-video-shape", help="Preceding conditioning video shape as B,C,F,H,W")
    parser.add_argument("--post-cond-video-shape", help="Following conditioning video shape as B,C,F,H,W")
    parser.add_argument("--video-frames", type=int, help="Requested sample frame count.")
    parser.add_argument("--temporal-downsample-factor", default="1", help="Int or comma list, e.g. 4,2,1")
    parser.add_argument("--unet-temporal-divisor", default="1", help="Int or comma list of Unet3D total temporal divisors; default 1")
    parser.add_argument("--num-unets", type=int, help="Optional number of cascade stages for scalar expansion checks.")
    parser.add_argument("--texts", type=int, help="Number of text prompts/text embeddings.")
    parser.add_argument("--batch-size", type=int, default=1, help="Requested unconditional/sample batch size; text count overrides in text-conditioned sampling.")
    parser.add_argument("--return-pil-images", action="store_true", help="Flag planned return_pil_images=True.")
    parser.add_argument("--ignore-time", action="store_true", help="Flag deliberate ignore_time=True for training/forward.")
    parser.add_argument("--resize-cond-video-frames", dest="resize_cond_video_frames", action="store_true", default=True)
    parser.add_argument("--no-resize-cond-video-frames", dest="resize_cond_video_frames", action="store_false")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = Report()

    if args.batch_size <= 0:
        report.error("--batch-size must be positive")

    factors = validate_temporal_factors(args, report)
    divisors = validate_unet_divisors(args, len(factors), report)

    image_shape = parse_shape(args.image_shape, name="--image-shape", allowed_ranks=(4,), report=report)
    video_shape = parse_shape(args.video_shape, name="--video-shape", allowed_ranks=(5,), report=report)
    mask_shape = parse_shape(args.mask_shape, name="--mask-shape", allowed_ranks=(3, 4), report=report)
    cond_video_shape = parse_shape(args.cond_video_shape, name="--cond-video-shape", allowed_ranks=(5,), report=report)
    post_cond_video_shape = parse_shape(args.post_cond_video_shape, name="--post-cond-video-shape", allowed_ranks=(5,), report=report)

    ensure_square(image_shape, name="image", report=report)
    ensure_square(video_shape, name="video", report=report)
    ensure_square(cond_video_shape, name="cond_video_frames", report=report)
    ensure_square(post_cond_video_shape, name="post_cond_video_frames", report=report)

    if args.return_pil_images and args.video_model:
        report.error("return_pil_images=True is not supported for video models; keep return_pil_images=False")

    if args.operation in ("inpaint-video", "sample") and video_shape is not None and not args.video_model:
        report.warn("a 5D video shape was supplied without --video-model; Imagen is video only when a cascade stage is Unet3D")

    if args.operation == "inpaint-image" and args.video_model:
        report.warn("image inpainting with a video model is ambiguous; use inpaint-video for 5D video masks or an image model for 4D image masks")

    if args.operation == "train":
        if image_shape is None and video_shape is None:
            report.error("--operation train requires --image-shape or --video-shape")
        if image_shape is not None and video_shape is not None:
            report.error("provide only one of --image-shape or --video-shape for a single train preflight")

    if args.operation == "inpaint-image" and (image_shape is None or mask_shape is None):
        # Detailed messages are added by validate_mask as well; this keeps sample/inpaint pairing explicit.
        pass
    if args.operation == "inpaint-video" and (video_shape is None or mask_shape is None):
        pass

    inpaint_frames = video_shape[2] if (args.operation == "inpaint-video" and video_shape is not None) else None
    explicit_frames = args.video_frames
    if explicit_frames is not None and explicit_frames <= 0:
        report.error("--video-frames must be positive")

    video_frames = inpaint_frames if inpaint_frames is not None else explicit_frames
    if inpaint_frames is not None and explicit_frames is not None and inpaint_frames != explicit_frames:
        report.warn(
            f"inpaint_videos supplies video_frames={inpaint_frames}; explicit --video-frames {explicit_frames} "
            "would be ignored by the sample path"
        )

    if args.video_model and args.operation == "sample" and video_frames is None:
        report.error("video sample requires --video-frames unless --video-shape is supplied for video inpainting")

    if args.operation == "inpaint-video" and not args.video_model:
        report.error("video inpainting requires --video-model because it uses Unet3D video sampling behavior")

    planned_batch = args.batch_size
    if args.texts is not None:
        planned_batch = args.texts
    shape_batch = batch_from_shapes(video_shape, image_shape, cond_video_shape, post_cond_video_shape)
    if args.texts is None and shape_batch is not None:
        planned_batch = shape_batch
    report.inferred["planned_batch"] = planned_batch

    planned_channels = channel_from_shapes(video_shape, image_shape, cond_video_shape, post_cond_video_shape)
    report.inferred["planned_channels"] = planned_channels

    validate_text_batch(args, planned_batch, report)
    validate_batch("image", image_shape, planned_batch, report)
    validate_batch("video", video_shape, planned_batch, report)

    if image_shape and video_shape is None and args.operation == "train" and args.video_model:
        effective_ignore_time = True
        video_frames_for_stage_check: Optional[int] = 1
        report.note("4D training input to a video model is converted to a single-frame video and ignore_time=True")
    else:
        effective_ignore_time = args.ignore_time
        video_frames_for_stage_check = video_frames if args.video_model else None

    validate_stage_frames(
        video_frames_for_stage_check,
        factors,
        divisors,
        ignore_time=effective_ignore_time,
        report=report,
    )

    validate_conditioning_video(
        name="cond_video_frames",
        shape=cond_video_shape,
        factors=factors,
        divisors=divisors,
        planned_batch=planned_batch,
        planned_channels=planned_channels,
        resize_cond_video_frames=args.resize_cond_video_frames,
        report=report,
    )
    validate_conditioning_video(
        name="post_cond_video_frames",
        shape=post_cond_video_shape,
        factors=factors,
        divisors=divisors,
        planned_batch=planned_batch,
        planned_channels=planned_channels,
        resize_cond_video_frames=args.resize_cond_video_frames,
        report=report,
    )

    validate_mask(
        mask=mask_shape,
        image_shape=image_shape,
        video_shape=video_shape,
        video_frames=video_frames,
        planned_batch=planned_batch,
        operation=args.operation,
        report=report,
    )

    if args.operation == "inpaint-image" and (image_shape is None or mask_shape is None):
        # validate_mask already covers exact missing item; no-op here.
        pass
    if args.operation == "inpaint-video" and (video_shape is None or mask_shape is None):
        pass

    report.inferred["effective_ignore_time"] = effective_ignore_time
    report.inferred["video_frames"] = video_frames
    report.inferred["resize_cond_video_frames"] = args.resize_cond_video_frames

    payload = {
        "ok": not report.errors,
        "errors": report.errors,
        "warnings": report.warnings,
        "notes": report.notes,
        "inferred": report.inferred,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "OK" if payload["ok"] else "FAILED"
        print(f"video_shape_quickcheck: {status}")
        for key in ("errors", "warnings", "notes"):
            values = payload[key]
            if not values:
                continue
            print(f"\n{key.upper()}:")
            for value in values:
                print(f"- {value}")
        print("\nINFERRED:")
        for key, value in payload["inferred"].items():
            print(f"- {key}: {value}")

    return 0 if not report.errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
