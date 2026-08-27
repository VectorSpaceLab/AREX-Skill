#!/usr/bin/env python3
"""Safe preflight checks for tensorflow-yolov3 conversion inputs.

The script validates expected checkpoint shard names, class/anchor files, and
PB output paths. It does not import TensorFlow, build a graph, restore weights,
write checkpoints, or convert model artifacts.
"""

from __future__ import print_function

import argparse
import glob
import json
import os
import re
import sys

OUTPUT_NODE_NAMES = [
    "input/input_data",
    "pred_sbbox/concat_2",
    "pred_mbbox/concat_2",
    "pred_lbbox/concat_2",
]

DEFAULTS = {
    "original_ckpt": "checkpoint/yolov3_coco.ckpt",
    "demo_ckpt": "checkpoint/yolov3_coco_demo.ckpt",
    "pb_output": "yolov3_coco.pb",
    "classes": "data/classes/coco.names",
    "anchors": "data/anchors/basline_anchors.txt",
}


def _abs_path(root, value):
    if os.path.isabs(value):
        return os.path.abspath(value)
    return os.path.abspath(os.path.join(root, value))


def _display(path, root):
    path_abs = os.path.abspath(path)
    root_abs = os.path.abspath(root)
    try:
        common = os.path.commonpath([path_abs, root_abs])
    except ValueError:
        return path
    if common == root_abs:
        rel = os.path.relpath(path_abs, root_abs)
        return "." if rel == "." else rel.replace(os.sep, "/")
    return path


def _finding(findings, level, code, message, path=None, remedy=None, strict_fail=False):
    item = {
        "level": level,
        "code": code,
        "message": message,
        "strictFail": bool(strict_fail),
    }
    if path is not None:
        item["path"] = path
    if remedy:
        item["remedy"] = remedy
    findings.append(item)


def _check_checkpoint(findings, root, label, prefix, required_for):
    prefix_abs = _abs_path(root, prefix)
    prefix_rel = _display(prefix_abs, root)
    meta = prefix_abs + ".meta"
    index = prefix_abs + ".index"
    data_glob = prefix_abs + ".data-*"
    data_files = sorted(glob.glob(data_glob))

    missing = []
    if not os.path.isfile(meta):
        missing.append(_display(meta, root))
    if not os.path.isfile(index):
        missing.append(_display(index, root))
    if not data_files:
        missing.append(_display(data_glob, root))

    if missing:
        _finding(
            findings,
            "WARN",
            "checkpoint-missing-" + label,
            "%s checkpoint prefix is incomplete for %s; missing %s"
            % (prefix_rel, required_for, ", ".join(missing)),
            path=prefix_rel,
            remedy="Extract or create the TensorFlow checkpoint shards, then pass the prefix without .meta/.index/.data suffixes.",
            strict_fail=True,
        )
    else:
        _finding(
            findings,
            "OK",
            "checkpoint-present-" + label,
            "%s has .meta, .index, and %d data shard(s)." % (prefix_rel, len(data_files)),
            path=prefix_rel,
        )

    state_file = os.path.join(os.path.dirname(prefix_abs), "checkpoint")
    if os.path.isfile(state_file):
        try:
            with open(state_file, "r") as handle:
                state_text = handle.read(4096)
        except OSError as exc:
            _finding(
                findings,
                "WARN",
                "checkpoint-state-unreadable-" + label,
                "Could not read TensorFlow checkpoint state file: %s" % exc,
                path=_display(state_file, root),
            )
        else:
            base = os.path.basename(prefix_abs)
            if base not in state_text:
                _finding(
                    findings,
                    "WARN",
                    "checkpoint-state-different-" + label,
                    "checkpoint/checkpoint exists but does not reference %s; this can be normal after manual extraction but may confuse restore debugging."
                    % base,
                    path=_display(state_file, root),
                )


def _read_nonempty_lines(path):
    with open(path, "r") as handle:
        return [line.strip() for line in handle if line.strip() and not line.lstrip().startswith("#")]


