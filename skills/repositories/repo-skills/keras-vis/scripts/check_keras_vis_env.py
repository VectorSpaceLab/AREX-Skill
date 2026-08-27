#!/usr/bin/env python3
"""Cross-cutting keras-vis environment diagnostic.

The helper reports package versions, backend state, and optional image utility
availability without relying on the original repository checkout. With
`--smoke`, it also runs a tiny saliency pass on a synthetic Keras model.
"""

import argparse
import json
import random
import sys
from importlib import import_module
from importlib import util as importlib_util
from typing import Any, Dict, List, Optional

import importlib_metadata


def _module_available(name: str) -> bool:
    try:
        return importlib_util.find_spec(name) is not None
    except Exception:
        return False


def _optional_packages() -> Dict[str, bool]:
    return {
        "Pillow": _module_available("PIL"),
        "imageio": _module_available("imageio"),
    }


def _format_exc(exc: BaseException) -> str:
    return f"{exc.__class__.__name__}: {exc}"


def _import_runtime() -> Dict[str, Any]:
    import numpy as np
    import keras
    import keras.backend as K
    import tensorflow as tf
    from keras.layers import Dense, Flatten, Input
    from keras.models import Model
    from vis.visualization import visualize_saliency

    return {
        "np": np,
        "keras": keras,
        "K": K,
        "tf": tf,
        "Dense": Dense,
        "Flatten": Flatten,
        "Input": Input,
        "Model": Model,
        "visualize_saliency": visualize_saliency,
    }


def _print_import_advice(exc: BaseException) -> None:
    print(f"import error: {_format_exc(exc)}", file=sys.stderr)
    print(
        "This release expects standalone Keras 2.2.x, TensorFlow 1.15.x, and a protobuf 3.20.x pin. "
        "If the error mentions TensorFlow 1.x protobuf descriptors, downgrade protobuf to 3.20.3. "
        "Do not switch this skill to tensorflow.keras.",
        file=sys.stderr,
    )


def _tiny_smoke(runtime: Dict[str, Any], seed: int) -> Dict[str, Any]:
    np = runtime["np"]
    K = runtime["K"]
    tf = runtime["tf"]
    Dense = runtime["Dense"]
    Flatten = runtime["Flatten"]
    Input = runtime["Input"]
    Model = runtime["Model"]
    visualize_saliency = runtime["visualize_saliency"]

    old_format = K.image_data_format()
    try:
        random.seed(seed)
        np.random.seed(seed)
        keras_seed_set = False
        try:
            if hasattr(K, "set_random_seed"):
                K.set_random_seed(seed)
                keras_seed_set = True
        except Exception:
            pass
        if not keras_seed_set:
            try:
                if hasattr(tf, "set_random_seed"):
                    tf.set_random_seed(seed)
                elif hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
                    tf.compat.v1.set_random_seed(seed)
            except Exception:
                # Backend RNG support varies across legacy Keras/TensorFlow versions.
                pass

        K.set_image_data_format("channels_last")
        inp = Input((4, 4, 1))
        x = Flatten()(inp)
        x = Dense(2, activation="linear")(x)
        model = Model(inp, x)
        seed_input = np.random.RandomState(seed).rand(1, 4, 4, 1)
        grads = visualize_saliency(model, -1, 0, seed_input)
        arr = np.asarray(grads)
        return {
            "backend": K.backend(),
            "image_data_format": K.image_data_format(),
            "output_shape": list(arr.shape),
            "output_min": float(arr.min()),
            "output_max": float(arr.max()),
        }
    finally:
        K.set_image_data_format(old_format)


def _build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "packages": {},
        "optional": _optional_packages(),
        "imports": {},
        "smoke": None,
    }

    for dist_name in ("keras-vis", "Keras", "tensorflow", "protobuf"):
        try:
            report["packages"][dist_name] = importlib_metadata.version(dist_name)
        except importlib_metadata.PackageNotFoundError:
            report["packages"][dist_name] = None

    try:
        runtime = _import_runtime()
    except Exception as exc:  # pragma: no cover - environment guard
        report["imports"]["status"] = "fail"
        report["imports"]["error"] = _format_exc(exc)
        _print_import_advice(exc)
        return report

    report["imports"] = {
        "status": "pass",
        "vis_module": getattr(import_module("vis"), "__file__", None),
        "keras_version": getattr(runtime["keras"], "__version__", None),
        "tensorflow_version": getattr(runtime["tf"], "__version__", None),
        "backend": runtime["K"].backend(),
        "image_data_format": runtime["K"].image_data_format(),
    }

    if args.smoke:
        try:
            report["smoke"] = _tiny_smoke(runtime, args.seed)
        except Exception as exc:  # pragma: no cover - runtime guard
            report["smoke"] = {"status": "fail", "error": _format_exc(exc)}
            raise

    return report


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a keras-vis environment and optional smoke behavior.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--smoke", action="store_true", help="run a tiny saliency smoke check")
    parser.add_argument("--require-optional", action="store_true", help="treat Pillow and imageio as required")
    parser.add_argument("--seed", type=int, default=1337, help="random seed for the smoke check")
    return parser.parse_args(argv)


def _print_text(report: Dict[str, Any], require_optional: bool) -> None:
    print("keras-vis environment diagnostic")
    for name, version in sorted(report["packages"].items()):
        print(f"package[{name}]={version}")
    print(f"backend={report['imports'].get('backend')}")
    print(f"image_data_format={report['imports'].get('image_data_format')}")
    print(f"vis_module={report['imports'].get('vis_module')}")
    print(f"optional[Pillow]={report['optional']['Pillow']}")
    print(f"optional[imageio]={report['optional']['imageio']}")
    if require_optional and not all(report["optional"].values()):
        print("status=fail optional packages missing", file=sys.stderr)
    if report.get("smoke") is not None:
        print("smoke=" + json.dumps(report["smoke"], sort_keys=True))


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = _build_report(args)
    except Exception as exc:
        print(f"smoke error: {_format_exc(exc)}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report, args.require_optional)

    if report["imports"].get("status") != "pass":
        return 2
    if args.require_optional and not all(report["optional"].values()):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
