#!/usr/bin/env python3
"""Validate local inputs for the streamlit-geospatial dashboard branches.

The helper is deliberately local and deterministic. It reads CSV/TSV-like CSV
text and GeoJSON, optionally writes one JSON report only when --output is
provided, and never downloads or extracts anything.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


REQUIRED_COLUMNS: dict[tuple[str, str], tuple[str, ...]] = {
    ("monthly", "national"): ("month_date_yyyymm", "country"),
    ("monthly", "state"): ("month_date_yyyymm", "state", "state_id"),
    ("monthly", "metro"): (
        "month_date_yyyymm",
        "cbsa_code",
        "cbsa_title",
        "HouseholdRank",
    ),
    ("monthly", "county"): ("month_date_yyyymm", "county_fips", "county_name"),
    ("monthly", "zip"): ("month_date_yyyymm", "postal_code", "zip_name", "flag"),
    ("weekly", "national"): ("week_end_date", "geo_country"),
    ("weekly", "metro"): ("week_end_date", "cbsa_code", "cbsa_title", "hh_rank"),
}

PERIOD_COLUMN = {"monthly": "month_date_yyyymm", "weekly": "week_end_date"}
GEOMETRY_KEY = {
    "national": "NAME",
    "state": "STUSPS",
    "county": "GEOID",
    "metro": "CBSAFP",
    "zip": "GEOID10",
}
DATA_KEY = {
    "national": "country",
    "state": "state_id",
    "county": "county_fips",
    "metro": "cbsa_code",
    "zip": "postal_code",
}

_NULLS = {"", "na", "n/a", "null", "none", "nan"}
_MONTH_RE = re.compile(r"^(?P<year>\d{4})[-/]?(?P<month>\d{2})$")


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.details: dict[str, Any] = {}

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "ok" if not self.errors else "error",
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }


def _is_null(value: Any) -> bool:
    return value is None or str(value).strip().lower() in _NULLS


def _non_null(values: Iterable[Any]) -> list[str]:
    return [str(value).strip() for value in values if not _is_null(value)]


def _read_csv(path: Path, delimiter: str) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            headers = list(reader.fieldnames or [])
            if not headers:
                raise ValueError("file has no header row")
            if any(not header or not header.strip() for header in headers):
                raise ValueError("header row contains a blank column name")
            if len(headers) != len(set(headers)):
                duplicates = sorted({h for h in headers if headers.count(h) > 1})
                raise ValueError(f"duplicate header names: {duplicates}")
            rows = []
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(
                        f"row {line_number} has more fields than the header"
                    )
                rows.append(dict(row))
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        raise ValueError(f"cannot read CSV {path}: {exc}") from exc
    return headers, rows


def _month_value(value: str) -> str | None:
    match = _MONTH_RE.fullmatch(str(value).strip())
    if not match:
        return None
    year = int(match.group("year"))
    month = int(match.group("month"))
    if not 1 <= month <= 12:
        return None
    return f"{year:04d}{month:02d}"


def _week_value(value: str) -> str | None:
    text = str(value).strip()
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return None


def _canonical_period(value: Any, frequency: str) -> str | None:
    if _is_null(value):
        return None
    return _month_value(str(value)) if frequency == "monthly" else _week_value(str(value))


def _canonical_key(value: Any, category: str, frequency: str, *, national_weekly_index: int | None = None) -> str | None:
    if _is_null(value):
        return None
    text = str(value).strip()
    if category in {"county", "zip"}:
        if not text.isdigit():
            return None
        return text.zfill(5)
    if category == "state":
        return text.upper()
    if category == "metro":
        if not text.isdigit():
            return None
        return text[:5]
    if category == "national":
        if frequency == "weekly" and national_weekly_index == 0:
            return "united states"
        return text.casefold()
    return text


def _parse_geojson(path: Path, category: str, report: ValidationReport) -> tuple[set[str], dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report.error(f"cannot read GeoJSON {path}: {exc}")
        return set(), {}

    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        report.error("GeoJSON must have type FeatureCollection")
        return set(), {}
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        report.error("GeoJSON FeatureCollection has no features")
        return set(), {}

    property_key = GEOMETRY_KEY[category]
    keys: set[str] = set()
    null_geometry = 0
    missing_property = 0
    invalid_features = 0
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            invalid_features += 1
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict) or property_key not in properties:
            missing_property += 1
        else:
            key = _canonical_key(properties.get(property_key), category, "monthly")
            if key is not None:
                keys.add(key)
        geometry = feature.get("geometry")
        if geometry is None:
            null_geometry += 1
        elif not isinstance(geometry, dict) or not isinstance(
            geometry.get("type"), str
        ):
            invalid_features += 1
        elif geometry["type"] != "GeometryCollection" and "coordinates" not in geometry:
            invalid_features += 1

    if missing_property:
        report.error(
            f"GeoJSON has {missing_property} feature(s) without required property {property_key!r}"
        )
    if invalid_features:
        report.error(f"GeoJSON has {invalid_features} invalid feature/geometry record(s)")
    if not keys:
        report.error(f"GeoJSON has no usable values for property {property_key!r}")
    if null_geometry:
        report.warning(f"GeoJSON has {null_geometry} feature(s) with null geometry")
    if null_geometry == len(features):
        report.error("GeoJSON has no non-null geometries")

    details = {
        "feature_count": len(features),
        "property_key": property_key,
        "usable_join_key_count": len(keys),
        "null_geometry_count": null_geometry,
    }
    return keys, details


def _validate_dictionary(path: Path, metrics: list[str], report: ValidationReport) -> dict[str, Any]:
    try:
        headers, rows = _read_csv(path, ",")
    except ValueError as exc:
        report.error(str(exc))
        return {}
    required = {"Name", "Label", "Description"}
    missing = sorted(required - set(headers))
    if missing:
        report.error(f"data dictionary is missing required column(s): {', '.join(missing)}")
    names = [row.get("Name", "").strip() for row in rows]
    duplicates = sorted({name for name in names if name and names.count(name) > 1})
    if duplicates:
        report.error(f"data dictionary has duplicate Name value(s): {', '.join(duplicates)}")
    for metric in metrics:
        matches = [row for row in rows if row.get("Name", "").strip() == metric]
        if not matches:
            report.error(f"metric {metric!r} is absent from the data dictionary")
        elif _is_null(matches[0].get("Label")) or _is_null(matches[0].get("Description")):
            report.warning(f"metric {metric!r} has a blank label or description")
    return {"row_count": len(rows), "columns": headers, "metric_rows_checked": metrics}


def validate(args: argparse.Namespace) -> dict[str, Any]:
    report = ValidationReport()
    category = args.category
    frequency = args.frequency
    expected = REQUIRED_COLUMNS[(frequency, category)]
    period_column = PERIOD_COLUMN[frequency]

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        report.error(f"CSV file does not exist or is not a regular file: {csv_path}")
        return report.as_dict()
    try:
        headers, rows = _read_csv(csv_path, args.delimiter)
    except ValueError as exc:
        report.error(str(exc))
        return report.as_dict()

    missing = sorted(set(expected).difference(headers))
    missing_extra = sorted(set(args.required_column).difference(headers))
    if missing:
        report.error(
            f"{frequency}/{category} CSV is missing required column(s): {', '.join(missing)}"
        )
    if missing_extra:
        report.error(f"CSV is missing requested column(s): {', '.join(missing_extra)}")
    if period_column not in headers:
        report.error(f"CSV has no period column {period_column!r}")
        return report.as_dict()

    canonical_periods: dict[str, int] = {}
    invalid_period_rows = 0
    for row in rows:
        raw = row.get(period_column)
        canonical = _canonical_period(raw, frequency)
        if canonical is None and not _is_null(raw):
            invalid_period_rows += 1
        elif canonical is not None:
            canonical_periods[canonical] = canonical_periods.get(canonical, 0) + 1
    if invalid_period_rows:
        report.warning(
            f"{invalid_period_rows} row(s) have an unparseable {period_column} value"
        )
    available_periods = sorted(canonical_periods)
    report.details.update(
        {
            "csv": str(csv_path),
            "row_count": len(rows),
            "columns": headers,
            "required_columns": list(expected),
            "available_periods": available_periods,
        }
    )
    if not available_periods:
        report.error(f"CSV has no usable values in period column {period_column!r}")

    selected_period = None
    if args.period is not None:
        selected_period = _canonical_period(args.period, frequency)
        if selected_period is None:
            expected_format = "YYYYMM or YYYY-MM" if frequency == "monthly" else "MM/DD/YYYY"
            report.error(f"invalid --period {args.period!r}; expected {expected_format}")
        elif selected_period not in canonical_periods:
            report.error(
                f"period {args.period!r} is absent; available periods: "
                + (", ".join(available_periods) if available_periods else "none")
            )
    report.details["selected_period"] = selected_period

    selected_row_indices = list(range(len(rows)))
    selected_rows = rows
    if selected_period is not None:
        selected_row_indices = [
            index
            for index, row in enumerate(rows)
            if _canonical_period(row.get(period_column), frequency) == selected_period
        ]
        selected_rows = [rows[index] for index in selected_row_indices]
        if not selected_rows:
            report.error(f"no rows remain for selected period {selected_period}")

    metrics = list(dict.fromkeys(args.metric))
    metric_results: dict[str, Any] = {}
    for metric in metrics:
        if metric not in headers:
            report.error(f"metric column {metric!r} is absent from the CSV")
            metric_results[metric] = {"column_present": False, "non_null_count": 0}
            continue
        values = _non_null(row.get(metric) for row in selected_rows)
        metric_results[metric] = {
            "column_present": True,
            "non_null_count": len(values),
        }
        if not values:
            period_suffix = f" for period {selected_period}" if selected_period else ""
            report.error(f"metric {metric!r} has no non-null values{period_suffix}")
    report.details["metrics"] = metric_results

    data_key = DATA_KEY[category]
    if data_key not in headers and not (category == "national" and frequency == "weekly"):
        report.error(f"CSV has no join key column {data_key!r}")
    csv_keys: set[str] = set()
    null_key_rows = 0
    for index, row in enumerate(selected_rows):
        raw_key = row.get(data_key)
        # Weekly national has no country source column; mirror the page's
        # row-zero special case without inventing a key for other rows. The
        # source applies this before period filtering, so use the original row
        # position rather than the filtered list position.
        source_index = selected_row_indices[index]
        if category == "national" and frequency == "weekly" and source_index == 0:
            raw_key = "United States"
        key = _canonical_key(
            raw_key,
            category,
            frequency,
            national_weekly_index=source_index if frequency == "weekly" else None,
        )
        if key is None:
            null_key_rows += 1
        else:
            csv_keys.add(key)
    if null_key_rows:
        report.warning(f"{null_key_rows} selected row(s) have a null or invalid join key")
    report.details["csv_join_key"] = data_key
    report.details["csv_usable_join_key_count"] = len(csv_keys)

    if args.dictionary:
        dictionary_path = Path(args.dictionary)
        if not dictionary_path.is_file():
            report.error(f"data dictionary does not exist or is not a regular file: {dictionary_path}")
        else:
            report.details["dictionary"] = _validate_dictionary(dictionary_path, metrics, report)

    if args.geojson:
        geo_path = Path(args.geojson)
        if not geo_path.is_file():
            report.error(f"GeoJSON does not exist or is not a regular file: {geo_path}")
        else:
            geo_keys, geo_details = _parse_geojson(geo_path, category, report)
            report.details["geojson"] = {"path": str(geo_path), **geo_details}
            overlap = sorted(csv_keys & geo_keys)
            unmatched_csv = sorted(csv_keys - geo_keys)
            unmatched_geo = sorted(geo_keys - csv_keys)
            report.details["join"] = {
                "overlap_count": len(overlap),
                "unmatched_csv_key_count": len(unmatched_csv),
                "unmatched_geo_key_count": len(unmatched_geo),
                "sample_unmatched_csv_keys": unmatched_csv[:10],
                "sample_unmatched_geo_keys": unmatched_geo[:10],
            }
            if csv_keys and geo_keys and not overlap:
                report.error(
                    "normalized join keys have zero overlap between CSV and GeoJSON; "
                    "check identifier padding, case, and boundary vintage"
                )
            elif unmatched_csv:
                report.warning(
                    f"{len(unmatched_csv)} normalized CSV join key(s) have no GeoJSON feature"
                )
            elif unmatched_geo:
                report.warning(
                    f"{len(unmatched_geo)} normalized GeoJSON key(s) have no CSV row for the selected period"
                )

    return report.as_dict()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local Streamlit dashboard CSV, dictionary, and GeoJSON inputs."
    )
    parser.add_argument("--csv", required=True, help="local metrics CSV")
    parser.add_argument("--category", choices=sorted(GEOMETRY_KEY), required=True)
    parser.add_argument("--frequency", choices=("monthly", "weekly"), required=True)
    parser.add_argument("--period", help="requested YYYYMM/YYYY-MM or MM/DD/YYYY period")
    parser.add_argument("--metric", action="append", default=[], help="metric column; repeatable")
    parser.add_argument("--dictionary", help="optional local data dictionary CSV")
    parser.add_argument("--geojson", help="optional local boundary GeoJSON")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ',')")
    parser.add_argument(
        "--required-column",
        action="append",
        default=[],
        help="additional required column; repeatable",
    )
    parser.add_argument(
        "--output",
        help="optional explicit JSON report path; without it, no files are written",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = validate(args)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"cannot write explicit output {output}: {exc}", file=sys.stderr)
            return 2
        print(f"wrote validation report to {output}")
    else:
        sys.stdout.write(rendered)
    if result["errors"]:
        print("validation failed:", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 2
    if result["warnings"]:
        print("validation passed with warnings:", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"- {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
