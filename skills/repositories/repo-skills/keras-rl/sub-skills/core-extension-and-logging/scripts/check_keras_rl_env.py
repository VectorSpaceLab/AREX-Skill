#!/usr/bin/env python3
"""Check an installed keras-rl runtime environment.

Run this inside the Python environment where future keras-rl work will run. The
script does not need the original source checkout; it imports the installed
packages and optionally performs a tiny DQN compile smoke.
"""

from __future__ import print_function

import argparse
import importlib
import json
import os
import platform
import sys
import traceback


CAVEAT = (
    "keras-rl is legacy standalone Keras 2.x code. Select a legacy Keras backend "
    "before importing Keras. Theano CPU is often a conservative compile-only "
    "choice; TensorFlow-era imports can succeed while agent construction still "
    "fails on symbolic Tensor behavior such as len(model.output). Modern "
    "tf.keras/Keras 3 stacks should be treated as incompatible until a smoke "
    "check passes."
)

MODULES = [
    "rl",
    "rl.memory",
    "rl.policy",
    "rl.processors",
    "rl.callbacks",
    "rl.agents.dqn",
    "rl.agents.ddpg",
    "rl.agents.cem",
    "rl.agents.sarsa",
    "rl.util",
]

DISTRIBUTIONS = [
    "keras-rl",
    "Keras",
    "keras",
    "tensorflow",
    "Theano",
    "theano",
    "gym",
    "h5py",
    "wandb",
    "matplotlib",
    "numpy",
]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Import-check keras-rl/Keras/backend compatibility and optionally compile a tiny DQN agent."
    )
    parser.add_argument(
        "--no-smoke",
        action="store_true",
        help="Only run version and import checks; skip the compile smoke.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report instead of text.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include full tracebacks in text output for failed imports or smoke checks.",
    )
    return parser.parse_args(argv)


def distribution_version(name):
    try:
        try:
            from importlib import metadata
        except ImportError:  # Python < 3.8
            import importlib_metadata as metadata  # type: ignore
        return metadata.version(name)
    except Exception:
        try:
            import pkg_resources
            return pkg_resources.get_distribution(name).version
        except Exception:
            return None


def module_version(module):
    return getattr(module, "__version__", None)


def try_import(module_name):
    try:
        module = importlib.import_module(module_name)
        return {
            "module": module_name,
            "ok": True,
            "version": module_version(module),
            "error": None,
            "traceback": None,
        }
    except Exception as exc:
        return {
            "module": module_name,
            "ok": False,
            "version": None,
            "error": "{}: {}".format(exc.__class__.__name__, exc),
            "traceback": traceback.format_exc(),
        }


def keras_backend_report():
    report = {
        "keras_import_ok": False,
        "keras_version": None,
        "backend": None,
        "floatx": None,
        "image_data_format": None,
        "error": None,
        "traceback": None,
    }
    try:
        import keras
        import keras.backend as K
        report["keras_import_ok"] = True
        report["keras_version"] = getattr(keras, "__version__", None)
        try:
            report["backend"] = K.backend()
        except Exception as exc:
            report["backend"] = "unknown ({})".format(exc)
        try:
            report["floatx"] = K.floatx()
        except Exception:
            pass
        try:
            if hasattr(K, "image_data_format"):
                report["image_data_format"] = K.image_data_format()
            elif hasattr(K, "image_dim_ordering"):
                report["image_data_format"] = K.image_dim_ordering()
        except Exception:
            pass
    except Exception as exc:
        report["error"] = "{}: {}".format(exc.__class__.__name__, exc)
        report["traceback"] = traceback.format_exc()
    return report


def compile_smoke():
    report = {"ok": False, "name": "dqn_compile", "error": None, "traceback": None}
    try:
        from keras.layers import Activation, Dense, Flatten
        from keras.models import Sequential
        from keras.optimizers import Adam
        from rl.agents.dqn import DQNAgent
        from rl.memory import SequentialMemory

        nb_actions = 2
        model = Sequential()
        model.add(Flatten(input_shape=(1, 4)))
        model.add(Dense(8))
        model.add(Activation("relu"))
        model.add(Dense(nb_actions))
        model.add(Activation("linear"))

        memory = SequentialMemory(limit=32, window_length=1)
        agent = DQNAgent(
            model=model,
            nb_actions=nb_actions,
            memory=memory,
            nb_steps_warmup=1,
            target_model_update=1,
        )
        try:
            optimizer = Adam(lr=0.001)
        except TypeError:
            optimizer = Adam(learning_rate=0.001)
        agent.compile(optimizer, metrics=["mae"])
        report["ok"] = True
    except Exception as exc:
        report["error"] = "{}: {}".format(exc.__class__.__name__, exc)
        report["traceback"] = traceback.format_exc()
    return report


