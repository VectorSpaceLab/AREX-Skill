#!/usr/bin/env python3
"""Validate XLNet pretraining text or integer-id corpora.

The validator is intentionally lightweight and does not import TensorFlow.
It checks:

- empty input globs
- empty files
- blank-line document boundaries
- `<eop>` suffix usage in raw text
- non-integer tokens in id mode
- mixed raw/id lines when mode is inferred automatically
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional


_INT_TOKEN_RE = re.compile(r"^[+-]?\d+$")


@dataclass
class FileReport:
  path: str
  lines: int = 0
  empty_lines: int = 0
  documents: int = 0
  eop_suffix_lines: int = 0
  mode: Optional[str] = None
  warnings: List[str] = field(default_factory=list)
  errors: List[str] = field(default_factory=list)

  @property
  def nonempty_lines(self):
    return self.lines - self.empty_lines


def expand_inputs(patterns):
  files = []
  errors = []
  for pattern in patterns:
    matches = sorted(glob.glob(pattern))
    if not matches and os.path.isfile(pattern):
      matches = [pattern]
    if not matches:
      errors.append(f"No files matched: {pattern}")
      continue
    files.extend(matches)

  unique = []
  seen = set()
  for path in files:
    if path in seen:
      continue
    seen.add(path)
    unique.append(path)
  return unique, errors


def infer_line_mode(stripped_line):
  tokens = stripped_line.split()
  if tokens and all(_INT_TOKEN_RE.match(token) for token in tokens):
    return "ids"
  return "raw"


def validate_ids_line(path, lineno, stripped_line, report):
  tokens = stripped_line.split()
  for token in tokens:
    if not _INT_TOKEN_RE.match(token):
      report.errors.append(
          f"{path}:{lineno} contains a non-integer token: {token!r}")
      return
    if int(token) < 0:
      report.errors.append(
          f"{path}:{lineno} contains a negative id token: {token!r}")
      return


def validate_raw_line(path, lineno, stripped_line, report):
  if "<eop>" in stripped_line:
    if stripped_line.endswith("<eop>"):
      report.eop_suffix_lines += 1
    else:
      report.warnings.append(
          f"{path}:{lineno} contains <eop> but not as a line suffix")


def validate_file(path, mode):
  report = FileReport(path=path)
  inferred_mode = None
  in_doc = False

  try:
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
      for lineno, line in enumerate(handle, 1):
        report.lines += 1
        stripped = line.strip()
        if not stripped:
          report.empty_lines += 1
          in_doc = False
          continue

        if not in_doc:
          report.documents += 1
          in_doc = True

        if mode == "auto":
          line_mode = infer_line_mode(stripped)
          if inferred_mode is None:
            inferred_mode = line_mode
          elif line_mode != inferred_mode:
            report.errors.append(
                f"{path}:{lineno} mixes raw text and integer-id lines")
            continue
          if line_mode == "ids":
            validate_ids_line(path, lineno, stripped, report)
          else:
            validate_raw_line(path, lineno, stripped, report)
        elif mode == "ids":
          validate_ids_line(path, lineno, stripped, report)
        else:
          validate_raw_line(path, lineno, stripped, report)
  except OSError as exc:
    report.errors.append(f"{path}: {exc}")
    return report

  if mode == "auto":
    report.mode = inferred_mode
  else:
    report.mode = mode

  if report.lines == 0 or report.nonempty_lines == 0:
    report.warnings.append(f"{path} is empty or has no non-empty lines")

  return report


def build_parser():
  parser = argparse.ArgumentParser(
      description="Validate XLNet pretraining text or integer-id corpora.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "inputs", nargs="+",
      help="Input files or glob patterns to validate.")
  parser.add_argument(
      "--mode", choices=["auto", "raw", "ids"], default="auto",
      help="Validation mode. Auto infers the mode from each non-empty line.")
  parser.add_argument(
      "--json", action="store_true",
      help="Print a JSON report instead of a human-readable summary.")
  return parser


def main(argv=None):
  parser = build_parser()
  args = parser.parse_args(argv)

  files, expansion_errors = expand_inputs(args.inputs)
  errors = list(expansion_errors)
  reports = []
  all_warnings = []
  detected_modes = set()
  total_lines = 0
  total_empty = 0
  total_docs = 0
  total_eop = 0

  for path in files:
    report = validate_file(path, args.mode)
    reports.append(report)
    errors.extend(report.errors)
    all_warnings.extend(report.warnings)
    if report.mode:
      detected_modes.add(report.mode)
    total_lines += report.lines
    total_empty += report.empty_lines
    total_docs += report.documents
    total_eop += report.eop_suffix_lines

  if not files:
    errors.append("No input files were found after glob expansion.")

  if args.mode == "auto" and len({mode for mode in detected_modes if mode is not None}) > 1:
    errors.append("The validated files mix raw-text and id-mode corpora.")

  if not reports or all(report.nonempty_lines == 0 for report in reports):
    errors.append("No non-empty corpus lines were found.")

  summary = {
      "files": len(files),
      "mode": args.mode,
      "detected_modes": sorted(mode for mode in detected_modes if mode is not None),
      "total_lines": total_lines,
      "empty_lines": total_empty,
      "documents": total_docs,
      "eop_suffix_lines": total_eop,
      "warnings": all_warnings,
      "errors": errors,
      "reports": [report.__dict__ for report in reports],
  }

  if args.json:
    print(json.dumps(summary, indent=2, sort_keys=True))
  else:
    print(f"Validated {summary['files']} file(s) in {args.mode} mode.")
    print(f"Total lines: {total_lines}")
    print(f"Empty lines: {total_empty}")
    print(f"Documents: {total_docs}")
    print(f"<eop> suffix lines: {total_eop}")
    if summary["detected_modes"]:
      print(f"Detected modes: {', '.join(summary['detected_modes'])}")
    if all_warnings:
      print("Warnings:", file=sys.stderr)
      for warning in all_warnings:
        print(f"  - {warning}", file=sys.stderr)
    if errors:
      print("Errors:", file=sys.stderr)
      for error in errors:
        print(f"  - {error}", file=sys.stderr)
      return 1

  if errors:
    for error in errors:
      print(f"ERROR: {error}", file=sys.stderr)
    return 1

  for warning in all_warnings:
    print(f"WARNING: {warning}", file=sys.stderr)
  return 0


if __name__ == "__main__":
  sys.exit(main())