def _check_classes(findings, root, classes_path, train_from_coco):
    classes_abs = _abs_path(root, classes_path)
    classes_rel = _display(classes_abs, root)
    if not os.path.isfile(classes_abs):
        _finding(
            findings,
            "WARN",
            "classes-missing",
            "Class-name file is missing; YOLOV3 graph construction reads this file when conversion/freezing builds the model.",
            path=classes_rel,
            remedy="Create the .names file and point cfg.YOLO.CLASSES to it before running conversion.",
            strict_fail=True,
        )
        return None

    try:
        classes = _read_nonempty_lines(classes_abs)
    except UnicodeDecodeError as exc:
        _finding(findings, "ERROR", "classes-decode-error", "Could not decode class-name file: %s" % exc, path=classes_rel, strict_fail=True)
        return None
    except OSError as exc:
        _finding(findings, "ERROR", "classes-read-error", "Could not read class-name file: %s" % exc, path=classes_rel, strict_fail=True)
        return None

    if not classes:
        _finding(findings, "ERROR", "classes-empty", "Class-name file has no non-empty class names.", path=classes_rel, strict_fail=True)
        return 0

    duplicates = sorted({name for name in classes if classes.count(name) > 1})
    if duplicates:
        _finding(
            findings,
            "WARN",
            "classes-duplicates",
            "Class-name file contains duplicate names: %s" % ", ".join(duplicates[:5]),
            path=classes_rel,
        )

    count = len(classes)
    _finding(findings, "OK", "classes-present", "%s contains %d class name(s)." % (classes_rel, count), path=classes_rel)

    if count != 80 and not train_from_coco:
        _finding(
            findings,
            "WARN",
            "custom-classes-without-coco-init-flag",
            "Class count is %d, not COCO's 80. Plain convert_weight.py may hit output-head shape mismatches."
            % count,
            path=classes_rel,
            remedy="Use convert_weight.py --train_from_coco for custom classes, then train the randomly initialized heads.",
            strict_fail=True,
        )
    elif count != 80 and train_from_coco:
        _finding(
            findings,
            "OK",
            "custom-classes-coco-init-mode",
            "Custom class count is compatible with --train_from_coco because output heads are skipped and reinitialized.",
            path=classes_rel,
        )
    return count


def _check_anchors(findings, root, anchors_path):
    anchors_abs = _abs_path(root, anchors_path)
    anchors_rel = _display(anchors_abs, root)
    if not os.path.isfile(anchors_abs):
        _finding(
            findings,
            "WARN",
            "anchors-missing",
            "Anchor file is missing; YOLOV3 graph construction reads this file when conversion/freezing builds the model.",
            path=anchors_rel,
            remedy="Create a file with 18 numeric values representing 9 width,height anchor pairs.",
            strict_fail=True,
        )
        return None

    try:
        with open(anchors_abs, "r") as handle:
            text = handle.read()
    except OSError as exc:
        _finding(findings, "ERROR", "anchors-read-error", "Could not read anchor file: %s" % exc, path=anchors_rel, strict_fail=True)
        return None

    tokens = [tok for tok in re.split(r"[\s,]+", text.strip()) if tok]
    try:
        values = [float(tok) for tok in tokens]
    except ValueError as exc:
        _finding(findings, "ERROR", "anchors-parse-error", "Anchor file contains a non-numeric value: %s" % exc, path=anchors_rel, strict_fail=True)
        return None

    if len(values) != 18:
        _finding(
            findings,
            "ERROR",
            "anchors-count-invalid",
            "Anchor file should contain 18 numeric values (9 width,height pairs); found %d." % len(values),
            path=anchors_rel,
            strict_fail=True,
        )
        return len(values)

    if any(value <= 0 for value in values):
        _finding(findings, "WARN", "anchors-nonpositive", "Anchor values should be positive.", path=anchors_rel, strict_fail=True)
    else:
        _finding(findings, "OK", "anchors-present", "%s contains 9 positive width,height anchor pairs." % anchors_rel, path=anchors_rel)
    return len(values)


def _check_pb(findings, root, pb_output, expect_pb):
    pb_abs = _abs_path(root, pb_output)
    pb_rel = _display(pb_abs, root)
    parent = os.path.dirname(pb_abs) or os.getcwd()
    parent_rel = _display(parent, root)

    if os.path.isfile(pb_abs):
        size = os.path.getsize(pb_abs)
        _finding(findings, "OK", "pb-present", "%s exists (%d bytes)." % (pb_rel, size), path=pb_rel)
    else:
        level = "ERROR" if expect_pb else "WARN"
        _finding(
            findings,
            level,
            "pb-missing",
            "%s does not exist%s." % (pb_rel, " but --expect-pb was requested" if expect_pb else "; this is expected before freeze_graph.py runs"),
            path=pb_rel,
            remedy="Run freeze_graph.py after a converted/demo checkpoint exists, or choose the correct PB output path.",
            strict_fail=expect_pb,
        )

    if not os.path.isdir(parent):
        _finding(
            findings,
            "WARN",
            "pb-parent-missing",
            "PB output parent directory does not exist: %s" % parent_rel,
            path=parent_rel,
            remedy="Create the directory before freezing, or choose an output path under an existing directory.",
            strict_fail=True,
        )
    elif not os.access(parent, os.W_OK):
        _finding(findings, "WARN", "pb-parent-not-writable", "PB output parent directory is not writable: %s" % parent_rel, path=parent_rel, strict_fail=True)
    else:
        _finding(findings, "OK", "pb-parent-writable", "PB output parent directory is writable: %s" % parent_rel, path=parent_rel)