def build_report(no_smoke=False):
    report = {
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "environment": {
            "KERAS_BACKEND": os.environ.get("KERAS_BACKEND"),
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
        "caveat": CAVEAT,
        "distributions": {},
        "keras_backend": None,
        "imports": [],
        "smoke": {"skipped": bool(no_smoke), "result": None},
        "advice": [],
        "ok": False,
    }

    for dist in DISTRIBUTIONS:
        version = distribution_version(dist)
        if version is not None:
            report["distributions"][dist] = version

    report["keras_backend"] = keras_backend_report()
    for module_name in MODULES:
        report["imports"].append(try_import(module_name))

    if not no_smoke:
        report["smoke"]["result"] = compile_smoke()

    failed_imports = [item for item in report["imports"] if not item["ok"]]
    keras_ok = bool(report["keras_backend"].get("keras_import_ok"))
    smoke_ok = True if no_smoke else bool(report["smoke"]["result"] and report["smoke"]["result"].get("ok"))

    if not keras_ok:
        report["advice"].append("Keras import failed; install standalone legacy Keras 2.x with a compatible backend.")
    if failed_imports:
        failed_names = ", ".join(item["module"] for item in failed_imports)
        report["advice"].append("Failed keras-rl imports: {}.".format(failed_names))
        if any("wandb" in (item.get("error") or "") for item in failed_imports):
            report["advice"].append(
                "rl.callbacks imports wandb at module import time; install compatible wandb even if W&B logging is not used."
            )
    if not no_smoke and not smoke_ok:
        backend = report["keras_backend"].get("backend")
        report["advice"].append(
            "Compile smoke failed under backend {!r}. If this is TensorFlow, try a legacy Theano backend before debugging model code.".format(
                backend
            )
        )
    if not report["environment"].get("KERAS_BACKEND"):
        report["advice"].append(
            "KERAS_BACKEND is not set in the environment; backend selection may depend on user config and must be set before Keras import."
        )

    report["ok"] = keras_ok and not failed_imports and smoke_ok
    return report


def print_text_report(report, include_traceback=False):
    print("keras-rl environment check")
    print("==========================")
    print("Python: {version} ({implementation})".format(**report["python"]))
    print("Platform: {}".format(report["python"].get("platform")))
    print("KERAS_BACKEND: {}".format(report["environment"].get("KERAS_BACKEND") or "<unset>"))
    print("")
    print("Compatibility caveat:")
    print("  {}".format(report["caveat"]))
    print("")

    print("Distributions:")
    if report["distributions"]:
        for name in sorted(report["distributions"]):
            print("  {name}: {version}".format(name=name, version=report["distributions"][name]))
    else:
        print("  <no known distributions detected>")
    print("")

    kb = report["keras_backend"]
    print("Keras/backend:")
    if kb.get("keras_import_ok"):
        print("  Keras import: ok")
        print("  Keras version: {}".format(kb.get("keras_version") or "<unknown>"))
        print("  Backend: {}".format(kb.get("backend") or "<unknown>"))
        if kb.get("floatx"):
            print("  floatx: {}".format(kb.get("floatx")))
        if kb.get("image_data_format"):
            print("  image data format: {}".format(kb.get("image_data_format")))
    else:
        print("  Keras import: FAILED - {}".format(kb.get("error")))
        if include_traceback and kb.get("traceback"):
            print(kb["traceback"])
    print("")

    print("Imports:")
    for item in report["imports"]:
        if item["ok"]:
            suffix = " ({})".format(item["version"]) if item.get("version") else ""
            print("  OK     {}{}".format(item["module"], suffix))
        else:
            print("  FAILED {} - {}".format(item["module"], item["error"]))
            if include_traceback and item.get("traceback"):
                print(item["traceback"])
    print("")

    print("Compile smoke:")
    if report["smoke"].get("skipped"):
        print("  skipped (--no-smoke)")
    else:
        smoke = report["smoke"].get("result") or {}
        if smoke.get("ok"):
            print("  OK tiny DQNAgent compile smoke passed")
        else:
            print("  FAILED {}".format(smoke.get("error") or "unknown error"))
            if include_traceback and smoke.get("traceback"):
                print(smoke["traceback"])
    print("")

    if report["advice"]:
        print("Advice:")
        for item in report["advice"]:
            print("  - {}".format(item))
        print("")

    print("Overall: {}".format("OK" if report["ok"] else "FAILED"))


def main(argv=None):
    args = parse_args(argv)
    report = build_report(no_smoke=args.no_smoke)
    if args.json:
        public_report = json.loads(json.dumps(report))
        if not args.traceback:
            if public_report.get("keras_backend"):
                public_report["keras_backend"].pop("traceback", None)
            for item in public_report.get("imports", []):
                item.pop("traceback", None)
            if public_report.get("smoke", {}).get("result"):
                public_report["smoke"]["result"].pop("traceback", None)
        print(json.dumps(public_report, indent=2, sort_keys=True))
    else:
        print_text_report(report, include_traceback=args.traceback)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
