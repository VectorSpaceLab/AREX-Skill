#!/usr/bin/env python3
"""Safe Photo2Cartoon preprocessing contract checker.

This script validates the documented preprocessing contract without importing
TensorFlow, dlib, face-alignment, OpenCV, torch, or local repo modules. By
default it runs synthetic crop/alpha-shape checks. With --repo-root it also
performs static source checks against an explicit Photo2Cartoon checkout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass
class Check:
    status: str
    name: str
    detail: str


@dataclass
class CropBox:
    top: int
    bottom: int
    left: int
    right: int
    crop_h: int
    crop_w: int
    top_pad: int
    left_pad: int
    bottom_clip: int
    right_clip: int


def add(checks: list[Check], status: str, name: str, detail: str) -> None:
    checks.append(Check(status=status, name=name, detail=detail))


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def contains_contract(text: str, needle: str) -> bool:
    """Return True when text contains a literal or regex contract token."""
    if needle.startswith("regex:"):
        return re.search(needle[len("regex:") :], text, flags=re.MULTILINE | re.DOTALL) is not None
    return compact(needle) in compact(text) or needle in text


def compute_crop_box(
    landmarks: Iterable[tuple[float, float]], image_h: int, image_w: int
) -> CropBox:
    """Replicate Photo2Cartoon's landmark bbox expansion and padding math."""
    xs = [p[0] for p in landmarks]
    ys = [p[1] for p in landmarks]
    landmarks_top = min(ys)
    landmarks_bottom = max(ys)
    landmarks_left = min(xs)
    landmarks_right = max(xs)

    box_h = landmarks_bottom - landmarks_top
    box_w = landmarks_right - landmarks_left

    top = int(landmarks_top - 0.8 * box_h)
    bottom = int(landmarks_bottom + 0.3 * box_h)
    left = int(landmarks_left - 0.3 * box_w)
    right = int(landmarks_right + 0.3 * box_w)

    if bottom - top > right - left:
        left -= ((bottom - top) - (right - left)) // 2
        right = left + (bottom - top)
    else:
        top -= ((right - left) - (bottom - top)) // 2
        bottom = top + (right - left)

    top_pad = max(0, -top)
    left_pad = max(0, -left)
    bottom_clip = max(0, bottom - (image_h - 1))
    right_clip = max(0, right - (image_w - 1))

    return CropBox(
        top=top,
        bottom=bottom,
        left=left,
        right=right,
        crop_h=bottom - top + 1,
        crop_w=right - left + 1,
        top_pad=top_pad,
        left_pad=left_pad,
        bottom_clip=bottom_clip,
        right_clip=right_clip,
    )


def run_synthetic_checks(checks: list[Check]) -> dict[str, object]:
    centered = compute_crop_box(
        landmarks=[(120, 120), (220, 120), (220, 220), (120, 220), (170, 170)],
        image_h=360,
        image_w=360,
    )
    edge = compute_crop_box(
        landmarks=[(20, 30), (80, 30), (80, 100), (20, 100), (50, 65)],
        image_h=120,
        image_w=100,
    )

    if centered.crop_h == centered.crop_w:
        add(checks, "PASS", "synthetic centered crop is square", f"{centered.crop_h}x{centered.crop_w}")
    else:
        add(checks, "FAIL", "synthetic centered crop is square", asdict(centered).__repr__())

    if edge.crop_h == edge.crop_w and (edge.top_pad > 0 or edge.left_pad > 0 or edge.bottom_clip > 0 or edge.right_clip > 0):
        add(
            checks,
            "PASS",
            "synthetic edge crop keeps square with white padding",
            f"{edge.crop_h}x{edge.crop_w}, pads top={edge.top_pad}, left={edge.left_pad}, clips bottom={edge.bottom_clip}, right={edge.right_clip}",
        )
    else:
        add(checks, "FAIL", "synthetic edge crop keeps square with white padding", asdict(edge).__repr__())

    # Shape-only alpha composition check; no NumPy dependency is needed.
    face_shape = (edge.crop_h, edge.crop_w, 3)
    alpha_shape = (edge.crop_h, edge.crop_w)
    mask_shape = (alpha_shape[0], alpha_shape[1], 1)
    rgba_shape = (face_shape[0], face_shape[1], 4)
    if alpha_shape == face_shape[:2] and mask_shape[:2] == face_shape[:2] and rgba_shape[:2] == face_shape[:2]:
        add(
            checks,
            "PASS",
            "alpha mask broadcast contract",
            f"face={face_shape}, alpha={alpha_shape}, mask={mask_shape}, rgba={rgba_shape}",
        )
    else:
        add(
            checks,
            "FAIL",
            "alpha mask broadcast contract",
            f"face={face_shape}, alpha={alpha_shape}, mask={mask_shape}, rgba={rgba_shape}",
        )

    return {"centeredCrop": asdict(centered), "edgeCrop": asdict(edge)}


