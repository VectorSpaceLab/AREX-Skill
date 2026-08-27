#!/usr/bin/env python3
"""Safely assemble MapTR visualization sample directories into an MP4."""

from __future__ import print_function

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile


CAMERAS = (
    "CAM_FRONT_LEFT.jpg",
    "CAM_FRONT.jpg",
    "CAM_FRONT_RIGHT.jpg",
    "CAM_BACK_LEFT.jpg",
    "CAM_BACK.jpg",
    "CAM_BACK_RIGHT.jpg",
)
PREDICTION = "PRED_MAP_plot.png"
GROUND_TRUTH = "GT_fixednum_pts_MAP.png"
FRAME_SIZE = (1680, 450)
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


class VideoInputError(ValueError):
    """Raised for an invalid or incomplete visualization input."""


def parser():
    result = argparse.ArgumentParser(
        description="Assemble sorted MapTR visualization directories into MP4."
    )
    result.add_argument(
        "visdir",
        nargs="?",
        help="directory containing one child directory per visualization frame",
    )
    result.add_argument("--fps", default=10, type=int, help="video frames per second")
    result.add_argument("--video-name", default="demo", help="output name, with or without .mp4")
    result.add_argument(
        "--sample-name",
        default="SAMPLE_VIS.jpg",
        help="composite image name written inside each frame directory",
    )
    result.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing output video",
    )
    result.add_argument(
        "--self-check",
        action="store_true",
        help="assemble a two-frame temporary fixture and verify its output",
    )
    return result


def safe_name(value, option, suffixes=None):
    """Require a single local filename component, never a path."""
    if not value or value in {".", ".."} or not SAFE_NAME.fullmatch(value):
        raise VideoInputError(
            "%s must be a simple filename component, not a path: %r" % (option, value)
        )
    if suffixes is not None and Path(value).suffix.lower() not in suffixes:
        raise VideoInputError(
            "%s must end in one of %s: %r" % (option, ", ".join(sorted(suffixes)), value)
        )
    return value


def normalize_video_stem(value):
    value = safe_name(value, "--video-name")
    if value.lower().endswith(".mp4"):
        value = value[:-4]
    if not value:
        raise VideoInputError("--video-name must contain a non-empty stem")
    return value


def required_paths(frame_dir):
    return [frame_dir / name for name in CAMERAS] + [
        frame_dir / PREDICTION,
        frame_dir / GROUND_TRUTH,
    ]


def preflight_frame(frame_dir):
    missing = [str(path.name) for path in required_paths(frame_dir) if not path.is_file()]
    if missing:
        return "missing " + ", ".join(missing)
    return None


