#!/usr/bin/env python3
"""Summarize AlphaFold confidence_*.json and pae_*.json files.

This helper intentionally uses only the Python standard library. It does not
import AlphaFold, run inference, parse structures, or contact network services.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


CONFIDENCE_PREFIX = "confidence_"
PAE_PREFIX = "pae_"


def _load_json(path: Path) -> Any:
  with path.open("r", encoding="utf-8") as handle:
    return json.load(handle)


def _is_confidence_file(path: Path) -> bool:
  return path.name.startswith(CONFIDENCE_PREFIX) and path.suffix == ".json"


def _is_pae_file(path: Path) -> bool:
  return path.name.startswith(PAE_PREFIX) and path.suffix == ".json"


def _discover(paths: Sequence[Path]) -> List[Path]:
  discovered: List[Path] = []
  for path in paths:
    if path.is_dir():
      for child in sorted(path.rglob("*.json")):
        if _is_confidence_file(child) or _is_pae_file(child):
          discovered.append(child)
    elif path.is_file():
      discovered.append(path)
    else:
      raise FileNotFoundError(f"No such file or directory: {path}")
  return sorted(dict.fromkeys(discovered))


def _category(score: float) -> str:
  if 0 <= score < 50:
    return "D"
  if 50 <= score < 70:
    return "L"
  if 70 <= score < 90:
    return "M"
  if 90 <= score <= 100:
    return "H"
  return "invalid"


def _spans(indices: Iterable[int]) -> List[List[int]]:
  sorted_indices = sorted(indices)
  if not sorted_indices:
    return []
  spans: List[List[int]] = []
  start = previous = sorted_indices[0]
  for index in sorted_indices[1:]:
    if index == previous + 1:
      previous = index
      continue
    spans.append([start, previous])
    start = previous = index
  spans.append([start, previous])
  return spans


def _summarize_confidence(path: Path) -> Dict[str, Any]:
  data = _load_json(path)
  if not isinstance(data, dict):
    raise ValueError(f"{path}: confidence JSON must be an object")
  scores = data.get("confidenceScore")
  residue_numbers = data.get("residueNumber")
  categories = data.get("confidenceCategory")
  if not isinstance(scores, list):
    raise ValueError(f"{path}: missing list field confidenceScore")
  if residue_numbers is not None and len(residue_numbers) != len(scores):
    raise ValueError(f"{path}: residueNumber length differs from confidenceScore")
  if categories is not None and len(categories) != len(scores):
    raise ValueError(f"{path}: confidenceCategory length differs from confidenceScore")

  numeric_scores = [float(score) for score in scores]
  computed_categories = [_category(score) for score in numeric_scores]
  category_counts = {key: computed_categories.count(key) for key in ["D", "L", "M", "H", "invalid"]}
  low_indices = [index + 1 for index, cat in enumerate(computed_categories) if cat in {"D", "L", "invalid"}]

  if numeric_scores:
    mean_score = sum(numeric_scores) / len(numeric_scores)
    min_score = min(numeric_scores)
    max_score = max(numeric_scores)
  else:
    mean_score = min_score = max_score = math.nan

  mismatches = 0
  if isinstance(categories, list):
    mismatches = sum(
        1 for expected, observed in zip(computed_categories, categories) if expected != observed
    )

  return {
      "path": str(path),
      "type": "confidence",
      "residue_count": len(numeric_scores),
      "mean_plddt": None if math.isnan(mean_score) else round(mean_score, 2),
      "min_plddt": None if math.isnan(min_score) else round(min_score, 2),
      "max_plddt": None if math.isnan(max_score) else round(max_score, 2),
      "category_counts": category_counts,
      "low_confidence_spans": _spans(low_indices),
      "provided_category_mismatches": mismatches,
  }


def _extract_pae_payload(data: Any, path: Path) -> Dict[str, Any]:
  if isinstance(data, list):
    if len(data) != 1 or not isinstance(data[0], dict):
      raise ValueError(f"{path}: PAE JSON list must contain one object")
    return data[0]
  if isinstance(data, dict):
    return data
  raise ValueError(f"{path}: PAE JSON must be an object or one-object list")


def _summarize_pae(path: Path) -> Dict[str, Any]:
  payload = _extract_pae_payload(_load_json(path), path)
  matrix = payload.get("predicted_aligned_error")
  max_pae = payload.get("max_predicted_aligned_error")
  if not isinstance(matrix, list):
    raise ValueError(f"{path}: missing list field predicted_aligned_error")
  size = len(matrix)
  if any(not isinstance(row, list) for row in matrix):
    raise ValueError(f"{path}: PAE rows must be lists")
  row_lengths = [len(row) for row in matrix]
  is_square = all(length == size for length in row_lengths)
  values = [float(value) for row in matrix for value in row]

  high_threshold = None
  high_fraction = None
  if max_pae is not None and values:
    high_threshold = 0.7 * float(max_pae)
    high_fraction = sum(value >= high_threshold for value in values) / len(values)

  diagonal_values: List[float] = []
  if is_square:
    diagonal_values = [float(matrix[index][index]) for index in range(size)]

  return {
      "path": str(path),
      "type": "pae",
      "size": size,
      "row_lengths_unique": sorted(set(row_lengths)),
      "is_square": is_square,
      "max_predicted_aligned_error": max_pae,
      "observed_min": round(min(values), 2) if values else None,
      "observed_max": round(max(values), 2) if values else None,
      "observed_mean": round(sum(values) / len(values), 2) if values else None,
      "high_pae_threshold": round(high_threshold, 2) if high_threshold is not None else None,
      "high_pae_fraction": round(high_fraction, 4) if high_fraction is not None else None,
      "diagonal_max": round(max(diagonal_values), 2) if diagonal_values else None,
  }


def summarize(path: Path) -> Dict[str, Any]:
  if _is_confidence_file(path):
    return _summarize_confidence(path)
  if _is_pae_file(path):
    return _summarize_pae(path)
  raise ValueError(f"{path}: expected confidence_*.json or pae_*.json")


def _print_text(summaries: Sequence[Dict[str, Any]]) -> None:
  for summary in summaries:
    print(f"{summary['path']} ({summary['type']})")
    if summary["type"] == "confidence":
      print(
          "  residues={residue_count} mean_plddt={mean_plddt} "
          "min={min_plddt} max={max_plddt}".format(**summary)
      )
      print(f"  category_counts={summary['category_counts']}")
      print(f"  low_confidence_spans={summary['low_confidence_spans']}")
      if summary["provided_category_mismatches"]:
        print(f"  category_mismatches={summary['provided_category_mismatches']}")
    else:
      print(
          "  size={size} square={is_square} max_pae={max_predicted_aligned_error} "
          "observed_min={observed_min} observed_max={observed_max} "
          "observed_mean={observed_mean}".format(**summary)
      )
      print(
          "  high_pae_threshold={high_pae_threshold} "
          "high_pae_fraction={high_pae_fraction} diagonal_max={diagonal_max}".format(**summary)
      )


def main() -> None:
  parser = argparse.ArgumentParser(
      description="Summarize AlphaFold confidence_*.json and pae_*.json files."
  )
  parser.add_argument("paths", nargs="+", type=Path, help="JSON file(s) or directory/directories")
  parser.add_argument("--json", action="store_true", help="Emit machine-readable summary JSON")
  args = parser.parse_args()

  files = _discover(args.paths)
  summaries = [summarize(path) for path in files]
  if args.json:
    print(json.dumps({"files": summaries}, indent=2, sort_keys=True))
  else:
    _print_text(summaries)


if __name__ == "__main__":
  main()
