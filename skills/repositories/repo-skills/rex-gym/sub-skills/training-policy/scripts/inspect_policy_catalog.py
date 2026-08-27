#!/usr/bin/env python3
"""Safely inspect Rex-Gym policy package assets without training or GUI playback.

This helper is intentionally independent of the Rex-Gym source checkout. It
uses distribution metadata, checks package-relative config/checkpoint files,
and extracts a few scalar config fields without deserializing YAML object tags.
It never imports TensorFlow, creates an environment, starts a session, opens a
window, restores a checkpoint, downloads data, or writes files.

Examples:
  python inspect_policy_catalog.py --help
  python inspect_policy_catalog.py
  python inspect_policy_catalog.py --policy walk_ik --config-summary
"""
from __future__ import print_function

import argparse
import json
import os
import re
import sys


POLICY_CATALOG = {
    "gallop_ol": ("rex_gym/policies/gallop/ol", "model.ckpt-4000000"),
    "gallop_ik": ("rex_gym/policies/gallop/ik", "model.ckpt-2000000"),
    "walk_ik": ("rex_gym/policies/walk/ik", "model.ckpt-2000000"),
    "walk_ol": ("rex_gym/policies/walk/ol", "model.ckpt-4000000"),
    "standup_ol": ("rex_gym/policies/standup/ol", "model.ckpt-2000000"),
    "turn_ik": ("rex_gym/policies/turn/ik", "model.ckpt-2000000"),
    "turn_ol": ("rex_gym/policies/turn/ol", "model.ckpt-2000000"),
    "poses_ik": ("rex_gym/policies/poses", "model.ckpt-2000000"),
}
ENVIRONMENT_DEFAULTS = {
    "gallop": "ik",
    "walk": "ik",
    "turn": "ol",
    "standup": "ol",
    "go": "ik",
    "poses": "ik",
}
SCALAR_FIELDS = (
    "max_length", "steps", "num_agents", "eval_episodes", "update_every",
    "use_gpu", "policy_lr", "value_lr",
)


def _metadata_module():
    """Return importlib metadata with the Python 3.7-compatible fallback."""
    try:
        from importlib import metadata  # Python 3.8+
        return metadata
    except ImportError:
        try:
            import importlib_metadata as metadata  # type: ignore
            return metadata
        except ImportError:
            return None


def _distribution(metadata, requested):
    """Resolve common hyphen/underscore distribution spellings."""
    names = [requested]
    alternate = requested.replace("-", "_")
    if alternate not in names:
        names.append(alternate)
    for name in names:
        try:
            return metadata.distribution(name), name
        except Exception:
            continue
    return None, requested


def _entry_points(distribution):
    """Return console entry point names across metadata API generations."""
    try:
        points = distribution.entry_points
        if hasattr(points, "select"):
            points = points.select(group="console_scripts")
        elif isinstance(points, dict):
            points = points.get("console_scripts", ())
        return sorted(getattr(point, "name", str(point)) for point in points)
    except Exception:
        return []


def _recorded_files(distribution):
    """Return normalized distribution-record paths, or an empty list."""
    try:
        return set(str(path).replace(os.sep, "/") for path in (distribution.files or ()))
    except Exception:
        return set()


def _resource_status(distribution, recorded, relative_path):
    """Check metadata and filesystem presence without reading checkpoint bytes."""
    listed = relative_path in recorded
    present = False
    size = None
    try:
        located = distribution.locate_file(relative_path)
        present = os.path.isfile(str(located))
        if present:
            size = os.path.getsize(str(located))
    except Exception:
        # A zip or unusual installer may expose metadata without a normal file.
        present = False
    return {"path": relative_path, "listed": listed, "present": present, "bytes": size}


