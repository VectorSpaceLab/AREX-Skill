#!/usr/bin/env python3
"""Validate a JSON OpenLane-V2-style prediction submission.

This standalone checker distills the OpenLane-V2 schema rules for JSON files.
It uses only the Python standard library plus optional iso3166 country lookup;
it never imports OpenLane-V2, NumPy, OpenMMLab, or the InternImage repository.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional

try:  # optional; validation still runs without it
    from iso3166 import countries  # type: ignore
except Exception:  # pragma: no cover - depends on caller environment
    countries = None


REQUIRED_STRING_FIELDS = ["method", "e-mail", "institution / company", "country / region"]
PLACEHOLDER_VALUES = {"", "change_me", "changeme", "todo", "tbd", "unknown", "xxx", "none", "null"}
VALID_TRAFFIC_ATTRIBUTES = set(range(13))


class Report:
    """Small structured validation report."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.frames_checked = 0
        self.lanes_checked = 0
        self.traffic_checked = 0

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "frames_checked": self.frames_checked,
                "lanes_checked": self.lanes_checked,
                "traffic_elements_checked": self.traffic_checked,
                "country_checked_with_iso3166": countries is not None,
            },
        }


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def matrix_shape(value: Any) -> str:
    if not isinstance(value, list):
        return type(value).__name__
    if not value:
        return "0x?"
    if not all(isinstance(row, list) for row in value):
        return f"{len(value)}xnon-list"
    widths = sorted({len(row) for row in value})
    return f"{len(value)}x{widths[0] if len(widths) == 1 else widths}"


def is_numeric_matrix(value: Any, rows: Optional[int], cols: Optional[int]) -> bool:
    if not isinstance(value, list):
        return False
    if rows is not None and len(value) != rows:
        return False
    for row in value:
        if not isinstance(row, list):
            return False
        if cols is not None and len(row) != cols:
            return False
        if not all(is_number(cell) for cell in row):
            return False
    return True


def looks_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def check_required_keys(obj: Dict[str, Any], keys: List[str], path: str, report: Report) -> None:
    for key in keys:
        if key not in obj:
            report.error(f"{path}.{key}", "missing required key")


def validate_identifier(value: Any, path: str, report: Report) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        report.error(path, "id must be an integer or string")
    elif isinstance(value, str) and value == "":
        report.error(path, "id string must not be empty")


def validate_confidence(value: Any, path: str, report: Report, strict_confidence: bool) -> None:
    if not is_number(value):
        report.error(path, "confidence must be a finite number")
        return
    if not 0.0 <= float(value) <= 1.0:
        message = "confidence is outside [0, 1]"
        if strict_confidence:
            report.error(path, message)
        else:
            report.warn(path, message)


def validate_top_metadata(data: Dict[str, Any], report: Report, allow_placeholder_metadata: bool) -> None:
    for field in REQUIRED_STRING_FIELDS:
        path = field
        if field not in data:
            report.error(path, "missing required metadata field")
            continue
        value = data[field]
        if not isinstance(value, str):
            report.error(path, "must be a string")
            continue
        if not allow_placeholder_metadata and looks_placeholder(value):
            report.error(path, "metadata field still looks like a placeholder")

    authors = data.get("authors")
    if not isinstance(authors, list):
        report.error("authors", "must be a list of strings")
    else:
        if len(authors) > 10:
            report.error("authors", "must contain at most 10 authors")
        if not authors and not allow_placeholder_metadata:
            report.warn("authors", "author list is empty")
        for idx, author in enumerate(authors):
            if not isinstance(author, str):
                report.error(f"authors[{idx}]", "must be a string")
            elif not allow_placeholder_metadata and looks_placeholder(author):
                report.error(f"authors[{idx}]", "author still looks like a placeholder")

    country = data.get("country / region")
    if isinstance(country, str) and country.strip() and countries is not None:
        try:
            countries.get(country)
        except Exception:
            report.error("country / region", "not recognized by iso3166; use a country name or alpha code")
    elif countries is None:
        report.warn("country / region", "iso3166 is not installed; country was checked only as a non-empty string")


def get_frame_predictions(frame_value: Any, frame_path: str, report: Report) -> Optional[Dict[str, Any]]:
    if not isinstance(frame_value, dict):
        report.error(frame_path, "frame result must be an object")
        return None
    if "predictions" in frame_value:
        predictions = frame_value["predictions"]
    else:
        predictions = frame_value
        report.warn(frame_path, "accepted direct prediction object; upstream devkit commonly expects a 'predictions' wrapper")
    if not isinstance(predictions, dict):
        report.error(f"{frame_path}.predictions", "must be an object")
        return None
    return predictions


def validate_lane(instance: Any, base_path: str, report: Report, strict_confidence: bool) -> Any:
    if not isinstance(instance, dict):
        report.error(base_path, "lane instance must be an object")
        return None
    check_required_keys(instance, ["id", "points", "confidence"], base_path, report)
    lane_id = instance.get("id")
    validate_identifier(lane_id, f"{base_path}.id", report)
    points = instance.get("points")
    if not is_numeric_matrix(points, None, 3):
        report.error(f"{base_path}.points", f"must be a numeric #points x 3 matrix, got {matrix_shape(points)}")
    elif len(points) < 2:
        report.warn(f"{base_path}.points", "lane polyline has fewer than two points")
    validate_confidence(instance.get("confidence"), f"{base_path}.confidence", report, strict_confidence)
    report.lanes_checked += 1
    return lane_id


