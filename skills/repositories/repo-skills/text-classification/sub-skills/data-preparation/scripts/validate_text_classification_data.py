#!/usr/bin/env python3
"""Read-only validator for legacy text-classification line formats.

This helper deliberately has no TensorFlow, h5py, pickle, or repository-module
imports. It validates raw records and emits diagnostics; it never rewrites the
input.
"""

import argparse
import codecs
import json
import sys


MODES = ("single-label", "multi-label", "prediction-tsv", "relation")


def _diagnostic(line_number, level, code, message):
    return {
        "line": line_number,
        "level": level,
        "code": code,
        "message": message,
    }


def _missing_separator_diagnostic(line, marker_index, line_number):
    if marker_index > 0 and not line[marker_index - 1].isspace():
        return _diagnostic(
            line_number,
            "warning",
            "missing-label-separator",
            "label prefix is not preceded by whitespace",
        )
    return None


def _validate_single_label(line, line_number, label_prefix):
    diagnostics = []
    count = line.count(label_prefix)
    if count == 0:
        return [
            _diagnostic(
                line_number,
                "error",
                "missing-label-prefix",
                "expected one label prefix {!r}".format(label_prefix),
            )
        ]
    if count != 1:
        diagnostics.append(
            _diagnostic(
                line_number,
                "error",
                "label-prefix-count",
                "expected exactly one label prefix; found {}".format(count),
            )
        )

    marker_index = line.find(label_prefix)
    text = line[:marker_index].strip()
    label_text = line[marker_index + len(label_prefix) :].strip()
    if not text:
        diagnostics.append(
            _diagnostic(line_number, "error", "empty-text", "text field is empty")
        )
    if not label_text:
        diagnostics.append(
            _diagnostic(line_number, "error", "empty-label", "label is empty")
        )
    elif len(label_text.split()) != 1 or label_prefix in label_text:
        diagnostics.append(
            _diagnostic(
                line_number,
                "error",
                "invalid-single-label",
                "single-label mode requires exactly one non-whitespace label token",
            )
        )

    separator_diagnostic = _missing_separator_diagnostic(
        line, marker_index, line_number
    )
    if separator_diagnostic is not None:
        diagnostics.append(separator_diagnostic)
    return diagnostics


def _validate_multi_label(line, line_number, label_prefix):
    diagnostics = []
    marker_index = line.find(label_prefix)
    if marker_index < 0:
        return [
            _diagnostic(
                line_number,
                "error",
                "missing-label-prefix",
                "expected a label prefix {!r}".format(label_prefix),
            )
        ]

    text = line[:marker_index].strip()
    label_text = line[marker_index + len(label_prefix) :].strip()
    if not text:
        diagnostics.append(
            _diagnostic(line_number, "error", "empty-text", "text field is empty")
        )
    if not label_text:
        diagnostics.append(
            _diagnostic(
                line_number, "error", "empty-label-list", "label list is empty"
            )
        )
    else:
        labels = []
        for token in label_text.split():
            label = token
            if token.startswith(label_prefix):
                label = token[len(label_prefix) :]
            if not label:
                diagnostics.append(
                    _diagnostic(
                        line_number,
                        "error",
                        "empty-label",
                        "a label prefix is not followed by a label",
                    )
                )
                continue
            if label_prefix in label:
                diagnostics.append(
                    _diagnostic(
                        line_number,
                        "error",
                        "embedded-label-prefix",
                        "label token {!r} contains an embedded prefix".format(token),
                    )
                )
                continue
            labels.append(label)

        if not labels:
            diagnostics.append(
                _diagnostic(
                    line_number,
                    "error",
                    "no-valid-labels",
                    "no nonempty label tokens were found",
                )
            )
        seen = set()
        duplicates = []
        for label in labels:
            if label in seen and label not in duplicates:
                duplicates.append(label)
            seen.add(label)
        if duplicates:
            diagnostics.append(
                _diagnostic(
                    line_number,
                    "warning",
                    "duplicate-label",
                    "duplicate label(s): {}".format(", ".join(duplicates)),
                )
            )

    separator_diagnostic = _missing_separator_diagnostic(
        line, marker_index, line_number
    )
    if separator_diagnostic is not None:
        diagnostics.append(separator_diagnostic)
    return diagnostics


def _validate_prediction_tsv(line, line_number):
    fields = line.split("\t")
    if len(fields) != 2:
        return [
            _diagnostic(
                line_number,
                "error",
                "tsv-field-count",
                "expected exactly two tab-separated fields; found {}".format(
                    len(fields)
                ),
            )
        ]

    diagnostics = []
    if not fields[0].strip():
        diagnostics.append(
            _diagnostic(
                line_number, "error", "empty-question-id", "question id is empty"
            )
        )
    if not fields[1].strip():
        diagnostics.append(
            _diagnostic(line_number, "error", "empty-text", "text field is empty")
        )
    return diagnostics


