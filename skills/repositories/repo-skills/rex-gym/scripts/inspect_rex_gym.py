#!/usr/bin/env python3
"""Inspect an installed Rex-Gym package without training or opening PyBullet GUI.

Examples:
  python scripts/inspect_rex_gym.py
  python scripts/inspect_rex_gym.py --ppo
  python scripts/inspect_rex_gym.py --strict

The default checks distribution metadata, core imports, CLI commands, environment
and policy mappings, and deterministic kinematics. ``--ppo`` additionally imports
the legacy TensorFlow/TFP surface. The script performs no network, checkpoint
restore, training, file writes, or GUI construction.
"""
from __future__ import print_function

import argparse
import contextlib
import ctypes
import json
import os
import sys
import tempfile


def metadata_module():
    try:
        from importlib import metadata
        return metadata
    except ImportError:
        try:
            import importlib_metadata as metadata
            return metadata
        except ImportError:
            return None


def version_of(metadata, *names):
    if metadata is None:
        return None
    for name in names:
        try:
            return metadata.version(name)
        except Exception:
            pass
    return None


def check_import(name, versions, report):
    try:
        module = __import__(name)
        report["imports"][name] = {
            "ok": True,
            "version": getattr(module, "__version__", None),
        }
        return module
    except Exception as exc:
        report["imports"][name] = {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
        report["ok"] = False
        return None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ppo", action="store_true",
        help="also import TensorFlow 1.x and TensorFlow Probability")
    parser.add_argument(
        "--strict", action="store_true",
        help="exit nonzero when any requested check fails")
    parser.add_argument(
        "--pretty", action="store_true",
        help="pretty-print JSON instead of one compact line")
    return parser.parse_args(argv)


@contextlib.contextmanager
def redirect_native_output():
    """Capture C-level Bullet/TensorFlow startup chatter."""
    sys.stdout.flush()
    sys.stderr.flush()
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        # Use the same descriptor for both streams; diagnostics are not part of
        # the machine-readable report emitted by this helper.
        sink = tempfile.TemporaryFile(mode="w+b")
        try:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            yield
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            try:
                ctypes.CDLL(None).fflush(None)
            except Exception:
                pass
            os.dup2(stdout_fd, 1)
            os.dup2(stderr_fd, 2)
            sink.close()
    finally:
        os.close(stdout_fd)
        os.close(stderr_fd)


def run(args):
    metadata = metadata_module()
    report = {
        "ok": True,
        "distribution": {
            "name": "rex_gym",
            "version": version_of(metadata, "rex-gym", "rex_gym"),
        },
        "imports": {},
        "versions": {},
        "cli": {},
        "mappings": {},
        "kinematics": {},
        "ppo_requested": bool(args.ppo),
        "side_effects_started": False,
    }

    for module_name in ("rex_gym", "numpy", "gym", "pybullet", "click"):
        check_import(module_name, metadata, report)
    report["versions"] = {
        name: version_of(metadata, name)
        for name in ("numpy", "gym", "pybullet", "click", "protobuf", "cloudpickle")
    }

    try:
        from click.testing import CliRunner
        from rex_gym.cli.entry_point import cli
        result = CliRunner().invoke(cli, ["--help"])
        report["cli"] = {
            "ok": result.exit_code == 0,
            "commands": [name for name in ("policy", "train") if name in result.output],
        }
        if result.exit_code != 0:
            report["ok"] = False
            report["cli"]["error"] = result.output
    except Exception as exc:
        report["ok"] = False
        report["cli"] = {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }

    try:
        from rex_gym.util import flag_mapper
        report["mappings"] = {
            "environments": dict(flag_mapper.ENV_ID_TO_ENV_NAMES),
            "defaults": dict(flag_mapper.DEFAULT_SIGNAL),
            "terrains": dict(flag_mapper.TERRAIN_TYPE),
            "policy_ids": sorted(flag_mapper.ENV_ID_TO_POLICY),
        }
    except Exception as exc:
        report["ok"] = False
        report["mappings"] = {"error_type": exc.__class__.__name__, "error": str(exc)}

    try:
        import numpy as np
        from rex_gym.model.kinematics import Kinematics
        result = Kinematics().solve(np.zeros(3), np.zeros(3))
        report["kinematics"] = {
            "ok": len(result) == 5,
            "leg_angle_shapes": [list(np.asarray(item).shape) for item in result[:4]],
            "frame_shape": list(np.asarray(result[4]).shape),
            "finite": all(bool(np.isfinite(np.asarray(item)).all()) for item in result),
        }
        if not report["kinematics"]["ok"] or not report["kinematics"]["finite"]:
            report["ok"] = False
    except Exception as exc:
        report["ok"] = False
        report["kinematics"] = {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }

    if args.ppo:
        check_import("tensorflow", metadata, report)
        check_import("tensorflow_probability", metadata, report)
        report["versions"]["tensorflow"] = version_of(metadata, "tensorflow")
        report["versions"]["tensorflow_probability"] = version_of(
            metadata, "tensorflow-probability")

    if report["distribution"]["version"] is None:
        report["ok"] = False
        report["distribution"]["error"] = "Rex-Gym distribution metadata not found"
    return report


def main(argv=None):
    args = parse_args(argv)
    with redirect_native_output():
        report = run(args)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if args.strict and not report["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
