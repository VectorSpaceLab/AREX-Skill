#!/usr/bin/env python3
"""Import or optionally construct selected Keras-GAN MNIST generator classes.

Default behavior is import-only. The script never calls train(...), never
loads datasets intentionally, and never writes images or checkpoints.
"""
from __future__ import print_function

import argparse
import importlib.util
import os
import sys
import traceback

MODELS = {
    "gan": ("gan/gan.py", "GAN"),
    "dcgan": ("dcgan/dcgan.py", "DCGAN"),
    "cgan": ("cgan/cgan.py", "CGAN"),
    "acgan": ("acgan/acgan.py", "ACGAN"),
    "wgan": ("wgan/wgan.py", "WGAN"),
    "wgan-gp": ("wgan_gp/wgan_gp.py", "WGANGP"),
}

LEGACY_HINT = """\
Legacy dependency hint:
  These source files target the Keras 2.2 / TensorFlow 1.x era. A compatible
  runtime family is Python 3.7, TensorFlow 1.15.x, Keras 2.2.x, NumPy 1.18.x,
  SciPy 1.2.x, h5py<3, and protobuf<3.21. Do not diagnose failures by installing
  latest standalone Keras unless you are intentionally porting the code.
  WGAN-GP additionally imports the private legacy API keras.layers.merge._Merge.
"""


def load_module(module_name, script_path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not build import spec for %s" % script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize_instance(obj):
    names = ["img_shape", "img_dim", "latent_dim", "num_classes", "n_critic", "clip_value"]
    facts = []
    for name in names:
        if hasattr(obj, name):
            try:
                facts.append("%s=%r" % (name, getattr(obj, name)))
            except Exception:
                facts.append("%s=<unreadable>" % name)
    return ", ".join(facts) if facts else "no standard summary attributes found"


def print_dependency_error(exc, phase, model_name):
    print("%s FAILED for model '%s': %s: %s" % (phase, model_name, exc.__class__.__name__, exc))
    print(LEGACY_HINT)
    if model_name == "wgan-gp":
        print("WGAN-GP-specific hint: if the message mentions _Merge or keras.layers.merge, use a legacy Keras 2.2 runtime or port RandomWeightedAverage to a supported custom Layer/Lambda.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Safely import or optionally construct selected Keras-GAN MNIST generator models.")
    parser.add_argument("--repo-root", required=True, help="Path to a Keras-GAN checkout.")
    parser.add_argument("--model", required=True, choices=sorted(MODELS), help="Model script to import: %(choices)s.")
    parser.add_argument("--construct", action="store_true", help="Instantiate the selected class after import. Default is import-only.")
    parser.add_argument("--verbose", action="store_true", help="Print traceback on unexpected failures.")
    args = parser.parse_args(argv)

    os.environ.setdefault("MPLBACKEND", "Agg")

    repo_root = os.path.abspath(args.repo_root)
    rel_path, class_name = MODELS[args.model]
    script_path = os.path.join(repo_root, rel_path)
    if not os.path.isfile(script_path):
        print("ERROR: source file not found: %s" % script_path)
        return 1

    # Allow standalone scripts to resolve any local imports while keeping import by path explicit.
    sys.path.insert(0, os.path.dirname(script_path))
    sys.path.insert(0, repo_root)
    module_name = "keras_gan_dryrun_" + args.model.replace("-", "_")

    try:
        module = load_module(module_name, script_path)
    except ImportError as exc:
        print_dependency_error(exc, "IMPORT", args.model)
        if args.verbose:
            traceback.print_exc()
        return 2
    except Exception as exc:
        print("IMPORT FAILED for model '%s': %s: %s" % (args.model, exc.__class__.__name__, exc))
        print(LEGACY_HINT)
        if args.verbose:
            traceback.print_exc()
        return 2

    print("IMPORT OK: %s (%s)" % (rel_path, class_name))

    if not hasattr(module, class_name):
        print("ERROR: class %s was not found in %s" % (class_name, rel_path))
        return 1

    if not args.construct:
        print("Construct skipped. Re-run with --construct to instantiate; train(...) is never called by this helper.")
        return 0

    cls = getattr(module, class_name)
    try:
        instance = cls()
    except ImportError as exc:
        print_dependency_error(exc, "CONSTRUCT", args.model)
        if args.verbose:
            traceback.print_exc()
        return 3
    except Exception as exc:
        print("CONSTRUCT FAILED for model '%s': %s: %s" % (args.model, exc.__class__.__name__, exc))
        print(LEGACY_HINT)
        if args.model == "wgan-gp":
            print("WGAN-GP-specific hint: constructor failures often indicate legacy _Merge, graph-gradient, or fixed-batch interpolation incompatibility.")
        if args.verbose:
            traceback.print_exc()
        return 3

    print("CONSTRUCT OK: %s; %s" % (class_name, summarize_instance(instance)))
    print("No train(...) call was executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
