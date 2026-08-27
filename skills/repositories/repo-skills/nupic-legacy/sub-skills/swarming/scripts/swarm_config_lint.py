#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Safe stdlib linter for NuPIC legacy swarming search_def.json files.

This script intentionally does not import nupic and does not run a swarm.  It
checks the JSON shape and common configuration mistakes before a Python 2.7
NuPIC runtime, MySQL service, or HyperSearch workers are involved.
"""
from __future__ import print_function

import argparse
import io
import os
import sys

try:
    import json
except ImportError as exc:  # pragma: no cover - json is stdlib in supported Pythons
    sys.stderr.write("FATAL: could not import Python's json module: %s\n" % (exc,))
    sys.exit(3)

try:
    string_types = (basestring,)
except NameError:  # Python 3
    string_types = (str,)

try:
    integer_types = (int, long)
except NameError:  # Python 3
    integer_types = (int,)

ALLOWED_FIELD_TYPES = set(["datetime", "float", "int", "string"])
ALLOWED_INFERENCE_TYPES = set([
    "NontemporalClassification",
    "TemporalMultiStep",
    "NontemporalMultiStep",
    "TemporalClassification",
    "TemporalNextStep",
    "TemporalAnomaly",
    "NontemporalAnomaly",
    "MultiStep",
])
ALLOWED_SWARM_SIZES = set(["small", "medium", "large"])
ALLOWED_INPUT_PREDICTED_FIELD = set(["auto", "yes", "no"])
TIME_UNITS = [
    "microseconds", "milliseconds", "seconds", "minutes", "hours",
    "days", "weeks", "months", "years",
]


class Reporter(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def emit(self):
        for message in self.errors:
            print("ERROR: %s" % message)
        for message in self.warnings:
            print("WARN: %s" % message)


def is_string(value):
    return isinstance(value, string_types)


def is_integer(value):
    return isinstance(value, integer_types) and not isinstance(value, bool)


def is_number(value):
    return isinstance(value, integer_types + (float,)) and not isinstance(value, bool)


def load_json(path, reporter):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except IOError as exc:
        reporter.error("cannot read JSON file %r: %s" % (path, exc))
    except ValueError as exc:
        reporter.error("invalid JSON in %r: %s" % (path, exc))
    return None


def file_url_to_path(source):
    """Return path part for a file:// URL-like source used by NuPIC streams."""
    if not is_string(source) or not source.startswith("file://"):
        return None
    path = source[len("file://"):]
    # file:///data/a.csv leaves /data/a.csv after removing file://.
    return path


def resolve_file_source(json_dir, source):
    path = file_url_to_path(source)
    if path is None or path == "":
        return None
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(json_dir, path))


def check_included_fields(config, reporter):
    fields = config.get("includedFields")
    names = []
    if not isinstance(fields, list) or not fields:
        reporter.error("includedFields must be a non-empty list")
        return names

    seen = set()
    for index, field in enumerate(fields):
        prefix = "includedFields[%d]" % index
        if not isinstance(field, dict):
            reporter.error("%s must be an object" % prefix)
            continue

        name = field.get("fieldName")
        field_type = field.get("fieldType")

        if not is_string(name) or not name.strip():
            reporter.error("%s.fieldName must be a non-empty string" % prefix)
        else:
            names.append(name)
            if name in seen:
                reporter.error("duplicate included field name %r" % name)
            seen.add(name)

        if not is_string(field_type) or not field_type.strip():
            reporter.error("%s.fieldType must be a non-empty string" % prefix)
        elif field_type not in ALLOWED_FIELD_TYPES:
            reporter.warn(
                "%s.fieldType %r is unusual; expected one of %s" %
                (prefix, field_type, sorted(ALLOWED_FIELD_TYPES)))

        if "minValue" in field and not is_number(field.get("minValue")):
            reporter.warn("%s.minValue should be numeric when present" % prefix)
        if "maxValue" in field and not is_number(field.get("maxValue")):
            reporter.warn("%s.maxValue should be numeric when present" % prefix)
        if "runDelta" in field and not isinstance(field.get("runDelta"), bool):
            reporter.warn("%s.runDelta should be boolean when present" % prefix)

    return names


