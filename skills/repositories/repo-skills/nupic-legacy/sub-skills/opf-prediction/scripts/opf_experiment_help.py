#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Safe OPF experiment-runner helper for NuPIC legacy.

By default this script prints documented command patterns and does not run an
experiment. With --check-import or --runner-help it imports the installed NuPIC
experiment runner, without depending on the original repository checkout.
"""
from __future__ import print_function

import argparse
import inspect
import os
import sys


MISSING_RUNTIME = """\nCould not import nupic.frameworks.opf.experiment_runner. NuPIC legacy commonly\nrequires Python 2.7, the nupic package, compiled nupic.bindings, numpy\n1.12.x-era compatibility, and pycapnp/capnproto for some serialization paths.\nRun this helper from a working NuPIC legacy environment, then retry.\n"""


SUMMARY = """\
OPF experiment directory shape
------------------------------
An OPF experiment directory is a directory containing description.py. The
installed runner consumes one experiment directory plus optional flags:

  python -m nupic.frameworks.opf.experiment_runner [options] EXPERIMENT_DIR

Safe discovery commands
-----------------------
  # List task labels in description.py
  python -m nupic.frameworks.opf.experiment_runner --listTasks EXPERIMENT_DIR

  # List checkpoint labels under EXPERIMENT_DIR/savedmodels
  python -m nupic.frameworks.opf.experiment_runner --listCheckpoints EXPERIMENT_DIR

Small/test commands
-------------------
  # Run all tasks with reduced iteration counts where the experiment supports it
  python -m nupic.frameworks.opf.experiment_runner --testMode EXPERIMENT_DIR

  # Run selected tasks. The standalone dot prevents --tasks from consuming EXPERIMENT_DIR.
  python -m nupic.frameworks.opf.experiment_runner --tasks LearnTask InferTask . EXPERIMENT_DIR

Checkpoint commands
-------------------
  # Create checkpoint Initial without running tasks
  python -m nupic.frameworks.opf.experiment_runner -c Initial EXPERIMENT_DIR

  # Load checkpoint label Initial and run tasks
  python -m nupic.frameworks.opf.experiment_runner --load Initial EXPERIMENT_DIR

  # Run without checkpointing after each task
  python -m nupic.frameworks.opf.experiment_runner --noCheckpoint EXPERIMENT_DIR

Rules
-----
- Exactly one EXPERIMENT_DIR is required.
- Select only one of -c, --listCheckpoints, --listTasks, and --load.
- Do not combine -c with --noCheckpoint.
- --tasks consumes variable labels; put a standalone dot before EXPERIMENT_DIR.
- Runner checkpoints live under EXPERIMENT_DIR/savedmodels/<label>.nta/.
- For --load, pass the label only, not <label>.nta and not a filesystem path.
"""


def import_runner():
    try:
        from nupic.frameworks.opf import experiment_runner
        return experiment_runner
    except ImportError as exc:
        print(MISSING_RUNTIME, file=sys.stderr)
        print("ImportError: %s" % exc, file=sys.stderr)
        return None


def signature_text(func):
    try:
        if hasattr(inspect, "signature"):
            return str(inspect.signature(func))
    except Exception:
        pass
    try:
        return str(inspect.getargspec(func))
    except Exception:
        return "signature unavailable"


def print_summary(experiment_dir=None):
    print(SUMMARY)
    if experiment_dir:
        exp = experiment_dir
        print("Commands with your experiment directory")
        print("---------------------------------------")
        print("python -m nupic.frameworks.opf.experiment_runner --listTasks %s" % exp)
        print("python -m nupic.frameworks.opf.experiment_runner --testMode %s" % exp)
        print("python -m nupic.frameworks.opf.experiment_runner --listCheckpoints %s" % exp)
        print("python -m nupic.frameworks.opf.experiment_runner --load CHECKPOINT_LABEL %s" % exp)
        print("")
        desc = os.path.join(exp, "description.py")
        if os.path.exists(desc):
            print("Local check: found description.py")
        else:
            print("Local check: description.py not found at %s" % desc)


def check_import():
    runner = import_runner()
    if runner is None:
        return 2
    print("OK: imported nupic.frameworks.opf.experiment_runner")
    for name in ("runExperiment", "initExperimentPrng", "getCheckpointParentDir"):
        obj = getattr(runner, name, None)
        if obj is None:
            print("missing: %s" % name)
        else:
            print("%s: %s" % (name, signature_text(obj)))
    return 0


def runner_help():
    runner = import_runner()
    if runner is None:
        return 2
    try:
        # runExperiment(['--help']) reaches optparse help and exits 0 without
        # requiring an experiment directory or running model code.
        runner.runExperiment(["--help"])
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        try:
            return int(code)
        except Exception:
            return 0
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Print safe NuPIC legacy OPF experiment runner guidance.")
    parser.add_argument("--summary", action="store_true",
                        help="print self-contained command summary (default action)")
    parser.add_argument("--experiment-dir",
                        help="optional experiment dir to interpolate into command examples")
    parser.add_argument("--check-import", action="store_true",
                        help="import installed nupic.frameworks.opf.experiment_runner and print APIs")
    parser.add_argument("--runner-help", action="store_true",
                        help="delegate to installed experiment_runner --help without running an experiment")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    did = False
    status = 0
    if args.summary or not (args.check_import or args.runner_help):
        print_summary(args.experiment_dir)
        did = True
    if args.check_import:
        status = max(status, check_import())
        did = True
    if args.runner_help:
        status = max(status, runner_help())
        did = True
    if not did:
        parser.print_help()
    return status


if __name__ == "__main__":
    sys.exit(main())
