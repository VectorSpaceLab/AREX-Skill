#!/usr/bin/env python3
"""Run a bounded SuperGlue Matching smoke test from an explicit repo root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

REQUIRED_WEIGHTS = [
    Path("models/weights/superpoint_v1.pth"),
    Path("models/weights/superglue_indoor.pth"),
    Path("models/weights/superglue_outdoor.pth"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small SuperGlue Matching smoke test without downloading data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the repository root that contains the models/ package.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device to run the smoke on.",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=192,
        help="Synthetic image side length, or resize target when local images are provided.",
    )
    parser.add_argument(
        "--max-keypoints",
        type=int,
        default=256,
        help="SuperPoint max_keypoints passed into Matching.",
    )
    parser.add_argument(
        "--sinkhorn-iterations",
        type=int,
        default=20,
        help="SuperGlue sinkhorn_iterations passed into Matching.",
    )
    parser.add_argument(
        "--image0",
        type=Path,
        default=None,
        help="Optional local grayscale image for the first view.",
    )
    parser.add_argument(
        "--image1",
        type=Path,
        default=None,
        help="Optional local grayscale image for the second view.",
    )
    return parser.parse_args()


def ensure_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")
    if not (repo_root / "models").is_dir():
        raise SystemExit(f"repo root does not contain models/: {repo_root}")
    missing = [rel.as_posix() for rel in REQUIRED_WEIGHTS if not (repo_root / rel).is_file()]
    if missing:
        print("Missing required checkpoint files:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(2)
    return repo_root


def add_to_path(repo_root: Path) -> None:
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def choose_device(choice: str) -> torch.device:
    if choice == "auto":
        choice = "cuda" if torch.cuda.is_available() else "cpu"
    if choice == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")
    return torch.device(choice)


def resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_grayscale(path: Path, image_size: int, repo_root: Path) -> np.ndarray:
    resolved = resolve_path(path, repo_root)
    image = cv2.imread(str(resolved), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit(f"could not read image: {resolved}")
    if image_size > 0:
        image = cv2.resize(image, (image_size, image_size), interpolation=cv2.INTER_AREA)
    return image


def build_synthetic_pair(image_size: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:image_size, 0:image_size]
    base = 0.25 + 0.2 * np.sin(xx / 9.0) + 0.2 * np.cos(yy / 13.0)
    base += 0.08 * rng.standard_normal((image_size, image_size))
    base = np.clip(base, 0.0, 1.0)
    image0 = (base * 255).astype(np.uint8)
    cv2.rectangle(image0, (image_size // 8, image_size // 8), (image_size // 2, image_size // 2), 240, 2)
    cv2.circle(image0, (3 * image_size // 4, image_size // 3), max(4, image_size // 9), 200, 2)
    cv2.line(image0, (8, image_size - 8), (image_size - 8, 8), 255, 2)
    cv2.putText(image0, "SG", (image_size // 5, 4 * image_size // 5), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 180, 2, cv2.LINE_AA)
    shift = max(2, image_size // 32)
    matrix = np.float32([[1, 0, shift], [0, 1, shift // 2]])
    image1 = cv2.warpAffine(
        image0,
        matrix,
        (image_size, image_size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT101,
    )
    image1 = cv2.GaussianBlur(image1, (3, 3), 0)
    image1 = cv2.convertScaleAbs(image1, alpha=0.96, beta=4)
    return image0, image1


def to_tensor(image: np.ndarray, device: torch.device) -> torch.Tensor:
    return torch.from_numpy(image.astype(np.float32) / 255.0)[None, None].to(device)


def first_item(container):
    if isinstance(container, (list, tuple)):
        return container[0]
    return container


def summarize_matches(pred: dict) -> str:
    matches0 = pred["matches0"]
    if matches0.ndim == 2:
        matches0 = matches0[0]
    valid = matches0 >= 0
    valid_count = int(valid.sum().item()) if matches0.numel() else 0
    total = int(matches0.numel())
    return f"{valid_count}/{total} valid matches"


def main() -> int:
    args = parse_args()
    repo_root = ensure_repo_root(args.repo_root)
    add_to_path(repo_root)

    from models.matching import Matching

    device = choose_device(args.device)
    print(f"[setup] repo_root={repo_root}")
    print(f"[setup] device={device}")
    print(f"[setup] image_size={args.image_size}")

    model = Matching(
        {
            "superpoint": {"max_keypoints": args.max_keypoints},
            "superglue": {"sinkhorn_iterations": args.sinkhorn_iterations},
        }
    ).eval().to(device)

    print(f"[setup] superpoint.max_keypoints={model.superpoint.config['max_keypoints']}")
    print(f"[setup] superglue.weights={model.superglue.config['weights']}")
    print(f"[setup] superglue.sinkhorn_iterations={model.superglue.config['sinkhorn_iterations']}")

    if (args.image0 is None) ^ (args.image1 is None):
        raise SystemExit("provide both --image0 and --image1, or neither to use the synthetic pair")

    if args.image0 is None:
        image0, image1 = build_synthetic_pair(args.image_size)
        print("[setup] using synthetic image pair")
    else:
        image0 = load_grayscale(args.image0, args.image_size, repo_root)
        image1 = load_grayscale(args.image1, args.image_size, repo_root)
        print(
            f"[setup] using local image pair: {resolve_path(args.image0, repo_root)} | {resolve_path(args.image1, repo_root)}"
        )

    tensor0 = to_tensor(image0, device)
    tensor1 = to_tensor(image1, device)

    with torch.no_grad():
        pred = model({"image0": tensor0, "image1": tensor1})

    required = {"matches0", "matches1", "matching_scores0", "matching_scores1"}
    missing = required.difference(pred)
    if missing:
        raise SystemExit(f"missing expected output keys: {sorted(missing)}")

    kpts0 = first_item(pred.get("keypoints0", []))
    kpts1 = first_item(pred.get("keypoints1", []))
    scores0 = first_item(pred.get("scores0", []))
    desc0 = first_item(pred.get("descriptors0", []))
    matches0 = pred["matches0"]
    if matches0.ndim == 2:
        matches0 = matches0[0]
    valid = matches0 >= 0
    match_count = int(valid.sum().item()) if matches0.numel() else 0
    total_count = int(matches0.numel())

    print(f"[smoke] keypoints0_shape={tuple(kpts0.shape)} keypoints1_shape={tuple(kpts1.shape)}")
    print(f"[smoke] scores0_shape={tuple(scores0.shape)} descriptors0_shape={tuple(desc0.shape)}")
    print(f"[smoke] matches0_shape={tuple(pred['matches0'].shape)} matches1_shape={tuple(pred['matches1'].shape)}")
    print(f"[smoke] {summarize_matches(pred)}")
    if total_count and match_count == 0:
        print("[smoke] note: zero matches is still a valid smoke outcome for a weak synthetic input")
    print("[ok] Matching forward path completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