def check_stream_def(config, json_path, reporter, check_files):
    stream_def = config.get("streamDef")
    if not isinstance(stream_def, dict):
        reporter.error("streamDef must be an object")
        return []

    streams = stream_def.get("streams")
    sources = []
    if not isinstance(streams, list) or not streams:
        reporter.error("streamDef.streams must be a non-empty list")
    else:
        json_dir = os.path.dirname(os.path.abspath(json_path)) or os.getcwd()
        for index, stream in enumerate(streams):
            prefix = "streamDef.streams[%d]" % index
            if not isinstance(stream, dict):
                reporter.error("%s must be an object" % prefix)
                continue
            source = stream.get("source")
            if not is_string(source) or not source:
                reporter.error("%s.source must be a non-empty file:// string" % prefix)
                continue
            sources.append(source)
            if not source.startswith("file://"):
                reporter.error("%s.source must start with file://, got %r" % (prefix, source))
                continue
            path_part = file_url_to_path(source)
            if path_part in (None, ""):
                reporter.error("%s.source has an empty file:// path" % prefix)
                continue
            if source.startswith("file://~"):
                reporter.warn("%s.source contains ~; expand it before running NuPIC" % prefix)
            if check_files:
                resolved = resolve_file_source(json_dir, source)
                if resolved is None or not os.path.exists(resolved):
                    reporter.error("%s.source file does not exist: %r resolved to %r" %
                                   (prefix, source, resolved))
            columns = stream.get("columns")
            if columns is not None and not isinstance(columns, list):
                reporter.warn("%s.columns should be a list such as [\"*\"]" % prefix)
            last_record = stream.get("last_record")
            if last_record is not None and (not is_integer(last_record) or last_record < 0):
                reporter.warn("%s.last_record should be a non-negative integer when present" % prefix)

    aggregation = stream_def.get("aggregation")
    if aggregation is not None:
        if not isinstance(aggregation, dict):
            reporter.error("streamDef.aggregation must be an object when present")
        else:
            fields = aggregation.get("fields")
            if fields is not None:
                if not isinstance(fields, list):
                    reporter.error("streamDef.aggregation.fields must be a list of [fieldName, function]")
                else:
                    for index, item in enumerate(fields):
                        ok = (isinstance(item, list) and len(item) == 2 and
                              is_string(item[0]) and is_string(item[1]))
                        if not ok:
                            reporter.error(
                                "streamDef.aggregation.fields[%d] must be [fieldName, function] strings" % index)
            for unit in TIME_UNITS:
                value = aggregation.get(unit)
                if value is not None and (not is_integer(value) or value < 0):
                    reporter.warn("streamDef.aggregation.%s should be a non-negative integer" % unit)

    version = stream_def.get("version")
    if version is not None and not is_integer(version):
        reporter.warn("streamDef.version should be an integer when present")

    return sources


def check_inference(config, included_names, reporter):
    inference_type = config.get("inferenceType")
    if not is_string(inference_type) or not inference_type:
        reporter.error("inferenceType must be a non-empty string")
    elif inference_type not in ALLOWED_INFERENCE_TYPES:
        reporter.error("inferenceType %r is not one of %s" %
                       (inference_type, sorted(ALLOWED_INFERENCE_TYPES)))

    inference_args = config.get("inferenceArgs")
    if not isinstance(inference_args, dict):
        reporter.error("inferenceArgs must be an object")
        return

    prediction_steps = inference_args.get("predictionSteps")
    if not isinstance(prediction_steps, list) or not prediction_steps:
        reporter.error("inferenceArgs.predictionSteps must be a non-empty list")
    else:
        for index, step in enumerate(prediction_steps):
            if not is_integer(step):
                reporter.error("inferenceArgs.predictionSteps[%d] must be an integer" % index)
            elif step < 0:
                reporter.error("inferenceArgs.predictionSteps[%d] must be >= 0" % index)
            elif step == 0:
                reporter.warn("inferenceArgs.predictionSteps[%d] is 0; prediction swarms usually use positive steps" % index)

    predicted_field = inference_args.get("predictedField")
    if not is_string(predicted_field) or not predicted_field.strip():
        reporter.error("inferenceArgs.predictedField must be a non-empty string for prediction swarms")
    elif included_names and predicted_field not in included_names:
        reporter.warn("predictedField %r is not listed in includedFields %s" %
                      (predicted_field, sorted(included_names)))

    input_predicted_field = inference_args.get("inputPredictedField")
    if input_predicted_field is not None and input_predicted_field not in ALLOWED_INPUT_PREDICTED_FIELD:
        reporter.warn("inferenceArgs.inputPredictedField should be one of %s" %
                      sorted(ALLOWED_INPUT_PREDICTED_FIELD))