def _validate_relation(line, line_number, label_prefix):
    diagnostics = []
    count = line.count(label_prefix)
    if count == 0:
        return [
            _diagnostic(
                line_number,
                "error",
                "missing-label-prefix",
                "expected one label prefix {!r}".format(label_prefix),
            )
        ]
    if count != 1:
        diagnostics.append(
            _diagnostic(
                line_number,
                "error",
                "label-prefix-count",
                "expected exactly one label prefix; found {}".format(count),
            )
        )

    marker_index = line.find(label_prefix)
    relation_text = line[:marker_index]
    label_text = line[marker_index + len(label_prefix) :].strip()
    fields = relation_text.split("\t")
    if len(fields) != 2:
        diagnostics.append(
            _diagnostic(
                line_number,
                "error",
                "relation-field-count",
                "expected exactly two tab-separated sentence fields; found {}".format(
                    len(fields)
                ),
            )
        )
    else:
        if not fields[0].strip():
            diagnostics.append(
                _diagnostic(
                    line_number,
                    "error",
                    "empty-first-sentence",
                    "first sentence is empty",
                )
            )
        if not fields[1].strip():
            diagnostics.append(
                _diagnostic(
                    line_number,
                    "error",
                    "empty-second-sentence",
                    "second sentence is empty",
                )
            )

    if not label_text:
        diagnostics.append(
            _diagnostic(line_number, "error", "empty-label", "relation label is empty")
        )
    elif len(label_text.split()) != 1 or label_prefix in label_text:
        diagnostics.append(
            _diagnostic(
                line_number,
                "error",
                "invalid-relation-label",
                "relation mode requires exactly one non-whitespace label token",
            )
        )

    separator_diagnostic = _missing_separator_diagnostic(
        line, marker_index, line_number
    )
    if separator_diagnostic is not None:
        diagnostics.append(separator_diagnostic)
    return diagnostics


def validate_line(line, line_number, mode, label_prefix):
    """Return deterministic diagnostics for one decoded line."""
    if not line.strip():
        return [
            _diagnostic(line_number, "error", "blank-line", "record is blank")
        ]
    if mode == "single-label":
        return _validate_single_label(line, line_number, label_prefix)
    if mode == "multi-label":
        return _validate_multi_label(line, line_number, label_prefix)
    if mode == "prediction-tsv":
        return _validate_prediction_tsv(line, line_number)
    if mode == "relation":
        return _validate_relation(line, line_number, label_prefix)
    raise ValueError("unsupported mode: {}".format(mode))


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Validate legacy text-classification records without TensorFlow or "
            "modifying input."
        )
    )
    parser.add_argument("path", nargs="?", default="-", help="Input file or - for stdin.")
    parser.add_argument("--mode", choices=MODES, required=True, help="Explicit line format.")
    parser.add_argument(
        "--label-prefix",
        default="__label__",
        help="Label marker for labeled modes (default: __label__).",
    )
    parser.add_argument("--encoding", default="utf-8", help="Input character encoding.")
    parser.add_argument(
        "--encoding-errors",
        choices=("strict", "replace"),
        default="strict",
        help="Decode policy; replace also emits a warning.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit one JSON summary instead of text."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return status 1 when one or more format errors are found.",
    )
    return parser


def _print_text(summary):
    ordered_fields = (
        "mode",
        "source",
        "encoding",
        "label_prefix",
        "lines",
        "valid_lines",
        "invalid_lines",
        "errors",
        "warnings",
        "status",
    )
    for field in ordered_fields:
        print("{}: {}".format(field, summary[field]))
    if summary["diagnostics"]:
        print("diagnostics:")
        for item in summary["diagnostics"]:
            location = "line {}".format(item["line"])
            print(
                "{}: {} [{}] {}".format(
                    location, item["level"].upper(), item["code"], item["message"]
                )
            )
    else:
        print("diagnostics: none")


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.label_prefix:
        parser.error("--label-prefix must not be empty")
    try:
        codecs.lookup(args.encoding)
    except LookupError:
        parser.error("unknown encoding: {}".format(args.encoding))

    source = "<stdin>" if args.path == "-" else args.path
    stream = None
    should_close = False
    try:
        if args.path == "-":
            stream = getattr(sys.stdin, "buffer", sys.stdin)
        else:
            stream = open(args.path, "rb")
            should_close = True

        diagnostics = []
        invalid_line_numbers = set()
        line_count = 0
        for line_count, raw_line in enumerate(stream, 1):
            decode_diagnostics = []
            if isinstance(raw_line, bytes):
                try:
                    line = raw_line.decode(args.encoding, errors=args.encoding_errors)
                except UnicodeDecodeError as exc:
                    item = _diagnostic(
                        line_count,
                        "error",
                        "invalid-encoding",
                        "cannot decode with {} at byte {}: {}".format(
                            args.encoding, exc.start, exc.reason
                        ),
                    )
                    diagnostics.append(item)
                    invalid_line_numbers.add(line_count)
                    continue
            else:
                line = raw_line

            line = line.rstrip("\r\n")
            if args.encoding_errors == "replace" and "\ufffd" in line:
                decode_diagnostics.append(
                    _diagnostic(
                        line_count,
                        "warning",
                        "replacement-character",
                        "input contains a Unicode replacement character after decoding",
                    )
                )
            line_diagnostics = decode_diagnostics + validate_line(
                line, line_count, args.mode, args.label_prefix
            )
            diagnostics.extend(line_diagnostics)
            if any(item["level"] == "error" for item in line_diagnostics):
                invalid_line_numbers.add(line_count)

        if line_count == 0:
            diagnostics.append(
                _diagnostic(1, "error", "empty-input", "input contains no records")
            )

    except OSError as exc:
        print("error: cannot read {}: {}".format(source, exc), file=sys.stderr)
        return 2
    finally:
        if should_close and stream is not None:
            stream.close()

    error_count = sum(item["level"] == "error" for item in diagnostics)
    warning_count = sum(item["level"] == "warning" for item in diagnostics)
    if error_count:
        status = "invalid"
    elif warning_count:
        status = "valid-with-warnings"
    else:
        status = "valid"

    summary = {
        "mode": args.mode,
        "source": source,
        "encoding": args.encoding,
        "encoding_errors": args.encoding_errors,
        "label_prefix": args.label_prefix,
        "lines": line_count,
        "valid_lines": line_count - len(invalid_line_numbers),
        "invalid_lines": len(invalid_line_numbers),
        "errors": error_count,
        "warnings": warning_count,
        "status": status,
        "diagnostics": diagnostics,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(summary)

    if args.strict and error_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
