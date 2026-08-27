#!/usr/bin/env python3
"""Headless face_recognition API showcase for user-provided images.

Examples:
    python scripts/showcase_api.py --image ./unknown.jpg
    python scripts/showcase_api.py --image ./unknown.jpg --known-image ./known.jpg --tolerance 0.55
    python scripts/showcase_api.py --batch ./frame1.jpg ./frame2.jpg --model cnn --json

This is a safe adaptation of the repository's small image examples. It never
reads the original checkout's example files and never opens GUI windows.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any


def load_package() -> Any:
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated.*")
    try:
        import face_recognition
    except SystemExit as exc:
        raise RuntimeError(f"face_recognition import exited early: {exc!r}") from exc
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown dependency"
        if missing == "pkg_resources":
            raise RuntimeError(
                "face_recognition_models needs pkg_resources; install a compatible setuptools, "
                "for example: python -m pip install 'setuptools<81'"
            ) from exc
        raise RuntimeError(f"missing dependency {missing!r}; install face_recognition and its dependencies") from exc
    except BaseException as exc:
        raise RuntimeError(f"could not import face_recognition: {type(exc).__name__}: {exc}") from exc
    return face_recognition


def existing_file(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"not a readable image file: {path_text}")
    return path


def image_summary(face_recognition: Any, image_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    image = face_recognition.load_image_file(str(image_path), mode=args.mode)
    locations = face_recognition.face_locations(
        image,
        number_of_times_to_upsample=args.upsample,
        model=args.model,
    )
    landmarks = face_recognition.face_landmarks(
        image,
        face_locations=locations,
        model=args.landmarks_model,
    )
    encodings = face_recognition.face_encodings(
        image,
        known_face_locations=locations,
        num_jitters=args.num_jitters,
        model=args.encoding_model,
    )
    return {
        "image": str(image_path),
        "shape": list(image.shape),
        "model": args.model,
        "face_locations": [list(map(int, loc)) for loc in locations],
        "face_count": len(locations),
        "landmark_model": args.landmarks_model,
        "landmark_count": len(landmarks),
        "landmark_keys": [sorted(item.keys()) for item in landmarks],
        "encoding_model": args.encoding_model,
        "encoding_count": len(encodings),
        "_encodings": encodings,
    }


def compare_first_faces(face_recognition: Any, known: dict[str, Any], unknown: dict[str, Any], tolerance: float) -> dict[str, Any]:
    known_encodings = known.get("_encodings") or []
    unknown_encodings = unknown.get("_encodings") or []
    if not known_encodings:
        return {"ok": False, "error": "known image has no encodings"}
    if not unknown_encodings:
        return {"ok": False, "error": "unknown image has no encodings"}
    distances = face_recognition.face_distance([known_encodings[0]], unknown_encodings[0])
    matches = face_recognition.compare_faces([known_encodings[0]], unknown_encodings[0], tolerance=tolerance)
    return {
        "ok": True,
        "distance": float(distances[0]),
        "tolerance": tolerance,
        "match": bool(matches[0]),
    }


def batch_summary(face_recognition: Any, paths: list[Path], args: argparse.Namespace) -> dict[str, Any]:
    images = [face_recognition.load_image_file(str(path), mode=args.mode) for path in paths]
    shapes = [tuple(image.shape) for image in images]
    same_shape = len(set(shapes)) <= 1
    if not same_shape:
        return {
            "ok": False,
            "error": "batch_face_locations expects same-shaped images for reliable coordinates",
            "shapes": [list(shape) for shape in shapes],
        }
    locations = face_recognition.batch_face_locations(
        images,
        number_of_times_to_upsample=args.upsample,
        batch_size=args.batch_size,
    )
    return {
        "ok": True,
        "model": "cnn-batch",
        "batch_size": args.batch_size,
        "upsample": args.upsample,
        "items": [
            {
                "image": str(path),
                "shape": list(shape),
                "face_count": len(face_locations),
                "face_locations": [list(map(int, loc)) for loc in face_locations],
            }
            for path, shape, face_locations in zip(paths, shapes, locations)
        ],
    }


def strip_private_arrays(report: dict[str, Any]) -> dict[str, Any]:
    for key in ["target", "known"]:
        if key in report and isinstance(report[key], dict):
            report[key].pop("_encodings", None)
    return report


def print_human(report: dict[str, Any]) -> None:
    if "target" in report:
        target = report["target"]
        print(f"image: {target['image']}")
        print(f"shape: {target['shape']}")
        print(f"detector: {target['model']}")
        print(f"faces: {target['face_count']} {target['face_locations']}")
        print(f"landmarks: {target['landmark_count']} keys={target['landmark_keys']}")
        print(f"encodings: {target['encoding_count']} vectors")
    if "known" in report:
        known = report["known"]
        print(f"known_image: {known['image']} faces={known['face_count']} encodings={known['encoding_count']}")
    if "comparison" in report:
        comparison = report["comparison"]
        if comparison.get("ok"):
            print(
                "comparison: "
                f"distance={comparison['distance']:.6f} "
                f"tolerance={comparison['tolerance']} "
                f"match={comparison['match']}"
            )
        else:
            print(f"comparison: unavailable - {comparison.get('error')}")
    if "batch" in report:
        batch = report["batch"]
        if not batch.get("ok"):
            print(f"batch: failed - {batch.get('error')} shapes={batch.get('shapes')}")
        else:
            print(f"batch: {len(batch['items'])} images upsample={batch['upsample']} batch_size={batch['batch_size']}")
            for item in batch["items"]:
                print(f"  {item['image']}: faces={item['face_count']} {item['face_locations']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=existing_file, help="image to inspect or compare as unknown/target")
    parser.add_argument("--known-image", type=existing_file, help="known-person image used for comparison with --image")
    parser.add_argument("--batch", nargs="+", type=existing_file, help="same-shaped images to process with batch_face_locations")
    parser.add_argument("--model", choices=["hog", "cnn"], default="hog", help="detector model for --image; batch mode always uses the CNN detector internally")
    parser.add_argument("--upsample", type=int, default=1, help="face detector upsample count")
    parser.add_argument("--batch-size", type=int, default=128, help="batch_face_locations batch size")
    parser.add_argument("--mode", default="RGB", help="Pillow conversion mode passed to load_image_file")
    parser.add_argument("--landmarks-model", choices=["large", "small"], default="large", help="landmark model")
    parser.add_argument("--encoding-model", choices=["small", "large"], default="small", help="encoding model")
    parser.add_argument("--num-jitters", type=int, default=1, help="face encoding jitter count")
    parser.add_argument("--tolerance", type=float, default=0.6, help="comparison tolerance")
    parser.add_argument("--json", action="store_true", help="print JSON instead of human-readable text")
    args = parser.parse_args(argv)
    if not args.image and not args.batch:
        parser.error("provide --image, --batch, or both")
    if args.known_image and not args.image:
        parser.error("--known-image requires --image")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        face_recognition = load_package()
        report: dict[str, Any] = {"ok": True}
        if args.image:
            report["target"] = image_summary(face_recognition, args.image, args)
        if args.known_image:
            report["known"] = image_summary(face_recognition, args.known_image, args)
            report["comparison"] = compare_first_faces(face_recognition, report["known"], report["target"], args.tolerance)
            report["ok"] = report["ok"] and report["comparison"].get("ok", False)
        if args.batch:
            report["batch"] = batch_summary(face_recognition, args.batch, args)
            report["ok"] = report["ok"] and report["batch"].get("ok", False)
        strip_private_arrays(report)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_human(report)
        return 0 if report.get("ok") else 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
