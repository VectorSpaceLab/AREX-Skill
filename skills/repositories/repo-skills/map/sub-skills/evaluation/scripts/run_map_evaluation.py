#!/usr/bin/env python3
"""Safe VOC-style AP/mAP evaluator with explicit input and output paths.

Provenance: the AP/mAP metric behavior, input text conventions, and CLI option
names are adapted from the source repository's Apache-2.0 ``main.py`` evaluator.
This bundled version is self-contained, avoids changing the caller's cwd, refuses
to overwrite output directories unless requested, and disables plots/animation by
default.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_MIN_OVERLAP = 0.5
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


class EvaluationError(Exception):
    """User-facing evaluation failure."""


@dataclass
class GroundTruthObject:
    class_name: str
    bbox: Tuple[float, float, float, float]
    difficult: bool = False
    used: bool = False


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]
    file_id: str


@dataclass
class DetectionRecord:
    class_name: str
    file_id: str
    confidence: float
    bbox: Tuple[float, float, float, float]
    status: str
    iou: float
    min_overlap: float
    matched_gt_bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class ClassResult:
    ap: float
    precision: List[float]
    recall: List[float]
    monotonic_precision: List[float]
    monotonic_recall: List[float]
    tp: int
    fp: int
    ignored_detections: int
    npos: int
    lamr: float
    fppi: List[float] = field(default_factory=list)
    miss_rate: List[float] = field(default_factory=list)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run VOC-style AP/mAP evaluation on explicit folder paths."
    )
    parser.add_argument(
        "--ground-truth-dir",
        required=True,
        type=Path,
        help="Directory of one ground-truth .txt file per image.",
    )
    parser.add_argument(
        "--detection-results-dir",
        required=True,
        type=Path,
        help="Directory of one detection-results .txt file per image.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where output.txt and optional artifacts will be written.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=None,
        help="Optional image directory used only with --animation.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate --output-dir when it already contains files.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print only the final mAP line and essential errors.",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        nargs="+",
        default=[],
        metavar="CLASS",
        help="Ignore one or more class names during GT counting and DR summaries.",
    )
    parser.add_argument(
        "--set-class-iou",
        nargs="+",
        default=None,
        metavar=("CLASS_OR_IOU"),
        help="Pairs of CLASS IOU values, e.g. --set-class-iou person 0.7 car 0.6.",
    )
    parser.add_argument(
        "--min-overlap",
        type=float,
        default=DEFAULT_MIN_OVERLAP,
        help="Default IoU threshold for classes without a custom value (default: 0.5).",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Write optional PNG plots. Requires matplotlib; off by default.",
    )
    parser.add_argument(
        "-np",
        "--no-plot",
        action="store_true",
        help="Compatibility flag: disable plots even if --plot is present.",
    )
    parser.add_argument(
        "--animation",
        action="store_true",
        help="Write optional annotated image frames. Requires opencv-python and --images-dir; off by default.",
    )
    parser.add_argument(
        "-na",
        "--no-animation",
        action="store_true",
        help="Compatibility flag: disable animation even if --animation is present.",
    )
    args = parser.parse_args(argv)
    if args.no_plot:
        args.plot = False
    if args.no_animation:
        args.animation = False
    return args


def ensure_threshold(value: float, label: str) -> None:
    if not (0.0 < value < 1.0):
        raise EvaluationError(f"{label} must be between 0.0 and 1.0, exclusive; got {value!r}.")


def prepare_output_dir(output_dir: Path, overwrite: bool) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise EvaluationError(f"Output path exists but is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            if not overwrite:
                raise EvaluationError(
                    "Output directory already exists and is not empty. "
                    "Choose a new --output-dir or pass --overwrite to delete and recreate it."
                )
            shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def list_txt_files(folder: Path, label: str) -> List[Path]:
    if not folder.exists():
        raise EvaluationError(f"Missing {label} directory: {folder}")
    if not folder.is_dir():
        raise EvaluationError(f"{label} path is not a directory: {folder}")
    files = sorted(folder.glob("*.txt"))
    if not files:
        raise EvaluationError(f"No .txt files found in {label} directory: {folder}")
    return files


def check_matching_file_sets(gt_files: Sequence[Path], dr_files: Sequence[Path]) -> None:
    gt_ids = {p.stem for p in gt_files}
    dr_ids = {p.stem for p in dr_files}
    missing_dr = sorted(gt_ids - dr_ids)
    missing_gt = sorted(dr_ids - gt_ids)
    messages: List[str] = []
    if missing_dr:
        preview = ", ".join(missing_dr[:10])
        more = " ..." if len(missing_dr) > 10 else ""
        messages.append(f"missing detection-results .txt for image ids: {preview}{more}")
    if missing_gt:
        preview = ", ".join(missing_gt[:10])
        more = " ..." if len(missing_gt) > 10 else ""
        messages.append(f"missing ground-truth .txt for image ids: {preview}{more}")
    if messages:
        raise EvaluationError(
            "Ground-truth and detection-results file sets must match by basename; "
            + "; ".join(messages)
        )


def parse_bbox(parts: Sequence[str], path: Path, line_no: int) -> Tuple[float, float, float, float]:
    try:
        left, top, right, bottom = (float(v) for v in parts)
    except ValueError as exc:
        raise EvaluationError(
            f"File {path} line {line_no} has non-numeric box coordinates: {' '.join(parts)}"
        ) from exc
    if right < left or bottom < top:
        raise EvaluationError(
            f"File {path} line {line_no} has invalid box order; expected left <= right and top <= bottom."
        )
    return left, top, right, bottom


def parse_ground_truth_file(path: Path, ignored: set[str]) -> List[GroundTruthObject]:
    objects: List[GroundTruthObject] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 5:
                class_name, *box_parts = parts
                difficult = False
            elif len(parts) == 6 and parts[-1] == "difficult":
                class_name, *box_parts, _ = parts
                difficult = True
            else:
                raise EvaluationError(
                    f"File {path} line {line_no} is in the wrong ground-truth format. "
                    "Expected: <class_name> <left> <top> <right> <bottom> [difficult]; "
                    f"received: {line}"
                )
            if class_name in ignored:
                continue
            objects.append(GroundTruthObject(class_name, parse_bbox(box_parts, path, line_no), difficult))
    return objects


def parse_detection_file(path: Path, ignored: set[str]) -> List[Detection]:
    detections: List[Detection] = []
    file_id = path.stem
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 6:
                raise EvaluationError(
                    f"File {path} line {line_no} is in the wrong detection-results format. "
                    "Expected: <class_name> <confidence> <left> <top> <right> <bottom>; "
                    f"received: {line}"
                )
            class_name, confidence_text, *box_parts = parts
            if class_name in ignored:
                continue
            try:
                confidence = float(confidence_text)
            except ValueError as exc:
                raise EvaluationError(
                    f"File {path} line {line_no} has non-numeric confidence: {confidence_text}"
                ) from exc
            detections.append(Detection(class_name, confidence, parse_bbox(box_parts, path, line_no), file_id))
    return detections


def load_inputs(
    gt_dir: Path, dr_dir: Path, ignored: set[str]
) -> Tuple[Dict[str, List[GroundTruthObject]], List[Detection], Dict[str, int], Dict[str, int], Dict[str, int]]:
    gt_files = list_txt_files(gt_dir, "ground-truth")
    dr_files = list_txt_files(dr_dir, "detection-results")
    check_matching_file_sets(gt_files, dr_files)

    gt_by_file: Dict[str, List[GroundTruthObject]] = {}
    gt_counter_per_class: Dict[str, int] = {}
    counter_images_per_class: Dict[str, int] = {}
    for gt_file in gt_files:
        objects = parse_ground_truth_file(gt_file, ignored)
        gt_by_file[gt_file.stem] = objects
        seen_non_difficult_classes: set[str] = set()
        for obj in objects:
            if obj.difficult:
                continue
            gt_counter_per_class[obj.class_name] = gt_counter_per_class.get(obj.class_name, 0) + 1
            seen_non_difficult_classes.add(obj.class_name)
        for class_name in seen_non_difficult_classes:
            counter_images_per_class[class_name] = counter_images_per_class.get(class_name, 0) + 1

    if not gt_counter_per_class:
        raise EvaluationError(
            "No evaluable ground-truth objects remain after ignored classes and difficult-only rows."
        )

    detections: List[Detection] = []
    det_counter_per_class: Dict[str, int] = {}
    for dr_file in dr_files:
        parsed = parse_detection_file(dr_file, ignored)
        detections.extend(parsed)
        for det in parsed:
            det_counter_per_class[det.class_name] = det_counter_per_class.get(det.class_name, 0) + 1

    return gt_by_file, detections, gt_counter_per_class, counter_images_per_class, det_counter_per_class


def validate_class_iou(raw_values: Optional[Sequence[str]], gt_classes: Sequence[str]) -> Dict[str, float]:
    if not raw_values:
        return {}
    if len(raw_values) % 2 != 0:
        raise EvaluationError(
            "--set-class-iou requires CLASS IOU pairs, e.g. --set-class-iou person 0.7 car 0.6"
        )
    gt_set = set(gt_classes)
    overrides: Dict[str, float] = {}
    for class_name, iou_text in zip(raw_values[::2], raw_values[1::2]):
        if class_name not in gt_set:
            raise EvaluationError(
                f'Unknown or ignored class "{class_name}" in --set-class-iou. '
                "Custom IoU classes must be present in non-ignored, non-difficult ground truth."
            )
        if class_name in overrides:
            raise EvaluationError(f'Duplicate class "{class_name}" in --set-class-iou.')
        try:
            iou = float(iou_text)
        except ValueError as exc:
            raise EvaluationError(f'IoU for class "{class_name}" is not a number: {iou_text}') from exc
        ensure_threshold(iou, f'IoU for class "{class_name}"')
        overrides[class_name] = iou
    return overrides


def iou(box_a: Tuple[float, float, float, float], box_b: Tuple[float, float, float, float]) -> float:
    left = max(box_a[0], box_b[0])
    top = max(box_a[1], box_b[1])
    right = min(box_a[2], box_b[2])
    bottom = min(box_a[3], box_b[3])
    width = right - left + 1.0
    height = bottom - top + 1.0
    if width <= 0 or height <= 0:
        return 0.0
    intersection = width * height
    area_a = (box_a[2] - box_a[0] + 1.0) * (box_a[3] - box_a[1] + 1.0)
    area_b = (box_b[2] - box_b[0] + 1.0) * (box_b[3] - box_b[1] + 1.0)
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def voc_ap(recall: Sequence[float], precision: Sequence[float]) -> Tuple[float, List[float], List[float]]:
    mrec = [0.0, *recall, 1.0]
    mpre = [0.0, *precision, 0.0]
    for idx in range(len(mpre) - 2, -1, -1):
        mpre[idx] = max(mpre[idx], mpre[idx + 1])
    ap = 0.0
    for idx in range(1, len(mrec)):
        if mrec[idx] != mrec[idx - 1]:
            ap += (mrec[idx] - mrec[idx - 1]) * mpre[idx]
    return ap, mrec, mpre


def log_average_miss_rate(precision: Sequence[float], recall: Sequence[float]) -> Tuple[float, List[float], List[float]]:
    if not precision:
        return 0.0, [], []
    fppi = [1.0 - p for p in precision]
    miss_rate = [1.0 - r for r in recall]
    fppi_tmp = [-1.0, *fppi]
    miss_tmp = [1.0, *miss_rate]
    refs = [10 ** (-2.0 + idx * (2.0 / 8.0)) for idx in range(9)]
    sampled: List[float] = []
    for ref in refs:
        chosen = miss_tmp[0]
        for fppi_value, miss_value in zip(fppi_tmp, miss_tmp):
            if fppi_value <= ref:
                chosen = miss_value
        sampled.append(chosen)
    lamr = math.exp(sum(math.log(max(1e-10, value)) for value in sampled) / len(sampled))
    return lamr, miss_rate, fppi


def evaluate(
    gt_by_file: Dict[str, List[GroundTruthObject]],
    detections: Sequence[Detection],
    gt_counter_per_class: Dict[str, int],
    counter_images_per_class: Dict[str, int],
    min_overlap: float,
    class_iou: Dict[str, float],
) -> Tuple[Dict[str, ClassResult], List[DetectionRecord]]:
    results: Dict[str, ClassResult] = {}
    records: List[DetectionRecord] = []
    gt_classes = sorted(gt_counter_per_class)

    for class_name in gt_classes:
        class_detections = sorted(
            (d for d in detections if d.class_name == class_name),
            key=lambda det: det.confidence,
            reverse=True,
        )
        nd = len(class_detections)
        tp = [0] * nd
        fp = [0] * nd
        ignored_detections = 0
        threshold = class_iou.get(class_name, min_overlap)

        for idx, detection in enumerate(class_detections):
            candidates = gt_by_file[detection.file_id]
            ovmax = 0.0
            gt_match: Optional[GroundTruthObject] = None
            for obj in candidates:
                if obj.class_name != class_name:
                    continue
                overlap = iou(detection.bbox, obj.bbox)
                if overlap > ovmax:
                    ovmax = overlap
                    gt_match = obj

            status = "NO_MATCH"
            matched_gt_bbox = gt_match.bbox if gt_match is not None else None
            if gt_match is not None and ovmax >= threshold:
                if gt_match.difficult:
                    ignored_detections += 1
                    status = "DIFFICULT_IGNORED"
                elif not gt_match.used:
                    tp[idx] = 1
                    gt_match.used = True
                    status = "MATCH"
                else:
                    fp[idx] = 1
                    status = "REPEATED_MATCH"
            else:
                fp[idx] = 1
                if gt_match is not None and ovmax > 0:
                    status = "INSUFFICIENT_OVERLAP"

            records.append(
                DetectionRecord(
                    class_name=class_name,
                    file_id=detection.file_id,
                    confidence=detection.confidence,
                    bbox=detection.bbox,
                    status=status,
                    iou=ovmax,
                    min_overlap=threshold,
                    matched_gt_bbox=matched_gt_bbox,
                )
            )

        for idx in range(1, nd):
            fp[idx] += fp[idx - 1]
            tp[idx] += tp[idx - 1]

        npos = gt_counter_per_class[class_name]
        recall = [value / npos for value in tp]
        precision = [tp_i / (tp_i + fp_i) if (tp_i + fp_i) else 0.0 for tp_i, fp_i in zip(tp, fp)]
        ap, mrec, mpre = voc_ap(recall, precision)
        lamr, miss_rate, fppi = log_average_miss_rate(precision, recall)
        results[class_name] = ClassResult(
            ap=ap,
            precision=precision,
            recall=recall,
            monotonic_precision=mpre,
            monotonic_recall=mrec,
            tp=tp[-1] if tp else 0,
            fp=fp[-1] if fp else 0,
            ignored_detections=ignored_detections,
            npos=npos,
            lamr=lamr,
            fppi=fppi,
            miss_rate=miss_rate,
        )

    return results, records


def fmt_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def rounded(values: Iterable[float]) -> List[str]:
    return [f"{value:.2f}" for value in values]


def write_text_outputs(
    output_dir: Path,
    results: Dict[str, ClassResult],
    gt_counter_per_class: Dict[str, int],
    det_counter_per_class: Dict[str, int],
    ignored_classes: Sequence[str],
    class_iou: Dict[str, float],
    min_overlap: float,
) -> float:
    output_txt = output_dir / "output.txt"
    gt_classes = sorted(results)
    mean_ap = sum(result.ap for result in results.values()) / len(results)
    count_true_positives = {class_name: result.tp for class_name, result in results.items()}

    with output_txt.open("w", encoding="utf-8") as handle:
        handle.write("# AP and precision/recall per class\n")
        for class_name in gt_classes:
            result = results[class_name]
            handle.write(
                f"{fmt_percent(result.ap)} = {class_name} AP\n"
                f" Precision: {rounded(result.precision)}\n"
                f" Recall :{rounded(result.recall)}\n\n"
            )
        handle.write("\n# mAP of all classes\n")
        handle.write(f"mAP = {fmt_percent(mean_ap)}\n")
        handle.write("\n# Number of ground-truth objects per class\n")
        for class_name in sorted(gt_counter_per_class):
            handle.write(f"{class_name}: {gt_counter_per_class[class_name]}\n")
        handle.write("\n# Number of detected objects per class\n")
        for class_name in sorted(det_counter_per_class):
            n_det = det_counter_per_class[class_name]
            if class_name in results:
                tp = results[class_name].tp
                fp = results[class_name].fp
                ignored = results[class_name].ignored_detections
            else:
                tp = 0
                fp = n_det
                ignored = 0
            ignored_text = f", ignored:{ignored}" if ignored else ""
            handle.write(f"{class_name}: {n_det} (tp:{tp}, fp:{fp}{ignored_text})\n")

    summary = {
        "metric": "PASCAL VOC-style all-point AP with inclusive-pixel IoU",
        "mAP": mean_ap,
        "mAP_percent": round(mean_ap * 100.0, 6),
        "default_iou_threshold": min_overlap,
        "class_iou_overrides": class_iou,
        "ignored_classes": list(ignored_classes),
        "classes": {
            class_name: {
                "AP": result.ap,
                "AP_percent": round(result.ap * 100.0, 6),
                "npos": result.npos,
                "tp": result.tp,
                "fp": result.fp,
                "ignored_detections": result.ignored_detections,
                "precision": result.precision,
                "recall": result.recall,
                "log_average_miss_rate": result.lamr,
            }
            for class_name, result in results.items()
        },
        "detected_objects_per_class": dict(sorted(det_counter_per_class.items())),
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return mean_ap


def write_plots(
    output_dir: Path,
    results: Dict[str, ClassResult],
    gt_counter_per_class: Dict[str, int],
    det_counter_per_class: Dict[str, int],
    mean_ap: float,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise EvaluationError(
            'Optional dependency "matplotlib" is not installed. Omit --plot or install matplotlib.'
        ) from exc

    classes_dir = output_dir / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)

    for class_name, result in sorted(results.items()):
        fig, ax = plt.subplots()
        ax.plot(result.recall, result.precision, marker="o")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.05)
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title(f"{class_name} AP = {fmt_percent(result.ap)}")
        fig.tight_layout()
        fig.savefig(classes_dir / f"{class_name}.png")
        plt.close(fig)

    def barh_plot(values: Dict[str, float], title: str, xlabel: str, path: Path) -> None:
        names = list(values.keys())
        vals = [values[name] for name in names]
        fig, ax = plt.subplots(figsize=(8, max(3, 0.3 * len(names))))
        ax.barh(names, vals, color="royalblue")
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)

    barh_plot(
        dict(sorted((k, float(v)) for k, v in gt_counter_per_class.items())),
        "ground-truth",
        "Number of objects per class",
        output_dir / "ground-truth-info.png",
    )
    barh_plot(
        dict(sorted((k, float(v)) for k, v in det_counter_per_class.items())),
        "detection-results",
        "Number of detections per class",
        output_dir / "detection-results-info.png",
    )
    barh_plot(
        {k: v.lamr for k, v in sorted(results.items())},
        "log-average miss rate",
        "log-average miss rate",
        output_dir / "lamr.png",
    )
    barh_plot(
        {k: v.ap for k, v in sorted(results.items())},
        f"mAP = {fmt_percent(mean_ap)}",
        "Average Precision",
        output_dir / "mAP.png",
    )


def find_image(images_dir: Path, file_id: str) -> Path:
    candidates: List[Path] = []
    for suffix in IMAGE_EXTENSIONS:
        candidates.extend(images_dir.glob(file_id + suffix))
        candidates.extend(images_dir.glob(file_id + suffix.upper()))
    unique = sorted(set(candidates))
    if not unique:
        raise EvaluationError(f"Animation requested but no image file matches id {file_id!r} in {images_dir}")
    if len(unique) > 1:
        names = ", ".join(p.name for p in unique)
        raise EvaluationError(f"Animation requested but multiple image files match id {file_id!r}: {names}")
    return unique[0]


def int_box(box: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    return tuple(int(round(value)) for value in box)  # type: ignore[return-value]


def write_animation(output_dir: Path, images_dir: Optional[Path], records: Sequence[DetectionRecord]) -> None:
    if images_dir is None:
        raise EvaluationError("--animation requires --images-dir with image files matching GT/DR basenames.")
    if not images_dir.exists() or not images_dir.is_dir():
        raise EvaluationError(f"--images-dir is missing or is not a directory: {images_dir}")
    try:
        import cv2
    except ImportError as exc:
        raise EvaluationError(
            'Optional dependency "opencv-python" is not installed. Omit --animation or install opencv-python.'
        ) from exc

    frame_dir = output_dir / "images" / "detections_one_by_one"
    frame_dir.mkdir(parents=True, exist_ok=True)
    cumulative_dir = output_dir / "images"
    cumulative_cache = {}
    status_colors = {
        "MATCH": (0, 180, 0),
        "REPEATED_MATCH": (0, 0, 220),
        "INSUFFICIENT_OVERLAP": (0, 120, 255),
        "NO_MATCH": (0, 0, 220),
        "DIFFICULT_IGNORED": (180, 180, 180),
    }

    for idx, record in enumerate(records, start=1):
        image_path = find_image(images_dir, record.file_id)
        image = cv2.imread(str(image_path))
        if image is None:
            raise EvaluationError(f"OpenCV could not read image for animation: {image_path}")
        cumulative_path = cumulative_dir / image_path.name
        if record.file_id in cumulative_cache:
            cumulative = cumulative_cache[record.file_id]
        elif cumulative_path.exists():
            cumulative = cv2.imread(str(cumulative_path))
        else:
            cumulative = image.copy()
        if cumulative is None:
            cumulative = image.copy()

        color = status_colors.get(record.status, (255, 255, 255))
        left, top, right, bottom = int_box(record.bbox)
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        cv2.rectangle(cumulative, (left, top), (right, bottom), color, 2)
        cv2.putText(
            image,
            f"{record.class_name} {record.confidence:.3f} {record.status} IoU={record.iou:.2f}",
            (max(0, left), max(15, top - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            cumulative,
            record.class_name,
            (max(0, left), max(15, top - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
        if record.matched_gt_bbox is not None:
            gt_left, gt_top, gt_right, gt_bottom = int_box(record.matched_gt_bbox)
            cv2.rectangle(image, (gt_left, gt_top), (gt_right, gt_bottom), (255, 200, 100), 1)
            cv2.rectangle(cumulative, (gt_left, gt_top), (gt_right, gt_bottom), (255, 200, 100), 1)
        cv2.imwrite(str(frame_dir / f"{record.class_name}_detection{idx}.jpg"), image)
        cv2.imwrite(str(cumulative_path), cumulative)
        cumulative_cache[record.file_id] = cumulative


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        ensure_threshold(args.min_overlap, "--min-overlap")
        ignored = set(args.ignore or [])
        gt_by_file, detections, gt_counts, image_counts, det_counts = load_inputs(
            args.ground_truth_dir, args.detection_results_dir, ignored
        )
        gt_classes = sorted(gt_counts)
        class_iou = validate_class_iou(args.set_class_iou, gt_classes)
        prepare_output_dir(args.output_dir, args.overwrite)
        results, records = evaluate(
            gt_by_file,
            detections,
            gt_counts,
            image_counts,
            args.min_overlap,
            class_iou,
        )
        mean_ap = write_text_outputs(
            args.output_dir,
            results,
            gt_counts,
            det_counts,
            sorted(ignored),
            class_iou,
            args.min_overlap,
        )
        if args.plot:
            write_plots(args.output_dir, results, gt_counts, det_counts, mean_ap)
        if args.animation:
            write_animation(args.output_dir, args.images_dir, records)
        if not args.quiet:
            for class_name in sorted(results):
                print(f"{fmt_percent(results[class_name].ap)} = {class_name} AP")
        print(f"mAP = {fmt_percent(mean_ap)}")
        if not args.quiet:
            print(f"Wrote evaluation outputs to: {args.output_dir}")
        return 0
    except EvaluationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