def validate_traffic(instance: Any, base_path: str, report: Report, strict_confidence: bool) -> Any:
    if not isinstance(instance, dict):
        report.error(base_path, "traffic element must be an object")
        return None
    check_required_keys(instance, ["id", "points", "confidence", "attribute"], base_path, report)
    traffic_id = instance.get("id")
    validate_identifier(traffic_id, f"{base_path}.id", report)
    points = instance.get("points")
    if not is_numeric_matrix(points, 2, 2):
        report.error(f"{base_path}.points", f"must be a numeric 2 x 2 box matrix, got {matrix_shape(points)}")
    attribute = instance.get("attribute")
    if isinstance(attribute, bool) or not isinstance(attribute, int) or attribute not in VALID_TRAFFIC_ATTRIBUTES:
        report.error(f"{base_path}.attribute", "must be an integer traffic-element attribute id in [0, 12]")
    validate_confidence(instance.get("confidence"), f"{base_path}.confidence", report, strict_confidence)
    report.traffic_checked += 1
    return traffic_id


def validate_predictions(predictions: Dict[str, Any], frame_key: str, report: Report, strict_confidence: bool) -> None:
    frame_path = f"results[{frame_key!r}].predictions"
    lanes = predictions.get("lane_centerline")
    traffic = predictions.get("traffic_element")
    if not isinstance(lanes, list):
        report.error(f"{frame_path}.lane_centerline", "must be a list")
        lanes = []
    if not isinstance(traffic, list):
        report.error(f"{frame_path}.traffic_element", "must be a list")
        traffic = []

    ids: List[Any] = []
    for idx, lane in enumerate(lanes):
        ids.append(validate_lane(lane, f"{frame_path}.lane_centerline[{idx}]", report, strict_confidence))
    for idx, elem in enumerate(traffic):
        ids.append(validate_traffic(elem, f"{frame_path}.traffic_element[{idx}]", report, strict_confidence))

    present_ids = [item for item in ids if item is not None]
    if len(set(str(item) for item in present_ids)) != len(present_ids):
        report.error(frame_path, "ids must be unique across lane_centerline and traffic_element within a frame")

    lane_count = len(lanes)
    traffic_count = len(traffic)
    topology_lclc = predictions.get("topology_lclc")
    topology_lcte = predictions.get("topology_lcte")
    if not is_numeric_matrix(topology_lclc, lane_count, lane_count):
        report.error(
            f"{frame_path}.topology_lclc",
            f"must be #lane_centerline x #lane_centerline ({lane_count} x {lane_count}), got {matrix_shape(topology_lclc)}",
        )
    if not is_numeric_matrix(topology_lcte, lane_count, traffic_count):
        report.error(
            f"{frame_path}.topology_lcte",
            f"must be #lane_centerline x #traffic_element ({lane_count} x {traffic_count}), got {matrix_shape(topology_lcte)}",
        )
    report.frames_checked += 1


def validate(data: Any, strict_confidence: bool = False, allow_placeholder_metadata: bool = False) -> Report:
    report = Report()
    if not isinstance(data, dict):
        report.error("$", "submission must be a JSON object")
        return report
    validate_top_metadata(data, report, allow_placeholder_metadata)
    results = data.get("results")
    if not isinstance(results, dict):
        report.error("results", "must be an object mapping frame identifiers to prediction objects")
        return report
    if not results:
        report.warn("results", "submission contains no frame predictions")
    for frame_key, frame_value in results.items():
        predictions = get_frame_predictions(frame_value, f"results[{frame_key!r}]", report)
        if predictions is not None:
            validate_predictions(predictions, str(frame_key), report, strict_confidence)
    return report


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate JSON OpenLane-V2 prediction schema; does not import OpenLane-V2 or compute metrics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("submission", help="Path to a JSON submission/prediction file, or '-' to read JSON from stdin.")
    parser.add_argument("--json-report", action="store_true", help="Print machine-readable JSON report.")
    parser.add_argument("--strict-confidence", action="store_true", help="Treat confidence values outside [0, 1] as errors instead of warnings.")
    parser.add_argument("--allow-placeholder-metadata", action="store_true", help="Allow empty/TODO-like metadata values during early local debugging.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        data = load_json(args.submission)
    except Exception as exc:
        print(f"Failed to read JSON: {exc}", file=sys.stderr)
        return 2
    report = validate(data, strict_confidence=args.strict_confidence, allow_placeholder_metadata=args.allow_placeholder_metadata)
    if args.json_report:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print("OpenLane-V2 JSON schema check: " + ("PASS" if report.ok else "FAIL"))
        for error in report.errors:
            print(f"ERROR: {error}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        print(
            f"Checked {report.frames_checked} frame(s), {report.lanes_checked} lane(s), "
            f"{report.traffic_checked} traffic element(s)."
        )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