def check_iteration_and_size(config, reporter):
    iteration_count = config.get("iterationCount")
    if not is_integer(iteration_count):
        reporter.error("iterationCount must be an integer; use -1 for all records")
    elif iteration_count < -1:
        reporter.error("iterationCount must be >= -1")
    elif iteration_count == 0:
        reporter.warn("iterationCount is 0; use a small positive value for smoke tests or -1 for all records")

    swarm_size = config.get("swarmSize")
    if not is_string(swarm_size) or not swarm_size:
        reporter.error("swarmSize must be one of %s" % sorted(ALLOWED_SWARM_SIZES))
    elif swarm_size not in ALLOWED_SWARM_SIZES:
        reporter.error("swarmSize %r is not one of %s" % (swarm_size, sorted(ALLOWED_SWARM_SIZES)))


def check_field_cross_references(config, included_names, reporter):
    included = set(included_names)
    stream_def = config.get("streamDef")
    if isinstance(stream_def, dict):
        aggregation = stream_def.get("aggregation")
        if isinstance(aggregation, dict):
            fields = aggregation.get("fields")
            if isinstance(fields, list):
                for index, item in enumerate(fields):
                    if isinstance(item, list) and item and is_string(item[0]):
                        field_name = item[0]
                        if included and field_name not in included:
                            reporter.warn(
                                "aggregation field %r at index %d is not listed in includedFields" %
                                (field_name, index))


def check_custom_error_metric(config, reporter):
    metric = config.get("customErrorMetric")
    if metric is None:
        return
    if not isinstance(metric, dict):
        reporter.error("customErrorMetric must be an object when present")
        return
    custom_expr = metric.get("customExpr")
    if custom_expr is None:
        reporter.warn("customErrorMetric is present without customExpr")
    elif not is_string(custom_expr):
        reporter.error("customErrorMetric.customExpr must be a string")
    elif custom_expr.strip() == "":
        reporter.warn("customErrorMetric.customExpr is empty")
    error_window = metric.get("errorWindow")
    if error_window is not None and (not is_integer(error_window) or error_window <= 0):
        reporter.warn("customErrorMetric.errorWindow should be a positive integer when present")


def summarize(config, sources):
    included = config.get("includedFields") if isinstance(config, dict) else []
    if not isinstance(included, list):
        included = []
    print("Summary:")
    print("  includedFields: %d" % len(included))
    print("  stream sources: %d" % len(sources))
    print("  inferenceType: %r" % config.get("inferenceType"))
    args = config.get("inferenceArgs") if isinstance(config.get("inferenceArgs"), dict) else {}
    print("  predictedField: %r" % args.get("predictedField"))
    print("  predictionSteps: %r" % args.get("predictionSteps"))
    print("  iterationCount: %r" % config.get("iterationCount"))
    print("  swarmSize: %r" % config.get("swarmSize"))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Lint a NuPIC legacy swarming search_def.json without importing NuPIC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/swarm_config_lint.py search_def.json\n"
            "  python scripts/swarm_config_lint.py search_def.json --check-files --strict\n\n"
            "Exit codes:\n"
            "  0  no errors\n"
            "  1  validation errors\n"
            "  2  warnings treated as errors with --strict\n"
            "  3  file/import/JSON loading failure\n"))
    parser.add_argument("search_def", help="Path to a NuPIC swarming search definition JSON file")
    parser.add_argument("--check-files", action="store_true",
                        help="Verify file:// stream sources exist relative to the JSON file directory")
    parser.add_argument("--strict", action="store_true",
                        help="Return exit code 2 when warnings are present")
    parser.add_argument("--summary", action="store_true",
                        help="Print a short summary of important keys")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    reporter = Reporter()
    config = load_json(args.search_def, reporter)
    if config is None:
        reporter.emit()
        return 3

    if not isinstance(config, dict):
        reporter.error("top-level JSON value must be an object")
        reporter.emit()
        return 1

    included_names = check_included_fields(config, reporter)
    sources = check_stream_def(config, args.search_def, reporter, args.check_files)
    check_inference(config, included_names, reporter)
    check_iteration_and_size(config, reporter)
    check_field_cross_references(config, included_names, reporter)
    check_custom_error_metric(config, reporter)

    if args.summary:
        summarize(config, sources)

    reporter.emit()
    if reporter.errors:
        print("FAILED: %d error(s), %d warning(s)" % (len(reporter.errors), len(reporter.warnings)))
        return 1
    if args.strict and reporter.warnings:
        print("FAILED: 0 error(s), %d warning(s) treated as errors" % len(reporter.warnings))
        return 2
    if reporter.warnings:
        print("OK: 0 errors, %d warning(s)" % len(reporter.warnings))
    else:
        print("OK: no obvious swarming search definition issues found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
