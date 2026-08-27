#!/usr/bin/env python3
"""Read-only DLTK/TensorFlow 1.x compatibility diagnostic.

This reports versions and public symbol availability without printing module
installation paths, touching datasets, creating files, or contacting a
network. Run it from any working directory.
"""
from __future__ import print_function

import argparse
import json
import os
import sys


def collect():
    result = {
        "python": "%d.%d.%d" % sys.version_info[:3],
        "tensorflow": None,
        "dltk": None,
        "tensorflow_1x_symbols": {},
        "imports": {},
        "optional_imports": {},
    }
    try:
        import tensorflow as tf
    except Exception as exc:  # Import diagnostics should remain readable.
        result["tensorflow_error"] = "%s: %s" % (type(exc).__name__, exc)
        return result

    result["tensorflow"] = str(tf.__version__)
    for name in ("Session", "layers", "contrib", "estimator"):
        result["tensorflow_1x_symbols"][name] = hasattr(tf, name)

    try:
        import dltk
        from dltk.version import __version__
        result["dltk"] = str(__version__)
    except Exception as exc:
        result["dltk_error"] = "%s: %s" % (type(exc).__name__, exc)
        return result

    modules = (
        "dltk.core.activations",
        "dltk.core.losses",
        "dltk.core.metrics",
        "dltk.core.residual_unit",
        "dltk.core.upsample",
        "dltk.io.abstract_reader",
        "dltk.io.augmentation",
        "dltk.io.preprocessing",
        "dltk.networks.regression_classification.resnet",
        "dltk.networks.segmentation.unet",
        "dltk.networks.segmentation.fcn",
        "dltk.networks.autoencoder.convolutional_autoencoder",
        "dltk.networks.gan.dcgan",
        "dltk.networks.super_resolution.simple_super_resolution",
        "dltk.utils",
    )
    for module_name in modules:
        try:
            __import__(module_name)
            result["imports"][module_name] = "ok"
        except Exception as exc:
            result["imports"][module_name] = "%s: %s" % (
                type(exc).__name__, exc)

    for module_name in ("SimpleITK", "pandas"):
        try:
            __import__(module_name)
            result["optional_imports"][module_name] = "ok"
        except Exception as exc:
            result["optional_imports"][module_name] = "%s: %s" % (
                type(exc).__name__, exc)
    return result


def valid(result):
    return (
        result.get("tensorflow", "").startswith("1.")
        and all(result["tensorflow_1x_symbols"].values())
        and result.get("dltk") == "0.2.1"
        and all(value == "ok" for value in result.get("imports", {}).values())
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check DLTK 0.2.1 and TensorFlow 1.x public APIs without data I/O.")
    parser.add_argument("--json", action="store_true", help="emit JSON diagnostics")
    args = parser.parse_args(argv)

    # Avoid accidental historical GPU initialization during this diagnostic.
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    result = collect()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("python=%s" % result["python"])
        print("tensorflow=%s" % (result["tensorflow"] or "unavailable"))
        print("dltk=%s" % (result["dltk"] or "unavailable"))
        symbols = result.get("tensorflow_1x_symbols", {})
        print("tf1_symbols=%s" % ",".join(
            name for name, present in symbols.items() if present))
        failed = [name for name, value in result.get("imports", {}).items()
                  if value != "ok"]
        print("module_imports=%s" % ("PASS" if not failed else "FAIL"))
        if failed:
            print("failed_modules=%s" % ",".join(failed))
        optional = result.get("optional_imports", {})
        print("optional_imports=%s" % ",".join(
            "%s:%s" % (name, value) for name, value in optional.items()))

    if not valid(result):
        print("compatibility gate: FAIL", file=sys.stderr)
        return 1
    print("compatibility gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
