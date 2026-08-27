#!/usr/bin/env python3
"""Safely inspect GeoAI training-data layouts.

This helper is read-only. It does not download data, start training, delete files,
write reports, contact model hubs, or read credentials. It validates common GeoAI
training layouts and samples a small number of files for channel/label sanity checks
when optional I/O libraries are available.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}
LABEL_EXTS = IMAGE_EXTS | {".txt"}
RASTER_EXTS = {".tif", ".tiff"}
TEXT_EXTS = {".txt"}


def _new_report(mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "status": "ok",
        "errors": [],
        "warnings": [],
        "counts": {},
        "samples": [],
        "details": {},
    }


def _add_error(report: Dict[str, Any], message: str) -> None:
    report["errors"].append(message)


def _add_warning(report: Dict[str, Any], message: str) -> None:
    report["warnings"].append(message)


def _finish_report(report: Dict[str, Any], strict: bool = False) -> Dict[str, Any]:
    if report["errors"]:
        report["status"] = "error"
    elif strict and report["warnings"]:
        report["status"] = "error"
        report["errors"].append("strict mode treats warnings as errors")
    elif report["warnings"]:
        report["status"] = "warn"
    else:
        report["status"] = "ok"
    return report


def _is_readable(path: Path) -> bool:
    try:
        if path.is_dir():
            next(path.iterdir(), None)
        else:
            with path.open("rb") as handle:
                handle.read(1)
        return True
    except Exception:
        return False


def _list_files(root: Path, exts: Iterable[str]) -> List[Path]:
    exts_norm = {e.lower() for e in exts}
    if not root.is_dir():
        return []
    return sorted(
        [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in exts_norm]
    )


def _stem_index(paths: Sequence[Path]) -> Dict[str, List[Path]]:
    index: Dict[str, List[Path]] = {}
    for path in paths:
        index.setdefault(path.stem, []).append(path)
    return index


def _path_summary(paths: Sequence[Path], limit: int = 10) -> List[str]:
    return [str(p) for p in list(paths)[:limit]]


def _import_optional(module_name: str):
    try:
        return __import__(module_name)
    except Exception:
        return None


def _inspect_image_metadata(path: Path) -> Dict[str, Any]:
    """Return lightweight image metadata when optional libs are available."""
    meta: Dict[str, Any] = {"path": str(path), "readable": _is_readable(path)}
    suffix = path.suffix.lower()

    if suffix in RASTER_EXTS:
        rasterio = _import_optional("rasterio")
        if rasterio is None:
            meta["skipped"] = "rasterio not installed"
            return meta
        try:
            with rasterio.open(path) as src:
                meta.update(
                    {
                        "kind": "raster",
                        "bands": src.count,
                        "width": src.width,
                        "height": src.height,
                        "dtypes": list(src.dtypes),
                        "nodata": src.nodata,
                        "crs_present": bool(src.crs),
                    }
                )
        except Exception as exc:  # pragma: no cover - defensive runtime helper
            meta["error"] = f"could not inspect raster: {exc}"
        return meta

    try:
        from PIL import Image  # type: ignore
    except Exception:
        meta["skipped"] = "Pillow not installed"
        return meta

    try:
        with Image.open(path) as img:
            meta.update(
                {
                    "kind": "image",
                    "bands": len(img.getbands()),
                    "width": img.size[0],
                    "height": img.size[1],
                    "mode": img.mode,
                }
            )
    except Exception as exc:  # pragma: no cover - defensive runtime helper
        meta["error"] = f"could not inspect image: {exc}"
    return meta


def _downsample_array(arr):
    """Keep value inspection bounded for very large masks."""
    try:
        height, width = arr.shape[-2], arr.shape[-1]
        max_pixels = 2_000_000
        pixels = int(height) * int(width)
        if pixels <= max_pixels:
            return arr
        step = int((pixels / max_pixels) ** 0.5) + 1
        return arr[..., ::step, ::step]
    except Exception:
        return arr


def _inspect_label_values(path: Path, expected_classes: Optional[int], ignore_index: Optional[int]) -> Dict[str, Any]:
    info: Dict[str, Any] = {"path": str(path), "suffix": path.suffix.lower()}

    if path.suffix.lower() in TEXT_EXTS:
        try:
            lines = [ln.strip() for ln in path.read_text(errors="replace").splitlines() if ln.strip()]
        except Exception as exc:
            info["error"] = f"could not read text label: {exc}"
            return info
        info.update({"kind": "text", "nonempty_lines": len(lines)})
        if lines:
            first = lines[0].split()
            info["first_line_fields"] = len(first)
            if len(first) < 5:
                info["warning"] = "YOLO-style labels usually need class + box fields"
        return info

    arr = None
    if path.suffix.lower() in RASTER_EXTS:
        rasterio = _import_optional("rasterio")
        if rasterio is not None:
            try:
                with rasterio.open(path) as src:
                    arr = src.read(1)
                    info.update({"kind": "raster", "width": src.width, "height": src.height})
            except Exception as exc:
                info["error"] = f"could not read raster label: {exc}"
                return info
        else:
            info["skipped"] = "rasterio not installed"
            return info
    else:
        try:
            from PIL import Image  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            info["skipped"] = "Pillow or numpy not installed"
            return info
        try:
            with Image.open(path) as img:
                arr = np.asarray(img.convert("L"))
                info.update({"kind": "image", "width": img.size[0], "height": img.size[1]})
        except Exception as exc:
            info["error"] = f"could not read image label: {exc}"
            return info

    try:
        import numpy as np  # type: ignore

        sample = _downsample_array(arr)
        unique = np.unique(sample)
        unique_list = [int(x) if float(x).is_integer() else float(x) for x in unique[:50]]
        info.update(
            {
                "kind": info.get("kind", "mask"),
                "min": float(np.nanmin(sample)),
                "max": float(np.nanmax(sample)),
                "unique_sample": unique_list,
                "unique_sample_count": int(len(unique)),
            }
        )
        if expected_classes is not None:
            valid_max = expected_classes - 1
            ignore_ok = ignore_index is not None
            invalid = []
            for val in unique[:50]:
                ival = int(val) if float(val).is_integer() else float(val)
                if ignore_ok and ival == ignore_index:
                    continue
                if ival < 0 or ival > valid_max:
                    invalid.append(ival)
            if invalid:
                info["warning"] = (
                    f"sample labels outside [0, {valid_max}]"
                    + (f" excluding ignore_index={ignore_index}" if ignore_ok else "")
                    + f": {invalid[:10]}"
                )
        if ignore_index is not None:
            info["ignore_index_present_in_sample"] = bool((sample == ignore_index).any())
    except Exception as exc:  # pragma: no cover - defensive runtime helper
        info["error"] = f"could not compute label values: {exc}"
    return info


def _validate_paths(report: Dict[str, Any], paths: Sequence[Tuple[str, Optional[Path], str]]) -> bool:
    ok = True
    for label, path, kind in paths:
        if path is None:
            _add_error(report, f"missing required argument: {label}")
            ok = False
            continue
        if not path.exists():
            _add_error(report, f"{label} does not exist: {path}")
            ok = False
            continue
        if kind == "dir" and not path.is_dir():
            _add_error(report, f"{label} is not a directory: {path}")
            ok = False
        elif kind == "file" and not path.is_file():
            _add_error(report, f"{label} is not a file: {path}")
            ok = False
        elif not _is_readable(path):
            _add_error(report, f"{label} is not readable: {path}")
            ok = False
    return ok


def _sample_file_checks(
    report: Dict[str, Any],
    image_paths: Sequence[Path],
    label_paths: Sequence[Path],
    expected_channels: Optional[int],
    expected_classes: Optional[int],
    ignore_index: Optional[int],
    sample_limit: int,
) -> None:
    for image_path, label_path in list(zip(image_paths, label_paths))[:sample_limit]:
        sample: Dict[str, Any] = {"image": str(image_path), "label": str(label_path)}
        img_meta = _inspect_image_metadata(image_path)
        sample["image_meta"] = img_meta
        if expected_channels is not None and "bands" in img_meta:
            if img_meta["bands"] != expected_channels:
                _add_warning(
                    report,
                    f"{image_path} has {img_meta['bands']} band(s), expected {expected_channels}",
                )
        elif expected_channels is not None and img_meta.get("skipped"):
            _add_warning(report, f"could not verify channel count for {image_path}: {img_meta['skipped']}")

        label_info = _inspect_label_values(label_path, expected_classes, ignore_index)
        sample["label_meta"] = label_info
        if label_info.get("warning"):
            _add_warning(report, f"{label_path}: {label_info['warning']}")
        if label_info.get("error"):
            _add_warning(report, f"{label_path}: {label_info['error']}")
        report["samples"].append(sample)


def check_pairs(args: argparse.Namespace) -> Dict[str, Any]:
    report = _new_report("pairs")
    images_dir = Path(args.images_dir) if args.images_dir else None
    labels_dir = Path(args.labels_dir) if args.labels_dir else None
    if not _validate_paths(report, [("images-dir", images_dir, "dir"), ("labels-dir", labels_dir, "dir")]):
        return _finish_report(report, args.strict)

    assert images_dir is not None and labels_dir is not None
    images = _list_files(images_dir, IMAGE_EXTS)
    labels = _list_files(labels_dir, LABEL_EXTS)
    report["counts"].update({"images": len(images), "labels": len(labels)})

    if not images and not args.allow_empty:
        _add_error(report, f"no image files found in {images_dir}")
    if not labels and not args.allow_empty:
        _add_error(report, f"no label files found in {labels_dir}")

    image_index = _stem_index(images)
    label_index = _stem_index(labels)
    image_stems = set(image_index)
    label_stems = set(label_index)
    missing_labels = sorted(image_stems - label_stems)
    extra_labels = sorted(label_stems - image_stems)
    duplicate_images = {k: [str(p) for p in v] for k, v in image_index.items() if len(v) > 1}
    duplicate_labels = {k: [str(p) for p in v] for k, v in label_index.items() if len(v) > 1}

    report["details"].update(
        {
            "missing_label_stems": missing_labels[:50],
            "extra_label_stems": extra_labels[:50],
            "duplicate_image_stems": duplicate_images,
            "duplicate_label_stems": duplicate_labels,
        }
    )
    if missing_labels:
        _add_error(report, f"{len(missing_labels)} image(s) lack matching labels")
    if extra_labels:
        _add_warning(report, f"{len(extra_labels)} label file(s) have no matching image")
    if duplicate_images:
        _add_warning(report, f"duplicate image stems: {list(duplicate_images)[:10]}")
    if duplicate_labels:
        _add_warning(report, f"duplicate label stems: {list(duplicate_labels)[:10]}")

    matched = sorted(image_stems & label_stems)
    matched_images = [image_index[s][0] for s in matched]
    matched_labels = [label_index[s][0] for s in matched]
    _sample_file_checks(
        report,
        matched_images,
        matched_labels,
        args.expected_channels,
        args.expected_classes,
        args.ignore_index,
        max(args.sample_limit, 0),
    )
    return _finish_report(report, args.strict)


def check_coco(args: argparse.Namespace) -> Dict[str, Any]:
    report = _new_report("coco")
    images_dir = Path(args.images_dir) if args.images_dir else None
    annotations = Path(args.annotations) if args.annotations else None
    labels_dir = Path(args.labels_dir) if args.labels_dir else None

    paths = [("images-dir", images_dir, "dir"), ("annotations", annotations, "file")]
    if labels_dir is not None:
        paths.append(("labels-dir", labels_dir, "dir"))
    if not _validate_paths(report, paths):
        return _finish_report(report, args.strict)

    assert images_dir is not None and annotations is not None
    try:
        data = json.loads(annotations.read_text())
    except Exception as exc:
        _add_error(report, f"could not parse COCO JSON: {exc}")
        return _finish_report(report, args.strict)

    images = data.get("images", [])
    annotations_list = data.get("annotations", [])
    categories = data.get("categories", [])
    report["counts"].update(
        {
            "coco_images": len(images),
            "coco_annotations": len(annotations_list),
            "coco_categories": len(categories),
        }
    )
    if not isinstance(images, list) or not isinstance(annotations_list, list):
        _add_error(report, "COCO JSON must contain list fields 'images' and 'annotations'")
        return _finish_report(report, args.strict)
    if not categories:
        _add_warning(report, "COCO JSON has no categories; class_names/num_classes may be ambiguous")

    missing_images: List[str] = []
    existing_images: List[Path] = []
    for img in images:
        name = img.get("file_name") if isinstance(img, dict) else None
        if not name:
            _add_warning(report, "an image entry is missing file_name")
            continue
        image_path = images_dir / str(name)
        if image_path.is_file():
            existing_images.append(image_path)
        else:
            missing_images.append(str(name))
    report["details"]["missing_coco_images"] = missing_images[:50]
    if missing_images:
        _add_error(report, f"{len(missing_images)} COCO image file(s) missing under {images_dir}")

    if labels_dir is not None:
        label_index = _stem_index(_list_files(labels_dir, LABEL_EXTS))
        missing_label_masks = [p.stem for p in existing_images if p.stem not in label_index]
        report["details"]["missing_optional_label_masks"] = missing_label_masks[:50]
        if missing_label_masks:
            _add_warning(report, f"{len(missing_label_masks)} COCO image(s) lack same-stem label masks in {labels_dir}")
        matched_images = [p for p in existing_images if p.stem in label_index]
        matched_labels = [label_index[p.stem][0] for p in matched_images]
        _sample_file_checks(
            report,
            matched_images,
            matched_labels,
            args.expected_channels,
            args.expected_classes,
            args.ignore_index,
            max(args.sample_limit, 0),
        )
    else:
        for image_path in existing_images[: max(args.sample_limit, 0)]:
            meta = _inspect_image_metadata(image_path)
            if args.expected_channels is not None and "bands" in meta and meta["bands"] != args.expected_channels:
                _add_warning(report, f"{image_path} has {meta['bands']} band(s), expected {args.expected_channels}")
            report["samples"].append({"image": str(image_path), "image_meta": meta})

    return _finish_report(report, args.strict)


def check_yolo(args: argparse.Namespace) -> Dict[str, Any]:
    report = _new_report("yolo")
    root = Path(args.root) if args.root else None
    if not _validate_paths(report, [("root", root, "dir")]):
        return _finish_report(report, args.strict)
    assert root is not None

    images_dir = root / args.images_subdir
    labels_dir = root / args.labels_subdir
    if not _validate_paths(report, [("images subdir", images_dir, "dir"), ("labels subdir", labels_dir, "dir")]):
        return _finish_report(report, args.strict)

    images = _list_files(images_dir, IMAGE_EXTS)
    labels = _list_files(labels_dir, LABEL_EXTS)
    label_index = _stem_index(labels)
    report["counts"].update({"images": len(images), "labels": len(labels)})

    if not images and not args.allow_empty:
        _add_error(report, f"no images found in {images_dir}")
    if not labels and not args.allow_empty:
        _add_error(report, f"no labels found in {labels_dir}")

    missing = [p.stem for p in images if p.stem not in label_index]
    extras = sorted(set(label_index) - {p.stem for p in images})
    text_labels = [p for p in labels if p.suffix.lower() in TEXT_EXTS]
    raster_labels = [p for p in labels if p.suffix.lower() not in TEXT_EXTS]
    report["details"].update(
        {
            "missing_label_stems": missing[:50],
            "extra_label_stems": extras[:50],
            "text_label_count": len(text_labels),
            "raster_or_image_label_count": len(raster_labels),
        }
    )
    if missing:
        _add_error(report, f"{len(missing)} YOLO image(s) lack same-stem labels")
    if extras:
        _add_warning(report, f"{len(extras)} label file(s) do not match images")
    if text_labels and raster_labels:
        _add_warning(report, "labels directory mixes text labels and raster/image labels; confirm the trainer supports this")

    matched_images = [p for p in images if p.stem in label_index]
    matched_labels = [label_index[p.stem][0] for p in matched_images]
    _sample_file_checks(
        report,
        matched_images,
        matched_labels,
        args.expected_channels,
        args.expected_classes,
        args.ignore_index,
        max(args.sample_limit, 0),
    )
    return _finish_report(report, args.strict)


def _find_imagefolder_root(root: Path, max_depth: int = 3) -> Path:
    """Mimic GeoAI's tolerance for nested extracted ImageFolder roots."""
    def has_class_dirs(candidate: Path) -> bool:
        dirs = [p for p in candidate.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not dirs:
            return False
        return any(_list_files(d, IMAGE_EXTS) for d in dirs)

    if has_class_dirs(root):
        return root

    for candidate in sorted([p for p in root.rglob("*") if p.is_dir()]):
        rel_depth = len(candidate.relative_to(root).parts)
        if rel_depth > max_depth:
            continue
        if has_class_dirs(candidate):
            return candidate
    return root


def check_imagefolder(args: argparse.Namespace) -> Dict[str, Any]:
    report = _new_report("imagefolder")
    root = Path(args.root) if args.root else None
    if not _validate_paths(report, [("root", root, "dir")]):
        return _finish_report(report, args.strict)
    assert root is not None

    detected_root = _find_imagefolder_root(root)
    if detected_root != root:
        _add_warning(report, f"using nested ImageFolder root: {detected_root}")
    class_dirs = sorted([p for p in detected_root.iterdir() if p.is_dir() and not p.name.startswith(".")])
    class_counts: Dict[str, int] = {}
    sample_images: List[Path] = []
    for class_dir in class_dirs:
        files = _list_files(class_dir, IMAGE_EXTS)
        if files:
            class_counts[class_dir.name] = len(files)
            sample_images.extend(files[: max(args.sample_limit, 0)])

    report["details"].update({"root_used": str(detected_root), "class_counts": class_counts})
    report["counts"].update({"classes": len(class_counts), "images": sum(class_counts.values())})
    if not class_counts and not args.allow_empty:
        _add_error(report, f"no class subdirectories with images found under {detected_root}")

    if args.expected_classes is not None and len(class_counts) != args.expected_classes:
        _add_warning(report, f"found {len(class_counts)} classes, expected {args.expected_classes}")

    for image_path in sample_images[: max(args.sample_limit, 0)]:
        meta = _inspect_image_metadata(image_path)
        if args.expected_channels is not None and "bands" in meta and meta["bands"] != args.expected_channels:
            _add_warning(report, f"{image_path} has {meta['bands']} band(s), expected {args.expected_channels}")
        report["samples"].append({"image": str(image_path), "image_meta": meta})

    return _finish_report(report, args.strict)


def print_human(report: Dict[str, Any]) -> None:
    print(f"GeoAI training layout check: {report['mode']} [{report['status']}]")
    if report["counts"]:
        print("Counts:")
        for key, value in report["counts"].items():
            print(f"  - {key}: {value}")
    if report["warnings"]:
        print("Warnings:")
        for item in report["warnings"]:
            print(f"  - {item}")
    if report["errors"]:
        print("Errors:")
        for item in report["errors"]:
            print(f"  - {item}")
    if report["samples"]:
        print(f"Sampled files: {len(report['samples'])}")
        for sample in report["samples"][:5]:
            image = sample.get("image")
            label = sample.get("label")
            print(f"  - image: {image}")
            if label:
                print(f"    label: {label}")
            image_meta = sample.get("image_meta") or {}
            if image_meta.get("bands") is not None:
                print(
                    f"    image shape: bands={image_meta.get('bands')}, "
                    f"width={image_meta.get('width')}, height={image_meta.get('height')}"
                )
            label_meta = sample.get("label_meta") or {}
            if label_meta.get("unique_sample") is not None:
                print(f"    label values sample: {label_meta.get('unique_sample')[:20]}")
            elif label_meta.get("kind") == "text":
                print(f"    text label lines: {label_meta.get('nonempty_lines')}")
    if report["status"] == "ok":
        print("Result: layout checks passed.")
    elif report["status"] == "warn":
        print("Result: usable with warnings; inspect warnings before training.")
    else:
        print("Result: fix errors before training.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validator for GeoAI training layouts. Modes: pairs for "
            "image/mask dirs, coco for COCO JSON, yolo for root/images+labels, "
            "and imagefolder for class-named directories."
        )
    )
    parser.add_argument("--mode", choices=["pairs", "coco", "yolo", "imagefolder"], required=True)
    parser.add_argument("--root", help="Root directory for yolo or imagefolder mode.")
    parser.add_argument("--images-dir", help="Images directory for pairs or coco mode.")
    parser.add_argument("--labels-dir", help="Labels/masks directory for pairs mode, or optional COCO sidecar masks.")
    parser.add_argument("--annotations", help="COCO annotations JSON for coco mode.")
    parser.add_argument("--images-subdir", default="images", help="YOLO images subdirectory name (default: images).")
    parser.add_argument("--labels-subdir", default="labels", help="YOLO labels subdirectory name (default: labels).")
    parser.add_argument("--expected-channels", type=int, help="Expected input band/channel count for sampled images.")
    parser.add_argument("--expected-classes", type=int, help="Expected class count for sampled masks, COCO categories, or ImageFolder classes.")
    parser.add_argument("--ignore-index", type=int, help="Mask value to treat as ignored during label sanity checks.")
    parser.add_argument("--sample-limit", type=int, default=3, help="Maximum number of matched samples to inspect (default: 3).")
    parser.add_argument("--allow-empty", action="store_true", help="Do not fail solely because a discovered directory is empty.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "pairs":
        report = check_pairs(args)
    elif args.mode == "coco":
        report = check_coco(args)
    elif args.mode == "yolo":
        report = check_yolo(args)
    elif args.mode == "imagefolder":
        report = check_imagefolder(args)
    else:  # pragma: no cover - argparse enforces choices
        parser.error(f"unknown mode: {args.mode}")
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    return 0 if report["status"] in {"ok", "warn"} else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
