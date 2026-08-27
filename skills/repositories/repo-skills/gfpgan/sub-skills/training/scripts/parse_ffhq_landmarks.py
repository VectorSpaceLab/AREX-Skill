#!/usr/bin/env python3
"""Parse FFHQ JSON landmarks into the GFPGAN component-landmark .pth schema.

The default mode only reads JSON and writes a PyTorch dictionary. It does not
open image data unless --save-crops-dir is provided.

Example:
    python scripts/parse_ffhq_landmarks.py --json-path ffhq-dataset-v2.json --save-path FFHQ_eye_mouth_landmarks_512.pth
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch

LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))
MOUTH = list(range(48, 68))


def component_triplet(landmarks: np.ndarray, indices: List[int], min_half_len: float = 16.0) -> Tuple[float, float, float]:
    points = landmarks[indices]
    mean = np.mean(points, axis=0)
    half_len = max(float(np.max(np.max(points, axis=0) - np.min(points, axis=0)) / 2.0), min_half_len)
    return float(mean[0]), float(mean[1]), half_len


def bbox_from_triplet(triplet: Tuple[float, float, float], enlarge: float = 1.0) -> np.ndarray:
    cx, cy, half_len = triplet
    half_len *= enlarge
    return np.hstack((np.array([cx, cy]) - half_len + 1, np.array([cx, cy]) + half_len)).astype(int)


def read_image(face_root: Path, file_path: str, index: int, lmdb_keys: Optional[List[str]] = None):
    if face_root.suffix == ".lmdb":
        from basicsr.utils import FileClient, imfrombytes

        key = lmdb_keys[index] if lmdb_keys else Path(file_path).stem
        client = FileClient("lmdb", db_paths=str(face_root))
        return imfrombytes(client.get(key), float32=True)
    img = cv2.imread(str(face_root / file_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image for crop preview: {face_root / file_path}")
    return img.astype(np.float32) / 255.0


def save_crop_preview(img: np.ndarray, bbox: np.ndarray, path: Path) -> None:
    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox.tolist()
    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    crop = img[y1:y2, x1:x2]
    cv2.imwrite(str(path), np.clip(crop * 255, 0, 255).astype(np.uint8))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a GFPGAN component landmark .pth file from FFHQ JSON metadata.")
    parser.add_argument("--json-path", required=True, help="Path to FFHQ JSON metadata containing image.face_landmarks.")
    parser.add_argument("--save-path", required=True, help="Output .pth path.")
    parser.add_argument("--scale", type=float, default=0.5, help="Scale applied to JSON landmark coordinates; 0.5 matches official 1024-to-512 FFHQ.")
    parser.add_argument("--enlarge-ratio", type=float, default=1.4, help="Eye crop enlarge ratio used for optional previews and documented schema.")
    parser.add_argument("--face-root", help="Optional image root or .lmdb used only with --save-crops-dir.")
    parser.add_argument("--save-crops-dir", help="Optional directory for eye/mouth crop previews. Requires --face-root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path = Path(args.json_path)
    if not json_path.is_file():
        print(f"JSON metadata not found: {json_path}", file=sys.stderr)
        return 2
    if args.save_crops_dir and not args.face_root:
        print("--save-crops-dir requires --face-root", file=sys.stderr)
        return 2

    with json_path.open("rb") as f:
        json_data: Dict[str, Any] = json.load(f, object_pairs_hook=OrderedDict)

    face_root = Path(args.face_root) if args.face_root else None
    lmdb_keys: Optional[List[str]] = None
    if face_root and face_root.suffix == ".lmdb":
        meta_info = face_root / "meta_info.txt"
        if meta_info.is_file():
            lmdb_keys = [line.split(".")[0].strip() for line in meta_info.read_text().splitlines() if line.strip()]

    save_dict: Dict[str, Dict[str, List[float]]] = {}
    crop_dir = Path(args.save_crops_dir) if args.save_crops_dir else None

    for item_idx, item in enumerate(json_data.values()):
        try:
            landmarks = np.array(item["image"]["face_landmarks"], dtype=np.float32) * args.scale
            left_eye = component_triplet(landmarks, LEFT_EYE)
            right_eye = component_triplet(landmarks, RIGHT_EYE)
            mouth = component_triplet(landmarks, MOUTH)
            save_dict[f"{item_idx:08d}"] = {
                "left_eye": list(left_eye),
                "right_eye": list(right_eye),
                "mouth": list(mouth),
            }

            if crop_dir and face_root:
                file_path = item["image"].get("file_path", f"{item_idx:08d}.png")
                img = read_image(face_root, file_path, item_idx, lmdb_keys)
                save_crop_preview(img, bbox_from_triplet(left_eye, args.enlarge_ratio), crop_dir / f"{item_idx:08d}_eye_left.png")
                save_crop_preview(img, bbox_from_triplet(right_eye, args.enlarge_ratio), crop_dir / f"{item_idx:08d}_eye_right.png")
                save_crop_preview(img, bbox_from_triplet(mouth, 1.0), crop_dir / f"{item_idx:08d}_mouth.png")
        except Exception as exc:
            print(f"Failed item {item_idx}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
            return 1

    save_path = Path(args.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(save_dict, str(save_path))
    print(f"Saved {len(save_dict)} landmark entries to {save_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