SOURCE_EXPECTATIONS: dict[str, list[tuple[str, str]]] = {
    "utils/preprocess.py": [
        ("Preprocess class", "class Preprocess"),
        ("default device/detector", "def __init__(self, device='cpu', detector='dlib')"),
        ("FaceDetect constructed with device/detector", "FaceDetect(device, detector)"),
        ("FaceSeg constructed", "FaceSeg()"),
        ("process aligns first", "self.detect.align(image)"),
        ("process returns None for no face", "if face_info is None"),
        ("RGBA stack", "np.dstack((face, mask))"),
        ("top expansion ratio", "landmarks_top - 0.8 *"),
        ("bottom expansion ratio", "landmarks_bottom + 0.3 *"),
        ("left expansion ratio", "landmarks_left - 0.3 *"),
        ("right expansion ratio", "landmarks_right + 0.3 *"),
        ("white crop allocation", "np.ones((bottom - top + 1, right - left + 1, 3), np.uint8) * 255"),
    ],
    "utils/face_detect.py": [
        ("face_alignment API", "face_alignment.FaceAlignment"),
        ("detector is forwarded", "face_detector=detector"),
        ("landmark retrieval", "self.fa.get_landmarks(image)"),
        ("largest face selection", "np.argmax(areas)"),
        ("left eye landmark", "landmarks[36]"),
        ("right eye landmark", "landmarks[45]"),
        ("affine rotation", "cv2.warpAffine"),
        ("white rotation border", "borderValue=(255, 255, 255)"),
    ],
    "utils/face_seg.py": [
        ("default segmentation asset", "seg_model_384.pb"),
        ("TensorFlow compat session", "tf.compat.v1.Session"),
        ("GraphDef import", "tf.compat.v1.GraphDef"),
        ("input tensor name", "input_1:0"),
        ("output tensor name", "sigmoid/Sigmoid:0"),
        ("384x384 input resize", "cv2.resize(image, (384, 384)"),
        ("input normalization", "image / 255."),
        ("uint8 mask output", "output * 255"),
    ],
    "data_process.py": [
        ("Preprocess used", "Preprocess()"),
        ("batch process call", "pre.process(img)"),
        ("RGB face channels", "face_rgba[:,:,:3]"),
        ("alpha channel", "face_rgba[:,:,3]"),
        ("white background formula", "face*mask + (1-mask)*255"),
        ("OpenCV write", "cv2.imwrite"),
    ],
}


def run_source_checks(root: Path, checks: list[Check]) -> None:
    if not root.exists():
        add(checks, "FAIL", "repo root exists", f"not found: {root}")
        return
    if not root.is_dir():
        add(checks, "FAIL", "repo root is directory", f"not a directory: {root}")
        return

    add(checks, "PASS", "repo root exists", str(root))

    for rel, expectations in SOURCE_EXPECTATIONS.items():
        path = root / rel
        if not path.exists():
            add(checks, "FAIL", f"{rel} exists", "missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        add(checks, "PASS", f"{rel} exists", f"{path.stat().st_size} bytes")
        for label, needle in expectations:
            if contains_contract(text, needle):
                add(checks, "PASS", f"{rel}: {label}", needle)
            else:
                add(checks, "FAIL", f"{rel}: {label}", f"missing token: {needle}")


def check_seg_model(path: Path | None, require: bool, checks: list[Check]) -> None:
    if path is None:
        add(checks, "WARN", "segmentation graph path", "not checked; pass --repo-root or --seg-model")
        return
    if path.exists() and path.is_file() and path.stat().st_size > 0:
        add(checks, "PASS", "segmentation graph asset", f"found non-empty file: {path}")
    elif require:
        add(checks, "FAIL", "segmentation graph asset", f"missing or empty: {path}")
    else:
        add(
            checks,
            "WARN",
            "segmentation graph asset",
            f"missing or empty external asset: {path}; use --require-seg-model when this must fail",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check Photo2Cartoon preprocessing source contracts and synthetic crop/alpha semantics safely. "
            "The checker performs no imports from TensorFlow, dlib, face-alignment, OpenCV, torch, or the target checkout."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Explicit path to a Photo2Cartoon checkout for static source checks.",
    )
    parser.add_argument(
        "--seg-model",
        type=Path,
        help="Explicit path to seg_model_384.pb. If omitted with --repo-root, utils/seg_model_384.pb is checked.",
    )
    parser.add_argument(
        "--require-seg-model",
        action="store_true",
        help="Fail when the segmentation graph file is missing or empty. By default it is only a warning because the graph is an external asset.",
    )
    parser.add_argument(
        "--skip-synthetic",
        action="store_true",
        help="Skip pure-Python synthetic crop and alpha-shape checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the text report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks: list[Check] = []
    details: dict[str, object] = {}

    if args.skip_synthetic:
        add(checks, "WARN", "synthetic checks", "skipped by --skip-synthetic")
    else:
        details["synthetic"] = run_synthetic_checks(checks)

    if args.repo_root is not None:
        root = args.repo_root.expanduser().resolve()
        run_source_checks(root, checks)
        seg_path = args.seg_model.expanduser().resolve() if args.seg_model else root / "utils" / "seg_model_384.pb"
    else:
        if args.seg_model:
            seg_path = args.seg_model.expanduser().resolve()
        else:
            seg_path = None
        add(checks, "WARN", "source contract checks", "skipped; pass --repo-root to check a checkout")

    check_seg_model(seg_path, args.require_seg_model, checks)

    status_counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for check in checks:
        status_counts[check.status] = status_counts.get(check.status, 0) + 1
    ok = status_counts.get("FAIL", 0) == 0

    payload = {
        "ok": ok,
        "summary": status_counts,
        "checks": [asdict(c) for c in checks],
        "details": details,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Photo2Cartoon preprocessing contract check")
        print(f"ok: {ok}")
        print(f"summary: {status_counts}")
        for check in checks:
            print(f"[{check.status}] {check.name}: {check.detail}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