def read_image(cv2, path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise VideoInputError("cannot decode image: %s" % path)
    return image


def add_label(cv2, image, label):
    # Keep the source layout's small black label while avoiding assumptions
    # about the source image dimensions.
    thickness = max(1, min(image.shape[0] // 80, 3))
    scale = max(0.4, min(image.shape[0] / 180.0, 1.2))
    (width, height), _ = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness
    )
    cv2.rectangle(image, (0, 0), (width + 8, height + 8), (0, 0, 0), -1)
    cv2.putText(
        image,
        label,
        (4, height + 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
    return image


def compose_sample(cv2, frame_dir, sample_name):
    """Create one camera/prediction/GT composite and return its BGR image."""
    camera_images = [read_image(cv2, frame_dir / name) for name in CAMERAS]
    target_height, target_width = camera_images[0].shape[:2]
    if target_height < 1 or target_width < 1:
        raise VideoInputError("camera image has invalid dimensions: %s" % frame_dir)

    normalized = []
    labels = ("FRONT_LEFT", "FRONT", "FRONT_RIGHT", "BACK_LEFT", "BACK", "BACK_RIGHT")
    for image, label in zip(camera_images, labels):
        image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        if label == "BACK":
            image = cv2.flip(image, 1)
        normalized.append(add_label(cv2, image, label))

    row_one = cv2.hconcat(normalized[:3])
    row_two = cv2.hconcat(normalized[3:])
    cameras = cv2.vconcat((row_one, row_two))

    pred = read_image(cv2, frame_dir / PREDICTION)
    truth = read_image(cv2, frame_dir / GROUND_TRUTH)
    pred = cv2.copyMakeBorder(pred, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    truth = cv2.copyMakeBorder(truth, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(0, 0, 0))

    def fit_height(image):
        height, width = image.shape[:2]
        if height < 1 or width < 1:
            raise VideoInputError("map image has invalid dimensions: %s" % frame_dir)
        width = max(1, int(round(width * float(cameras.shape[0]) / height)))
        return cv2.resize(image, (width, cameras.shape[0]), interpolation=cv2.INTER_AREA)

    pred = add_label(cv2, fit_height(pred), "PRED")
    truth = add_label(cv2, fit_height(truth), "GT")
    sample = cv2.hconcat((cameras, pred, truth))
    sample_path = frame_dir / sample_name
    params = [cv2.IMWRITE_JPEG_QUALITY, 70] if sample_path.suffix.lower() in {".jpg", ".jpeg"} else []
    if not cv2.imwrite(str(sample_path), sample, params):
        raise VideoInputError("could not write sample image: %s" % sample_path)
    return sample


def frame_directories(visdir):
    return sorted((path for path in visdir.iterdir() if path.is_dir()), key=lambda path: path.name)


def assemble(visdir, fps, video_name, sample_name, overwrite=False, cv2_module=None):
    """Assemble complete, decodable child directories in deterministic order."""
    if fps <= 0:
        raise VideoInputError("--fps must be greater than zero")
    visdir = Path(visdir).expanduser().resolve()
    if not visdir.is_dir():
        raise VideoInputError("visualization directory is not a directory: %s" % visdir)

    sample_name = safe_name(sample_name, "--sample-name", IMAGE_SUFFIXES)
    if sample_name in set(CAMERAS) | {PREDICTION, GROUND_TRUTH}:
        raise VideoInputError("--sample-name would overwrite a required input image")
    video_stem = normalize_video_stem(video_name)
    output_path = visdir.parent / (video_stem + ".mp4")
    if output_path.exists() and not overwrite:
        raise VideoInputError("output exists; pass --overwrite to replace: %s" % output_path)
    if not os.access(str(visdir.parent), os.W_OK):
        raise VideoInputError("output directory is not writable: %s" % visdir.parent)

    if cv2_module is None:
        import cv2 as cv2_module

    candidates = frame_directories(visdir)
    if not candidates:
        raise VideoInputError("no frame directories found in: %s" % visdir)
    usable = []
    for frame_dir in candidates:
        problem = preflight_frame(frame_dir)
        if not problem:
            try:
                for image_path in required_paths(frame_dir):
                    read_image(cv2_module, image_path)
            except VideoInputError as exc:
                problem = str(exc)
        if problem:
            print("SKIP %s: %s" % (frame_dir.name, problem), file=sys.stderr)
        else:
            usable.append(frame_dir)
    if not usable:
        raise VideoInputError("no complete frame directory remains after validation")

    # Write beside the requested output and atomically publish only after all
    # frames have been composed. This avoids leaving a plausible-looking MP4
    # after a late decode or codec failure.
    temp_path = None
    writer = None
    processed = []
    try:
        handle = tempfile.NamedTemporaryFile(
            prefix=".%s-" % video_stem,
            suffix=".mp4",
            dir=str(visdir.parent),
            delete=False,
        )
        temp_path = Path(handle.name)
        handle.close()
        fourcc = cv2_module.VideoWriter_fourcc(*"mp4v")
        writer = cv2_module.VideoWriter(str(temp_path), fourcc, fps, FRAME_SIZE, True)
        if not writer.isOpened():
            raise VideoInputError("mp4v VideoWriter could not open: %s" % temp_path)
        for frame_dir in usable:
            sample = compose_sample(cv2_module, frame_dir, sample_name)
            frame = cv2_module.resize(sample, FRAME_SIZE, interpolation=cv2_module.INTER_AREA)
            writer.write(frame)
            processed.append(frame_dir.name)
        writer.release()
        writer = None
        if not temp_path.is_file() or temp_path.stat().st_size == 0:
            raise VideoInputError("VideoWriter produced an empty file")
        if output_path.exists() and not overwrite:
            raise VideoInputError("output appeared during assembly: %s" % output_path)
        os.replace(str(temp_path), str(output_path))
        temp_path = None
    finally:
        if writer is not None:
            writer.release()
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass
    print("WROTE %s (%d frames, %dfps, %dx%d)" % (
        output_path, len(processed), fps, FRAME_SIZE[0], FRAME_SIZE[1]
    ))
    print("ORDER " + ",".join(processed))
    return output_path, processed


def self_check():
    import cv2
    import numpy as np

    with tempfile.TemporaryDirectory(prefix="maptr-video-check-") as root:
        root = Path(root)
        visdir = root / "vis"
        visdir.mkdir()
        # Create in reverse order to prove the assembler sorts directory names.
        for name, value in (("frame-b", 80), ("frame-a", 40)):
            frame = visdir / name
            frame.mkdir()
            for index, camera in enumerate(CAMERAS):
                image = np.full((24, 32, 3), value + index, dtype=np.uint8)
                if not cv2.imwrite(str(frame / camera), image):
                    raise VideoInputError("fixture camera write failed")
            for filename in (PREDICTION, GROUND_TRUTH):
                image = np.full((30, 20, 3), value, dtype=np.uint8)
                if not cv2.imwrite(str(frame / filename), image):
                    raise VideoInputError("fixture map write failed")
        (visdir / "not-a-frame.txt").write_text("ignored\n")
        output, order = assemble(visdir, 2, "fixture", "SAMPLE_VIS.jpg")
        if order != ["frame-a", "frame-b"]:
            raise AssertionError("fixture order was not deterministic: %r" % order)
        if not output.is_file() or output.stat().st_size == 0:
            raise AssertionError("fixture video was not written")
        for name in order:
            if not (visdir / name / "SAMPLE_VIS.jpg").is_file():
                raise AssertionError("fixture sample image was not written: %s" % name)
        print("SELF-CHECK PASS: two sorted frames and generated samples")


def main(argv=None):
    args = parser().parse_args(argv)
    if args.self_check:
        try:
            self_check()
        except (ImportError, VideoInputError, AssertionError) as exc:
            parser().error("self-check failed: %s" % exc)
        return 0
    if args.visdir is None:
        parser().error("visdir is required unless --self-check is used")
    try:
        assemble(
            args.visdir,
            args.fps,
            args.video_name,
            args.sample_name,
            overwrite=args.overwrite,
        )
    except (ImportError, OSError, VideoInputError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
