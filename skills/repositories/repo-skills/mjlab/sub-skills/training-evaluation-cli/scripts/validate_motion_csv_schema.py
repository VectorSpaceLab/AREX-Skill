from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


class ValidationError(Exception):
  """Raised when the CSV cannot be consumed by the motion converter."""


def _parse_positive_float(value: str) -> float:
  try:
    parsed = float(value)
  except ValueError as exc:
    raise argparse.ArgumentTypeError(f"not a float: {value!r}") from exc
  if parsed <= 0:
    raise argparse.ArgumentTypeError("value must be positive")
  return parsed


def _parse_positive_int(value: str) -> int:
  try:
    parsed = int(value)
  except ValueError as exc:
    raise argparse.ArgumentTypeError(f"not an integer: {value!r}") from exc
  if parsed <= 0:
    raise argparse.ArgumentTypeError("value must be positive")
  return parsed


def _parse_line_range(value: str | None) -> tuple[int, int] | None:
  if value is None:
    return None
  for separator in (":", "-"):
    if separator in value:
      start_text, end_text = value.split(separator, 1)
      break
  else:
    raise argparse.ArgumentTypeError("line range must look like START:END")

  try:
    start = int(start_text)
    end = int(end_text)
  except ValueError as exc:
    raise argparse.ArgumentTypeError("line range bounds must be integers") from exc
  if start < 1:
    raise argparse.ArgumentTypeError("line range starts at 1")
  if end < start:
    raise argparse.ArgumentTypeError("line range end must be >= start")
  return start, end


def _in_range(line_number: int, line_range: tuple[int, int] | None) -> bool:
  if line_range is None:
    return True
  start, end = line_range
  return start <= line_number <= end


def _read_selected_rows(
  path: Path,
  line_range: tuple[int, int] | None,
) -> tuple[int, int, int, float, float]:
  if not path.exists():
    raise ValidationError(f"file does not exist: {path}")
  if not path.is_file():
    raise ValidationError(f"not a file: {path}")

  total_physical_lines = 0
  selected_rows = 0
  column_count: int | None = None
  min_quat_norm = math.inf
  max_quat_norm = 0.0

  with path.open(newline="") as csv_file:
    reader = csv.reader(csv_file)
    for line_number, row in enumerate(reader, start=1):
      total_physical_lines = line_number
      if not _in_range(line_number, line_range):
        continue
      if not row or all(not item.strip() for item in row):
        raise ValidationError(f"line {line_number}: blank row in selected range")

      if column_count is None:
        column_count = len(row)
      elif len(row) != column_count:
        raise ValidationError(
          f"line {line_number}: expected {column_count} columns, got {len(row)}"
        )

      try:
        values = [float(item.strip()) for item in row]
      except ValueError as exc:
        raise ValidationError(f"line {line_number}: non-numeric value") from exc

      if len(values) < 7:
        raise ValidationError(
          f"line {line_number}: expected at least 7 base-pose columns"
        )

      quat_norm = math.sqrt(sum(component * component for component in values[3:7]))
      min_quat_norm = min(min_quat_norm, quat_norm)
      max_quat_norm = max(max_quat_norm, quat_norm)
      selected_rows += 1

  if line_range is not None and total_physical_lines < line_range[1]:
    raise ValidationError(
      f"line range ends at {line_range[1]}, but file has {total_physical_lines} lines"
    )
  if selected_rows == 0:
    raise ValidationError("no numeric rows selected")
  assert column_count is not None
  return selected_rows, total_physical_lines, column_count, min_quat_norm, max_quat_norm


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description=(
      "Validate a motion-imitation CSV before running the mjlab CSV-to-NPZ "
      "converter. Line ranges are 1-based and inclusive."
    )
  )
  parser.add_argument("csv_file", type=Path, help="Numeric CSV to validate.")
  parser.add_argument(
    "--input-fps",
    type=_parse_positive_float,
    default=30.0,
    help="Frame rate of the source CSV. Default: 30.",
  )
  parser.add_argument(
    "--output-fps",
    type=_parse_positive_float,
    default=50.0,
    help="Requested converter output frame rate. Default: 50.",
  )
  parser.add_argument(
    "--expected-dofs",
    type=_parse_positive_int,
    required=True,
    help="Expected number of joint-position columns after the 7 base columns.",
  )
  parser.add_argument(
    "--line-range",
    type=_parse_line_range,
    help="Optional 1-based inclusive range, for example 1:120 or 1-120.",
  )
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(argv)

  try:
    selected_rows, total_lines, columns, min_quat, max_quat = _read_selected_rows(
      args.csv_file,
      args.line_range,
    )

    actual_dofs = columns - 7
    if actual_dofs != args.expected_dofs:
      raise ValidationError(
        f"expected {args.expected_dofs} DOF columns, found {actual_dofs} "
        f"({columns} total columns)"
      )

    if selected_rows < 2:
      raise ValidationError("at least two selected frames are required")

    duration_s = (selected_rows - 1) / args.input_fps
    estimated_output_frames = math.ceil(duration_s * args.output_fps)
    if estimated_output_frames < 3:
      raise ValidationError(
        "estimated converter output has fewer than 3 frames; velocity "
        "estimation needs a longer range or higher output FPS"
      )
  except ValidationError as exc:
    print(f"motion CSV schema: INVALID: {exc}", file=sys.stderr)
    return 1

  print("motion CSV schema: OK")
  print(f"file: {args.csv_file}")
  print(f"selected rows: {selected_rows} of {total_lines} physical lines")
  if args.line_range is not None:
    print(f"line range: {args.line_range[0]}:{args.line_range[1]} (inclusive)")
  print(f"columns: {columns} total = 7 base + {actual_dofs} DOFs")
  print(f"input_fps: {args.input_fps:g}")
  print(f"output_fps: {args.output_fps:g}")
  print(f"duration_s: {duration_s:.6g}")
  print(f"estimated_output_frames: {estimated_output_frames}")

  if min_quat < 0.95 or max_quat > 1.05:
    print(
      "warning: quaternion column norms are outside the loose [0.95, 1.05] "
      f"range (min={min_quat:.6g}, max={max_quat:.6g})",
      file=sys.stderr,
    )

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
