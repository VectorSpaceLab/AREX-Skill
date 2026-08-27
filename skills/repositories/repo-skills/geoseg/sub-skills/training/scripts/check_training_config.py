#!/usr/bin/env python3
"""Safely validate a GeoSeg training config without importing or executing it.

The repository's configs construct datasets, models, optimizers, and sometimes
load checkpoints at module import time. This validator deliberately uses only
stdlib AST parsing and literal inspection; it never imports the config and
never launches training.
"""

import argparse
import ast
import sys
from pathlib import Path


REQUIRED = (
    "net",
    "loss",
    "train_loader",
    "val_loader",
    "classes",
    "num_classes",
    "use_aux_loss",
    "gpus",
    "max_epoch",
    "check_val_every_n_epoch",
    "monitor",
    "monitor_mode",
    "save_top_k",
    "save_last",
    "weights_path",
    "weights_name",
    "log_name",
    "pretrained_ckpt_path",
    "resume_ckpt_path",
    "optimizer",
    "lr_scheduler",
)

RECOMMENDED = (
    "ignore_index",
    "train_batch_size",
    "val_batch_size",
)

MONITORS = ("val_mIoU", "val_F1", "val_OA")


def _target_names(target):
    """Return simple names introduced by an assignment target."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for item in target.elts:
            names.extend(_target_names(item))
        return names
    return []


def _top_level_assignments(tree):
    """Map top-level assignment names to their final AST value nodes."""
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _target_names(target):
                    values[name] = node.value
        elif isinstance(node, ast.AnnAssign):
            for name in _target_names(node.target):
                values[name] = node.value
    return values


def _literal(node):
    """Return (is_literal, value), handling only safe literal expressions."""
    if node is None:
        return False, None
    try:
        return True, ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False, None


def _literal_display(node):
    is_literal, value = _literal(node)
    if is_literal:
        return repr(value)
    return "<runtime expression>"


def _is_none(node):
    is_literal, value = _literal(node)
    return is_literal and value is None


def validate(path):
    errors = []
    warnings = []

    if path.suffix != ".py":
        errors.append("config path must have a .py suffix")
    if "." in path.stem:
        errors.append("config filename stem may not contain a dot")
    if not path.exists():
        errors.append("config file does not exist")
    if errors:
        return errors, warnings, {}

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError) as exc:
        errors.append("could not read config: {}".format(exc))
        return errors, warnings, {}
    except SyntaxError as exc:
        errors.append("Python syntax error at line {}: {}".format(exc.lineno, exc.msg))
        return errors, warnings, {}

    values = _top_level_assignments(tree)
    missing = [name for name in REQUIRED if name not in values]
    for name in missing:
        errors.append("missing top-level assignment: {}".format(name))

    for name in RECOMMENDED:
        if name not in values:
            warnings.append("recommended assignment is absent: {}".format(name))

    if "monitor" in values:
        is_literal, monitor = _literal(values["monitor"])
        if is_literal and monitor not in MONITORS:
            errors.append(
                "monitor must be one of {}; got {!r}".format(
                    ", ".join(MONITORS), monitor
                )
            )
        elif not is_literal:
            warnings.append("monitor is a runtime expression; cannot check its name")

    if "monitor_mode" in values:
        is_literal, mode = _literal(values["monitor_mode"])
        if is_literal and mode not in ("max", "min"):
            errors.append("monitor_mode must be 'max' or 'min'; got {!r}".format(mode))
        elif not is_literal:
            warnings.append("monitor_mode is a runtime expression; cannot check it")

    for name in ("max_epoch", "check_val_every_n_epoch", "num_classes"):
        if name not in values:
            continue
        is_literal, value = _literal(values[name])
        if is_literal:
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append("{} must be a positive integer; got {!r}".format(name, value))
        else:
            warnings.append("{} is a runtime expression; positivity is unverified".format(name))

    if "save_top_k" in values:
        is_literal, value = _literal(values["save_top_k"])
        if is_literal:
            if not isinstance(value, int) or isinstance(value, bool) or value < -1:
                errors.append("save_top_k must be an integer >= -1; got {!r}".format(value))
        else:
            warnings.append("save_top_k is a runtime expression; range is unverified")

    if "save_last" in values:
        is_literal, value = _literal(values["save_last"])
        if is_literal and not isinstance(value, bool):
            errors.append("save_last must be boolean; got {!r}".format(value))
        elif not is_literal:
            warnings.append("save_last is a runtime expression; type is unverified")

    if "use_aux_loss" in values:
        is_literal, value = _literal(values["use_aux_loss"])
        if is_literal and not isinstance(value, bool):
            errors.append("use_aux_loss must be boolean; got {!r}".format(value))
        elif not is_literal:
            warnings.append("use_aux_loss is a runtime expression; type is unverified")

    # A pure resume restores optimizer/scheduler/callback state. The source
    # accepts both fields syntactically, but using both creates ambiguous state
    # precedence and is intentionally rejected by this safe preflight.
    if "pretrained_ckpt_path" in values and "resume_ckpt_path" in values:
        pretrained_none = _is_none(values["pretrained_ckpt_path"])
        resume_none = _is_none(values["resume_ckpt_path"])
        if not pretrained_none and not resume_none:
            errors.append(
                "choose one checkpoint intent: set only pretrained_ckpt_path "
                "or only resume_ckpt_path"
            )
        elif not pretrained_none or not resume_none:
            warnings.append("checkpoint mode: one checkpoint path is configured")
        else:
            warnings.append("checkpoint mode: fresh run (both checkpoint paths are None)")

    if "classes" in values:
        is_literal, classes = _literal(values["classes"])
        if is_literal and not isinstance(classes, (tuple, list)):
            errors.append("classes should be a tuple or list of class names")
        elif not is_literal:
            warnings.append("classes is a runtime expression; class-count alignment is unverified")

    if "ignore_index" not in values:
        warnings.append("ignore_index is absent; verify the loss and mask encoding manually")

    # These are intentionally warnings: the validator must not execute imports
    # to discover the runtime type of a network, loader, loss, optimizer, or
    # scheduler.
    for name in ("net", "loss", "train_loader", "val_loader", "optimizer", "lr_scheduler"):
        if name in values:
            warnings.append("{} runtime type is not inspected (safe static mode)".format(name))

    details = {
        "assignments": sorted(values),
        "monitor": _literal_display(values.get("monitor")),
        "num_classes": _literal_display(values.get("num_classes")),
        "use_aux_loss": _literal_display(values.get("use_aux_loss")),
    }
    return errors, warnings, details


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Statically validate a GeoSeg training config without importing it."
    )
    parser.add_argument("config", type=Path, help="Python config path")
    args = parser.parse_args(argv)

    errors, warnings, details = validate(args.config)
    print("GeoSeg training config: {}".format(args.config))
    print("Execution: none (AST parse only; no imports, data access, or training)" )
    for error in errors:
        print("ERROR: {}".format(error))
    for warning in warnings:
        print("WARNING: {}".format(warning))
    if details:
        print("Assignments discovered: {}".format(len(details["assignments"])))
        print("monitor: {}".format(details["monitor"]))
        print("num_classes: {}".format(details["num_classes"]))
        print("use_aux_loss: {}".format(details["use_aux_loss"]))

    if errors:
        print("RESULT: FAIL (fix errors before config import)")
        return 1
    print("RESULT: PASS (static contract passed; runtime/data checks remain)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