def _config_summary(distribution, config_path):
    """Extract harmless scalar lines; never run a YAML loader."""
    try:
        located = distribution.locate_file(config_path)
        with open(str(located), "r") as stream:
            text = stream.read(128 * 1024)
    except Exception as exc:
        return {"readable": False, "error": str(exc)}
    result = {"readable": True}
    for field in SCALAR_FIELDS:
        match = re.search(r"^\s{2}" + re.escape(field) + r":\s*(.*?)\s*$", text, re.MULTILINE)
        if match:
            result[field] = match.group(1)
    # Do not expose the config's historical absolute logdir or YAML tags.
    return result


def build_report(distribution, resolved_name, selected_policy, include_summary):
    recorded = _recorded_files(distribution)
    ids = [selected_policy] if selected_policy else sorted(POLICY_CATALOG)
    policies = {}
    for policy_id in ids:
        directory, basename = POLICY_CATALOG[policy_id]
        config = directory + "/config.yaml"
        sidecars = [
            config,
            directory + "/" + basename + ".data-00000-of-00001",
            directory + "/" + basename + ".index",
            directory + "/" + basename + ".meta",
        ]
        assets = [_resource_status(distribution, recorded, path) for path in sidecars]
        item = {
            "directory": directory,
            "checkpoint": basename,
            "assets": assets,
            "ready": all(asset["listed"] and asset["present"] for asset in assets),
        }
        if include_summary:
            item["config_summary"] = _config_summary(distribution, config)
        policies[policy_id] = item
    return {
        "distribution": resolved_name,
        "version": getattr(distribution, "version", None),
        "console_script_declared": "rex-gym" in _entry_points(distribution),
        "environment_defaults": ENVIRONMENT_DEFAULTS,
        "supported_policy_ids": sorted(POLICY_CATALOG),
        "policies": policies,
        "training_or_playback_started": False,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Inspect Rex-Gym package policy configs and checkpoint sidecars safely."
    )
    parser.add_argument(
        "--distribution", default="rex-gym",
        help="Distribution metadata name (default: rex-gym)."
    )
    parser.add_argument(
        "--policy", choices=sorted(POLICY_CATALOG),
        help="Inspect one supported policy id instead of the full catalog."
    )
    parser.add_argument(
        "--config-summary", action="store_true",
        help="Read small scalar config fields without YAML deserialization."
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Emit machine-readable JSON."
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 when any selected config/checkpoint asset is not ready."
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    metadata = _metadata_module()
    if metadata is None:
        print(
            "error: Python package metadata is unavailable; install the "
            "Python 3.7-compatible importlib-metadata helper or use a newer "
            "Python. No training or playback was started.",
            file=sys.stderr,
        )
        return 2
    distribution, resolved_name = _distribution(metadata, args.distribution)
    if distribution is None:
        print(
            "error: distribution {!r} was not found for this interpreter. "
            "Install Rex-Gym before inspecting package assets; no training or "
            "playback was started.".format(args.distribution),
            file=sys.stderr,
        )
        return 2
    report = build_report(distribution, resolved_name, args.policy, args.config_summary)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Rex-Gym distribution: {} {}".format(report["distribution"], report["version"]))
        print("Declared rex-gym console script: {}".format(report["console_script_declared"]))
        print("Supported policy ids: {}".format(", ".join(report["supported_policy_ids"])))
        for policy_id, item in report["policies"].items():
            state = "READY" if item["ready"] else "INCOMPLETE"
            print("{}: {} ({})".format(policy_id, state, item["checkpoint"]))
            for asset in item["assets"]:
                marker = "ok" if asset["listed"] and asset["present"] else "missing"
                size = "" if asset["bytes"] is None else " {} bytes".format(asset["bytes"])
                print("  [{}] {}{}".format(marker, asset["path"], size))
            if args.config_summary:
                print("  config summary: {}".format(item["config_summary"]))
        print("No training, TensorFlow session, checkpoint restore, or GUI playback was started.")
    if args.strict and not all(item["ready"] for item in report["policies"].values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
