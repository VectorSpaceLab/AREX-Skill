#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Validate NuPIC legacy FileRecordStream CSV files.

This script is intentionally self-contained and does not import nupic.  It is
safe to run under Python 2.7 or Python 3 against a local CSV file before trying
an OPF, Network API, or swarming workflow.
"""
from __future__ import print_function

import argparse
import csv
import datetime
import json
import os
import sys

PY2 = sys.version_info[0] == 2
try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)

VALID_TYPES = set(["string", "datetime", "int", "float", "bool", "list", "sdr"])
PUBLIC_FLAGS = set(["", "R", "S", "T", "C"])
LEGACY_FLAGS = set(["", "R", "S", "T", "C", "L"])
TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S:%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M",
    "%m/%d/%y %H:%M",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
)


class Reporter(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)


def open_csv_for_read(path):
    if PY2:
        return open(path, "rb")
    return open(path, "r", newline="")


def read_text_file(path):
    mode = "rb" if PY2 else "r"
    with open(path, mode) as handle:
        data = handle.read()
    if PY2:
        return data
    return data


def parse_timestamp(value):
    value = value.strip()
    for pattern in TIMESTAMP_FORMATS:
        try:
            return datetime.datetime.strptime(value, pattern)
        except ValueError:
            pass
    raise ValueError("timestamp does not match NuPIC legacy formats")


def parse_bool(value):
    lower = value.strip().lower()
    if lower in ("true", "t", "1"):
        return True
    if lower in ("false", "f", "0"):
        return False
    raise ValueError("bool must be one of true/t/1/false/f/0")


def parse_value(value, field_type):
    stripped = value.strip()

    # FileRecordStream treats the empty string as a missing value.  The exact
    # missing-data sentinel is NuPIC-owned, so this validator only verifies that
    # the empty cell is allowed to pass through the stream parser.
    if stripped == "":
        return None

    if field_type == "string":
        return value
    if field_type == "datetime":
        return parse_timestamp(stripped)
    if field_type == "int":
        if stripped in ("None", "NULL"):
            return None
        return int(stripped)
    if field_type == "float":
        if stripped == "None":
            return None
        return float(stripped)
    if field_type == "bool":
        return parse_bool(stripped)
    if field_type == "list":
        return [int(item) for item in stripped.split()]
    if field_type == "sdr":
        bad_chars = [char for char in stripped if char not in ("0", "1")]
        if bad_chars:
            raise ValueError("sdr must contain only 0 and 1 characters")
        return [int(char) for char in stripped]
    raise ValueError("unknown field type %r" % (field_type,))


def sorted_duplicates(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def read_and_validate_csv(path, args, reporter):
    if not os.path.exists(path):
        reporter.error("CSV file does not exist: %s" % path)
        return None
    if not os.path.isfile(path):
        reporter.error("CSV path is not a regular file: %s" % path)
        return None

    allowed_flags = PUBLIC_FLAGS if args.strict_public_flags else LEGACY_FLAGS

    try:
        handle = open_csv_for_read(path)
    except IOError as exc:
        reporter.error("Could not open CSV file %s: %s" % (path, exc))
        return None

    with handle:
        reader = csv.reader(handle, dialect="excel")
        header_rows = []
        line_number = 0
        try:
            for _ in range(3):
                header_rows.append(next(reader))
                line_number += 1
        except StopIteration:
            reporter.error(
                "CSV has only %d row(s); NuPIC FileRecordStream requires three "
                "header rows: names, types, and special flags" % line_number)
            return None
        except csv.Error as exc:
            reporter.error("CSV parser failed while reading headers: %s" % exc)
            return None

        names = [cell.strip() for cell in header_rows[0]]
        types = [cell.strip() for cell in header_rows[1]]
        specials = [cell.strip() for cell in header_rows[2]]

        width = len(names)
        if width == 0:
            reporter.error("Header row 1 is empty; expected at least one field name")
            return None

        if len(specials) == 0 and width == 1:
            # Matches FileRecordStream's one-column blank-special-row behavior.
            specials = [""]

        if len(types) != width or len(specials) != width:
            reporter.error(
                "Header rows have different widths: names=%d, types=%d, specials=%d. "
                "Add a third special-flag row with one cell per field." %
                (width, len(types), len(specials)))

        for index, name in enumerate(names):
            if not name:
                reporter.error("Header row 1 column %d has an empty field name" % (index + 1))
        duplicates = sorted_duplicates(names)
        if duplicates:
            reporter.warn("Duplicate field names can confuse encoders/search definitions: %s" %
                          ", ".join(duplicates))

        for index, field_type in enumerate(types):
            if field_type not in VALID_TYPES:
                reporter.error(
                    "Header row 2 column %d has invalid field type %r; expected one of %s" %
                    (index + 1, field_type, ", ".join(sorted(VALID_TYPES))))

        invalid_flags = []
        for index, flag in enumerate(specials):
            if flag not in allowed_flags:
                invalid_flags.append((index, flag))
                reporter.error(
                    "Header row 3 column %d has invalid special flag %r; expected blank or one of %s" %
                    (index + 1, flag, ", ".join(sorted([f for f in allowed_flags if f]))))
            elif flag == "L" and not args.strict_public_flags:
                reporter.warn(
                    "Header row 3 column %d uses legacy source-level flag 'L' (learning). "
                    "Public quick-start guidance only documents R/S/T/C." % (index + 1))

        if invalid_flags:
            reporter.warn(
                "If row 3 contains data values instead of flags, the file is probably "
                "missing the third NuPIC special-flag header row.")

        # Compatibility checks only make sense where all three headers line up.
        if len(types) == width and len(specials) == width:
            for index, (field_name, field_type, flag) in enumerate(zip(names, types, specials)):
                col = index + 1
                if flag == "T" and field_type != "datetime":
                    reporter.error("Column %d (%s) has T flag but type %r; timestamp fields must be datetime" %
                                   (col, field_name, field_type))
                elif flag == "S" and field_type not in ("string", "int"):
                    reporter.error("Column %d (%s) has S flag but type %r; sequence id should be string or int" %
                                   (col, field_name, field_type))
                elif flag == "R":
                    if field_type == "bool":
                        reporter.warn("Column %d (%s) uses bool with R flag; int 0/1 is safest for legacy FileRecordStream" %
                                      (col, field_name))
                    elif field_type != "int":
                        reporter.error("Column %d (%s) has R flag but type %r; reset should be int 0/1" %
                                       (col, field_name, field_type))
                elif flag == "C" and field_type not in ("int", "list"):
                    reporter.error("Column %d (%s) has C flag but type %r; category should be int or list" %
                                   (col, field_name, field_type))
                elif flag == "L" and field_type != "int":
                    reporter.error("Column %d (%s) has L flag but type %r; learning control should be int" %
                                   (col, field_name, field_type))

            for flag in ("T", "R", "S", "L"):
                if specials.count(flag) > 1:
                    reporter.warn("Multiple %s special flags found; most legacy workflows expect at most one" % flag)
            if specials.count("C") > 1:
                reporter.warn("Multiple C category flags found; verify the consuming workflow supports them")

        checked_rows = 0
        total_rows_seen = 0
        timestamp_index = specials.index("T") if "T" in specials else None
        sequence_index = specials.index("S") if "S" in specials else None
        reset_index = specials.index("R") if "R" in specials else None
        last_timestamp_by_sequence = {}

        if args.header_only:
            return {
                "names": names,
                "types": types,
                "specials": specials,
                "checked_rows": 0,
                "total_rows_seen": 0,
                "limited": False,
            }

        try:
            for row in reader:
                line_number += 1
                total_rows_seen += 1

                if args.max_data_rows is not None and checked_rows >= args.max_data_rows:
                    return {
                        "names": names,
                        "types": types,
                        "specials": specials,
                        "checked_rows": checked_rows,
                        "total_rows_seen": total_rows_seen - 1,
                        "limited": True,
                    }

                checked_rows += 1

                if len(row) == 0:
                    reporter.error("Row %d is blank; NuPIC data rows should have %d columns" %
                                   (line_number, width))
                    continue
                if len(row) != width:
                    reporter.error("Row %d has %d columns but header has %d" %
                                   (line_number, len(row), width))
                    continue
                if len(types) != width:
                    continue

                parsed_values = []
                for index, (value, field_type) in enumerate(zip(row, types)):
                    try:
                        parsed = parse_value(value, field_type)
                        parsed_values.append(parsed)
                    except Exception as exc:  # ValueError plus rare conversion errors.
                        reporter.error("Row %d column %d (%s, %s) value %r failed to parse: %s" %
                                       (line_number, index + 1, names[index], field_type, value, exc))
                        parsed_values.append(None)

                if reset_index is not None and reset_index < len(parsed_values):
                    reset_value = parsed_values[reset_index]
                    if reset_value not in (None, 0, 1, False, True):
                        reporter.error("Row %d reset field %s has value %r; expected 0/1 or boolean" %
                                       (line_number, names[reset_index], row[reset_index]))

                if timestamp_index is not None and timestamp_index < len(parsed_values):
                    timestamp = parsed_values[timestamp_index]
                    if isinstance(timestamp, datetime.datetime):
                        if sequence_index is not None and sequence_index < len(parsed_values):
                            sequence_key = parsed_values[sequence_index]
                        else:
                            sequence_key = "__single_sequence__"
                        reset_value = None
                        if reset_index is not None and reset_index < len(parsed_values):
                            reset_value = parsed_values[reset_index]
                        if reset_value in (1, True):
                            last_timestamp_by_sequence[sequence_key] = None
                        previous = last_timestamp_by_sequence.get(sequence_key)
                        if previous is not None and timestamp < previous:
                            reporter.warn("Row %d timestamp goes backward within sequence %r" %
                                          (line_number, sequence_key))
                        last_timestamp_by_sequence[sequence_key] = timestamp
        except csv.Error as exc:
            reporter.error("CSV parser failed near row %d: %s" % (line_number + 1, exc))

    return {
        "names": names,
        "types": types,
        "specials": specials,
        "checked_rows": checked_rows,
        "total_rows_seen": total_rows_seen,
        "limited": False,
    }


def load_model_params(path, reporter):
    if not os.path.exists(path):
        reporter.error("Model params file does not exist: %s" % path)
        return None
    try:
        text = read_text_file(path)
    except IOError as exc:
        reporter.error("Could not read model params %s: %s" % (path, exc))
        return None

    lower_path = path.lower()
    try:
        return json.loads(text)
    except Exception as json_exc:
        if lower_path.endswith(".json"):
            reporter.error("Model params %s is not valid JSON: %s" % (path, json_exc))
            return None

    try:
        import yaml  # Optional; only needed for YAML model params.
    except ImportError as exc:
        reporter.error(
            "Could not import PyYAML to parse YAML model params %s: %s. "
            "Use JSON params or install PyYAML in the active environment." % (path, exc))
        return None

    try:
        return yaml.safe_load(text)
    except Exception as yaml_exc:
        reporter.error("Model params %s is not valid YAML/JSON: %s" % (path, yaml_exc))
        return None


def get_nested_dict(root, path):
    value = root
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def validate_model_params(config, csv_fields, cli_predicted_fields, cli_encoder_fields, reporter):
    if config is None:
        return set()
    if not isinstance(config, dict):
        reporter.error("Model params root should be a dictionary/object")
        return set()

    model_params = config.get("modelParams")
    if not isinstance(model_params, dict):
        reporter.error("Model params should contain dictionary key modelParams")
        return set()

    encoders = get_nested_dict(config, ["modelParams", "sensorParams", "encoders"])
    encoder_fields = set()
    if encoders is None:
        reporter.warn("modelParams.sensorParams.encoders is missing; cannot check encoder fieldnames")
    elif not isinstance(encoders, dict):
        reporter.error("modelParams.sensorParams.encoders should be a dictionary/object")
    else:
        for encoder_name in sorted(encoders.keys()):
            encoder_config = encoders[encoder_name]
            if encoder_config in (None, False):
                continue
            if not isinstance(encoder_config, dict):
                reporter.warn("Encoder %r is not a dictionary; skipped fieldname check" % encoder_name)
                continue
            fieldname = encoder_config.get("fieldname")
            if fieldname is None:
                fieldname = encoder_config.get("fieldName")
            if fieldname is None:
                reporter.warn("Encoder %r has no fieldname; verify it is intentional" % encoder_name)
                continue
            encoder_fields.add(fieldname)
            if fieldname not in csv_fields:
                reporter.error("Encoder %r fieldname %r is not present in CSV header" %
                               (encoder_name, fieldname))

    model_predicted = model_params.get("predictedField")
    if model_predicted is not None:
        if model_predicted not in csv_fields:
            reporter.error("modelParams.predictedField %r is not present in CSV header" % model_predicted)
        if encoder_fields and model_predicted not in encoder_fields:
            reporter.warn("modelParams.predictedField %r is not used by any encoder fieldname" % model_predicted)

    for predicted in cli_predicted_fields:
        if predicted not in csv_fields:
            reporter.error("Requested predicted field %r is not present in CSV header" % predicted)
        if model_predicted is not None and predicted != model_predicted:
            reporter.warn("Requested predicted field %r differs from modelParams.predictedField %r" %
                          (predicted, model_predicted))
        if encoder_fields and predicted not in encoder_fields:
            reporter.warn("Requested predicted field %r is not used by any encoder fieldname" % predicted)

    for field in cli_encoder_fields:
        if field not in csv_fields:
            reporter.error("Requested encoder field %r is not present in CSV header" % field)
        if encoder_fields and field not in encoder_fields:
            reporter.error("Requested encoder field %r is not present in model params encoder fieldnames" % field)

    aggregation_info = config.get("aggregationInfo")
    if isinstance(aggregation_info, dict):
        fields = aggregation_info.get("fields")
        if fields is not None:
            for item in fields:
                try:
                    field_name = item[0]
                    function_name = item[1]
                except Exception:
                    reporter.error("aggregationInfo.fields entry %r should be [fieldName, functionName]" % (item,))
                    continue
                if field_name not in csv_fields:
                    reporter.error("aggregationInfo field %r is not present in CSV header" % field_name)
                if isinstance(function_name, STRING_TYPES):
                    simple_name = function_name.split(":", 1)[0]
                    if simple_name not in ("first", "last", "sum", "mean", "max", "min", "mode", "wmean"):
                        reporter.warn("aggregationInfo field %r uses uncommon aggregation function %r" %
                                      (field_name, function_name))

    return encoder_fields


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate a NuPIC legacy FileRecordStream CSV without importing nupic.")
    parser.add_argument("csv_path", help="Path to the NuPIC CSV stream file to validate")
    parser.add_argument(
        "--model-params",
        help="Optional model params JSON/YAML file. JSON uses stdlib; YAML requires PyYAML.")
    parser.add_argument(
        "--predicted-field", action="append", default=[],
        help="Expected predicted field name. May be supplied more than once.")
    parser.add_argument(
        "--encoder-field", action="append", default=[],
        help="Expected encoder fieldname. May be supplied more than once.")
    parser.add_argument(
        "--strict-public-flags", action="store_true",
        help="Reject source-level L learning flag and allow only public blank/R/S/T/C flags.")
    parser.add_argument(
        "--header-only", action="store_true",
        help="Validate only the three header rows; do not scan data rows.")
    parser.add_argument(
        "--max-data-rows", type=int,
        help="Validate at most this many data rows after the three headers.")
    return parser


def print_report(path, context, reporter, model_params_path):
    print("NuPIC CSV validation summary")
    print("  csv: %s" % path)
    if context is not None:
        print("  columns: %d" % len(context["names"]))
        print("  field names: %s" % ", ".join(context["names"]))
        if context["limited"]:
            print("  data rows checked: %d (limited by --max-data-rows)" % context["checked_rows"])
        else:
            print("  data rows checked: %d" % context["checked_rows"])
    if model_params_path:
        print("  model params: %s" % model_params_path)
    print("  errors: %d" % len(reporter.errors))
    print("  warnings: %d" % len(reporter.warnings))

    for message in reporter.errors:
        print("ERROR: %s" % message)
    for message in reporter.warnings:
        print("WARNING: %s" % message)

    if not reporter.errors:
        print("OK: CSV passed the selected NuPIC legacy data/configuration checks")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_data_rows is not None and args.max_data_rows < 0:
        parser.error("--max-data-rows must be >= 0")

    reporter = Reporter()
    context = read_and_validate_csv(args.csv_path, args, reporter)

    if context is not None:
        csv_fields = set(context["names"])
        config = None
        if args.model_params:
            config = load_model_params(args.model_params, reporter)
        if config is not None:
            validate_model_params(config, csv_fields, args.predicted_field, args.encoder_field, reporter)
        else:
            for predicted in args.predicted_field:
                if predicted not in csv_fields:
                    reporter.error("Requested predicted field %r is not present in CSV header" % predicted)
            for field in args.encoder_field:
                if field not in csv_fields:
                    reporter.error("Requested encoder field %r is not present in CSV header" % field)

    print_report(args.csv_path, context, reporter, args.model_params)
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
