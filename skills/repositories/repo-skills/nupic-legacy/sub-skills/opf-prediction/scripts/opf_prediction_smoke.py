#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small, safe OPF prediction smoke helper for NuPIC legacy.

Default mode imports ModelFactory and prints API availability. If --params,
--csv, and --predicted-field are supplied, it runs a bounded number of typed CSV
records through an OPF model and summarizes inference keys/predictions.

This script does not depend on the original NuPIC repository checkout.
"""
from __future__ import print_function

import argparse
import csv
import datetime
import inspect
import json
import os
import sys


MISSING_RUNTIME = """\nCould not import NuPIC OPF runtime. NuPIC legacy commonly requires Python 2.7,\nthe nupic package, compiled nupic.bindings, numpy 1.12.x-era compatibility,\nand pycapnp/capnproto for some serialization paths. Run this helper from a\nworking NuPIC legacy environment, then retry.\n"""


TYPE_ALIASES = {
    "float": "float",
    "double": "float",
    "real": "float",
    "int": "int",
    "integer": "int",
    "long": "int",
    "datetime": "datetime",
    "date": "datetime",
    "timestamp": "datetime",
    "string": "string",
    "str": "string",
    "bool": "bool",
    "boolean": "bool",
}


def import_model_factory():
    try:
        from nupic.frameworks.opf.model_factory import ModelFactory
        return ModelFactory
    except ImportError as exc:
        print(MISSING_RUNTIME, file=sys.stderr)
        print("ImportError: %s" % exc, file=sys.stderr)
        return None


def load_model_config(path):
    with open(path, "r") as handle:
        text = handle.read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to read YAML model params. Install PyYAML in "
            "the NuPIC legacy environment or provide JSON. Original error: %s" % exc)
    return yaml.safe_load(text)


def parse_field_type_overrides(values):
    overrides = {}
    for item in values or []:
        if ":" not in item:
            raise ValueError("--field-type must be NAME:TYPE, got %r" % item)
        name, typ = item.split(":", 1)
        typ = TYPE_ALIASES.get(typ.strip().lower(), typ.strip().lower())
        overrides[name.strip()] = typ
    return overrides


def normalize_type(type_name):
    return TYPE_ALIASES.get((type_name or "string").strip().lower(),
                            (type_name or "string").strip().lower())


def parse_bool(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "t", "yes", "y"):
        return True
    if text in ("0", "false", "f", "no", "n"):
        return False
    raise ValueError("cannot parse boolean value %r" % value)


def convert_value(name, value, type_name, date_format):
    typ = normalize_type(type_name)
    if value == "" or value is None:
        return None
    if typ == "float":
        return float(value)
    if typ == "int":
        return int(value)
    if typ == "datetime":
        try:
            return datetime.datetime.strptime(value, date_format)
        except ValueError:
            # ISO-like fallback that is useful for small hand-written smoke CSVs.
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.datetime.strptime(value, fmt)
                except ValueError:
                    pass
            raise
    if typ == "bool":
        return parse_bool(value)
    return value


def open_csv(path):
    if sys.version_info[0] >= 3:
        return open(path, "r", newline="")
    return open(path, "rb")


def read_typed_records(csv_path, limit, date_format, overrides):
    with open_csv(csv_path) as handle:
        reader = csv.reader(handle)
        try:
            names = next(reader)
            types = next(reader)
            flags = next(reader)
        except StopIteration:
            raise RuntimeError("CSV must contain NuPIC's three header rows: names, types, flags")

        if len(names) != len(types):
            raise RuntimeError("CSV name row and type row have different lengths")
        if len(flags) != len(names):
            raise RuntimeError("CSV flag row length does not match name row")

        field_types = dict(zip(names, types))
        field_types.update(overrides)

        count = 0
        for row in reader:
            if limit is not None and count >= limit:
                break
            if not row or all(cell == "" for cell in row):
                continue
            if len(row) != len(names):
                raise RuntimeError("data row %d has %d cells, expected %d" % (
                    count + 1, len(row), len(names)))
            record = {}
            for name, value in zip(names, row):
                record[name] = convert_value(name, value, field_types.get(name), date_format)
            count += 1
            yield record


def get_signature_text(func):
    try:
        if hasattr(inspect, "signature"):
            return str(inspect.signature(func))
    except Exception:
        pass
    try:
        return str(inspect.getargspec(func))
    except Exception:
        return "signature unavailable"


def print_import_smoke(ModelFactory):
    print("OK: imported nupic.frameworks.opf.model_factory.ModelFactory")
    print("ModelFactory.create: %s" % get_signature_text(ModelFactory.create))
    print("ModelFactory.loadFromCheckpoint: %s" % get_signature_text(
        ModelFactory.loadFromCheckpoint))


def summarize_result(result, requested_steps):
    inferences = result.inferences or {}
    keys = sorted([str(k) for k in inferences.keys()])
    print("predictionNumber=%s inferenceKeys=%s" % (
        getattr(result, "predictionNumber", None), ",".join(keys)))

    best = inferences.get("multiStepBestPredictions", {})
    all_predictions = inferences.get("multiStepPredictions", {})
    if not best and not all_predictions:
        print("  no multiStep predictions present yet")
        return

    steps = requested_steps or sorted(best.keys())
    for step in steps:
        value = best.get(step)
        if value is None:
            print("  step %s: no best prediction yet" % step)
            continue
        confidence = all_predictions.get(step, {}).get(value)
        print("  step %s: value=%r confidence=%r" % (step, value, confidence))


def run_model(args, ModelFactory):
    if bool(args.params) != bool(args.csv):
        raise RuntimeError("Use --params and --csv together, or omit both for import-only smoke")
    if not args.params:
        print_import_smoke(ModelFactory)
        return 0
    if not args.predicted_field:
        raise RuntimeError("--predicted-field is required when running records")

    model_config = load_model_config(args.params)
    if not isinstance(model_config, dict):
        raise RuntimeError("model params file did not load to a dict")
    if "model" not in model_config or "modelParams" not in model_config:
        raise RuntimeError("model config must contain top-level 'model' and 'modelParams' keys")

    model = ModelFactory.create(model_config, logLevel=args.log_level)
    model.enableInference({"predictedField": args.predicted_field})

    requested_steps = None
    if args.steps:
        requested_steps = [int(x.strip()) for x in args.steps.split(",") if x.strip()]

    overrides = parse_field_type_overrides(args.field_type)
    ran = 0
    for record in read_typed_records(args.csv, args.limit, args.date_format, overrides):
        if args.predicted_field not in record:
            raise RuntimeError("predicted field %r is missing from CSV record keys %r" % (
                args.predicted_field, sorted(record.keys())))
        result = model.run(record)
        print("record %d rawInputKeys=%s" % (ran + 1, ",".join(sorted(record.keys()))))
        summarize_result(result, requested_steps)
        ran += 1

    print("OK: ran %d record(s)" % ran)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Import-smoke or tiny bounded CSV run for NuPIC legacy OPF.")
    parser.add_argument("--params", help="YAML/JSON OPF model params to load")
    parser.add_argument("--csv", help="NuPIC three-header-row CSV to feed")
    parser.add_argument("--predicted-field", help="Field name for model.enableInference")
    parser.add_argument("--limit", type=int, default=3,
                        help="maximum data rows to run when --csv is supplied (default: 3)")
    parser.add_argument("--steps", help="comma-separated prediction steps to print, e.g. 1,5")
    parser.add_argument("--date-format", default="%m/%d/%y %H:%M",
                        help="datetime.strptime format for CSV datetime fields")
    parser.add_argument("--field-type", action="append", default=[],
                        help="override/inject a CSV field type as NAME:TYPE; may repeat")
    parser.add_argument("--log-level", type=int, default=40,
                        help="ModelFactory logging level integer (default: 40/ERROR)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    ModelFactory = import_model_factory()
    if ModelFactory is None:
        return 2

    try:
        return run_model(args, ModelFactory)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        print("Hint: verify predicted field, model-param nesting, CSV type conversion, "
              "and NuPIC legacy runtime dependencies.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
