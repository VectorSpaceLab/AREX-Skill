#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable

EVAL_TOKEN_COUNT = 38
MATCH_ONLY_TOKEN_COUNT = 2


class ValidationError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a SuperGlue pair manifest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--pair-file",
        required=True,
        type=Path,
        help="Whitespace-delimited pair manifest to validate",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Optional image root used to check that referenced files exist",
    )
    parser.add_argument(
        "--require-gt",
        action="store_true",
        help="Require the 38-token evaluation schema on every row",
    )
    return parser.parse_args()


def resolve_image_path(token: str, input_dir: Path | None) -> Path | None:
    if input_dir is None:
        return None
    path = Path(token)
    return path if path.is_absolute() else input_dir / path


def validate_numeric_values(
    values: list[str],
    expected_count: int,
    label: str,
    line_no: int,
) -> None:
    if len(values) != expected_count:
        raise ValidationError(
            f"Line {line_no}: {label} expects {expected_count} values, got {len(values)}"
        )
    for idx, value in enumerate(values):
        try:
            float(value)
        except ValueError as exc:
            raise ValidationError(
                f"Line {line_no}: {label} token {idx + 1} is not numeric: {value!r}"
            ) from exc


def validate_rotation(value: str, line_no: int, label: str) -> None:
    try:
        rotation = int(value)
    except ValueError as exc:
        raise ValidationError(
            f"Line {line_no}: {label} must be an integer in [0, 3], got {value!r}"
        ) from exc
    if rotation < 0 or rotation > 3:
        raise ValidationError(
            f"Line {line_no}: {label} must be in [0, 3], got {rotation}"
        )


def iter_rows(pair_file: Path) -> Iterable[tuple[int, list[str]]]:
    with pair_file.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            yield line_no, stripped.split()


def validate_pair_file(pair_file: Path, input_dir: Path | None, require_gt: bool) -> tuple[int, int]:
    if not pair_file.is_file():
        raise ValidationError(f"Pair file does not exist: {pair_file}")
    if input_dir is not None and not input_dir.is_dir():
        raise ValidationError(f"Input directory does not exist or is not a directory: {input_dir}")

    rows = list(iter_rows(pair_file))
    if not rows:
        raise ValidationError(f"No pair rows found in {pair_file}")

    match_only_rows = 0
    eval_rows = 0
    errors: list[str] = []

    for line_no, tokens in rows:
        token_count = len(tokens)
        if require_gt and token_count != EVAL_TOKEN_COUNT:
            errors.append(
                f"Line {line_no}: expected {EVAL_TOKEN_COUNT} tokens for evaluation, got {token_count}"
            )
            continue

        if token_count == MATCH_ONLY_TOKEN_COUNT:
            match_only_rows += 1
        elif token_count == EVAL_TOKEN_COUNT:
            eval_rows += 1
            try:
                validate_rotation(tokens[2], line_no, "rot0")
                validate_rotation(tokens[3], line_no, "rot1")
                validate_numeric_values(tokens[4:13], 9, "K0", line_no)
                validate_numeric_values(tokens[13:22], 9, "K1", line_no)
                validate_numeric_values(tokens[22:38], 16, "T_0to1", line_no)
            except ValidationError as exc:
                errors.append(str(exc))
                continue
        elif token_count == 4:
            errors.append(
                f"Line {line_no}: standalone rotation-only rows are not supported; use 2 tokens for match-only rows or 38 tokens for evaluation rows"
            )
            continue
        else:
            errors.append(
                f"Line {line_no}: expected 2 tokens for match-only rows or 38 tokens for evaluation rows, got {token_count}"
            )
            continue

        if input_dir is not None:
            for image_token in tokens[:2]:
                resolved = resolve_image_path(image_token, input_dir)
                if resolved is None:
                    continue
                if not resolved.is_file():
                    errors.append(
                        f"Line {line_no}: missing image file referenced by {image_token!r} -> {resolved}"
                    )

    if errors:
        raise ValidationError("\n".join(errors))

    return match_only_rows, eval_rows


def main() -> int:
    args = parse_args()
    try:
        match_only_rows, eval_rows = validate_pair_file(args.pair_file, args.input_dir, args.require_gt)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    total_rows = match_only_rows + eval_rows
    mode = "evaluation" if args.require_gt else "mixed"
    print(
        f"Validated {total_rows} row(s) from {args.pair_file} in {mode} mode"
    )
    if args.input_dir is not None:
        print(f"Image existence checked against {args.input_dir}")
    print(f"Match-only rows: {match_only_rows}")
    print(f"Evaluation rows: {eval_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