def _check_darknet(findings, root, darknet_weights):
    if not darknet_weights:
        return
    weights_abs = _abs_path(root, darknet_weights)
    weights_rel = _display(weights_abs, root)
    if os.path.isfile(weights_abs):
        _finding(findings, "OK", "darknet-weights-present", "%s exists." % weights_rel, path=weights_rel)
    else:
        _finding(
            findings,
            "WARN",
            "darknet-weights-missing",
            "Darknet .weights file was requested but is missing.",
            path=weights_rel,
            strict_fail=True,
        )
    _finding(
        findings,
        "WARN",
        "darknet-scripts-need-patching",
        "The bundled direct Darknet conversion scripts have known bugs: broken path literal, missing numpy import, and undefined output_graph in the PB script.",
        remedy="Patch and syntax-check a copy before running direct Darknet conversion, or prefer the release checkpoint flow.",
        strict_fail=True,
    )


def _print_text(args, findings):
    print("Conversion input check (no conversion performed)")
    print("Repository root: %s" % _display(os.path.abspath(args.repo_root), os.path.abspath(args.repo_root)))
    print("Mode: %s" % ("COCO-init for custom training (--train_from_coco)" if args.train_from_coco else "plain COCO/demo conversion"))
    print("Freeze output nodes: %s" % ", ".join(OUTPUT_NODE_NAMES))
    print("")
    for item in findings:
        path = " [%s]" % item["path"] if "path" in item else ""
        print("[%s] %s%s: %s" % (item["level"], item["code"], path, item["message"]))
        if item.get("remedy"):
            print("      remedy: %s" % item["remedy"])
    print("")
    counts = {"OK": 0, "WARN": 0, "ERROR": 0}
    for item in findings:
        counts[item["level"]] = counts.get(item["level"], 0) + 1
    print("Summary: %(OK)d OK, %(WARN)d warning(s), %(ERROR)d error(s)." % counts)
    print("No TensorFlow import, restore, conversion, graph freeze, or file write was attempted.")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Safely check tensorflow-yolov3 conversion prerequisites without converting weights."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root to resolve relative paths from (default: current directory).")
    parser.add_argument("--original-ckpt", default=DEFAULTS["original_ckpt"], help="Original/release checkpoint prefix used by convert_weight.py.")
    parser.add_argument("--demo-ckpt", default=DEFAULTS["demo_ckpt"], help="Converted/demo checkpoint prefix used by freeze_graph.py.")
    parser.add_argument("--pb-output", default=DEFAULTS["pb_output"], help="Frozen PB output path to check.")
    parser.add_argument("--classes", default=DEFAULTS["classes"], help="Class-name file used by cfg.YOLO.CLASSES.")
    parser.add_argument("--anchors", default=DEFAULTS["anchors"], help="Anchor file used by cfg.YOLO.ANCHORS.")
    parser.add_argument("--train-from-coco", action="store_true", help="Check expectations for convert_weight.py --train_from_coco custom-class initialization.")
    parser.add_argument("--expect-pb", action="store_true", help="Treat a missing PB output as an error, useful after freeze_graph.py should have completed.")
    parser.add_argument("--darknet-weights", help="Optional Darknet .weights path to check while warning about direct conversion script bugs.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if any strict-fail warning/error is found.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = os.path.abspath(args.repo_root)
    findings = []

    if not os.path.isdir(root):
        _finding(findings, "ERROR", "repo-root-missing", "Repository root does not exist or is not a directory.", path=args.repo_root, strict_fail=True)
    else:
        _finding(findings, "OK", "repo-root-present", "Repository root exists.", path=_display(root, root))
        _check_checkpoint(findings, root, "original", args.original_ckpt, "convert_weight.py restore")
        _check_checkpoint(findings, root, "demo", args.demo_ckpt, "freeze_graph.py restore")
        _check_classes(findings, root, args.classes, args.train_from_coco)
        _check_anchors(findings, root, args.anchors)
        _check_pb(findings, root, args.pb_output, args.expect_pb)
        _check_darknet(findings, root, args.darknet_weights)

    result = {
        "tool": "check_conversion_inputs",
        "converted": False,
        "repoRoot": _display(root, root) if os.path.isdir(root) else args.repo_root,
        "mode": "train_from_coco" if args.train_from_coco else "plain",
        "outputNodeNames": OUTPUT_NODE_NAMES,
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_text(args, findings)

    has_error = any(item["level"] == "ERROR" for item in findings)
    strict_hit = any(item.get("strictFail") for item in findings)
    if has_error or (args.strict and strict_hit):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
