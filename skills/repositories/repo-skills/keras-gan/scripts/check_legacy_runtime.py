#!/usr/bin/env python3
"""Check whether the current Python looks compatible with legacy Keras-GAN scripts.

This script imports dependency packages and builds a tiny Keras model. It does
not import Keras-GAN source files, download datasets, train models, or write
checkpoints/images.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any, Dict, List


def version_of(module_name: str, attr: str = "__version__") -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {"module": module_name, "ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
    version = getattr(module, attr, None)
    return {"module": module_name, "ok": True, "version": str(version) if version is not None else None}


def check_keras_model() -> Dict[str, Any]:
    try:
        import keras
        from keras.layers import Dense, Input
        from keras.models import Model

        x = Input(shape=(2,))
        y = Dense(1)(x)
        model = Model(x, y)
        backend = keras.backend.backend()
        return {"ok": True, "backend": backend, "output_shape": str(model.output_shape)}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def check_keras_contrib() -> Dict[str, Any]:
    try:
        from keras_contrib.layers.normalization.instancenormalization import InstanceNormalization  # noqa: F401
        return {"ok": True, "symbol": "keras_contrib.layers.normalization.instancenormalization.InstanceNormalization"}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def version_tuple(text: str) -> List[int]:
    parts: List[int] = []
    for piece in text.replace("-", ".").split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            digits = "".join(ch for ch in piece if ch.isdigit())
            if digits:
                parts.append(int(digits))
            break
    return parts


def add_version_advice(results: Dict[str, Any]) -> None:
    advice: List[str] = []
    by_module = {item["module"]: item for item in results["packages"]}

    keras = by_module.get("keras", {})
    if keras.get("ok") and keras.get("version"):
        if version_tuple(keras["version"]) >= [3]:
            advice.append("Keras 3+ is not source-compatible with these scripts; use legacy Keras 2.2.x or port deliberately.")
    tf = by_module.get("tensorflow", {})
    if tf.get("ok") and tf.get("version"):
        if version_tuple(tf["version"]) >= [2]:
            advice.append("TensorFlow 2.x changes graph/session behavior; faithful execution expects TensorFlow 1.15.x.")
    scipy = by_module.get("scipy", {})
    if scipy.get("ok") and scipy.get("version"):
        if version_tuple(scipy["version"]) >= [1, 3]:
            advice.append("SciPy 1.3+ removed scipy.misc.imread/imresize used by several loaders; use SciPy 1.2.x or port image I/O.")
    protobuf = by_module.get("google.protobuf", {})
    if protobuf.get("ok") and protobuf.get("version"):
        if version_tuple(protobuf["version"]) >= [3, 21]:
            advice.append("protobuf 3.21+ commonly breaks TensorFlow 1.x imports; pin protobuf<3.21 for legacy execution.")
    if not results["kerasContrib"].get("ok"):
        advice.append("keras-contrib InstanceNormalization is missing; CycleGAN/DiscoGAN/CCGAN/PixelDA/SRGAN imports may fail.")
    results["advice"] = advice


def collect() -> Dict[str, Any]:
    packages = [
        version_of("tensorflow"),
        version_of("keras"),
        version_of("numpy"),
        version_of("scipy"),
        version_of("matplotlib"),
        version_of("PIL", "__version__"),
        version_of("skimage"),
        version_of("h5py"),
        version_of("google.protobuf"),
    ]
    results: Dict[str, Any] = {
        "schemaVersion": 1,
        "python": sys.version.replace("\n", " "),
        "packages": packages,
        "kerasContrib": check_keras_contrib(),
        "tinyKerasModel": check_keras_model(),
    }
    add_version_advice(results)
    results["ok"] = all(item.get("ok") for item in packages[:5]) and results["tinyKerasModel"].get("ok") and results["kerasContrib"].get("ok")
    return results


def render_text(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("Keras-GAN legacy runtime check")
    lines.append(f"status: {'OK' if results['ok'] else 'CHECK WARNINGS'}")
    lines.append(f"python: {results['python']}")
    lines.append("packages:")
    for item in results["packages"]:
        if item.get("ok"):
            lines.append(f"  - {item['module']}: {item.get('version') or 'version unknown'}")
        else:
            lines.append(f"  - {item['module']}: MISSING/ERROR ({item.get('error')})")
    kc = results["kerasContrib"]
    lines.append(f"keras-contrib InstanceNormalization: {'OK' if kc.get('ok') else 'FAIL'}")
    if not kc.get("ok"):
        lines.append(f"  error: {kc.get('error')}")
    km = results["tinyKerasModel"]
    lines.append(f"tiny Keras model: {'OK' if km.get('ok') else 'FAIL'}")
    if km.get("ok"):
        lines.append(f"  backend: {km.get('backend')} output_shape: {km.get('output_shape')}")
    else:
        lines.append(f"  error: {km.get('error')}")
    if results.get("advice"):
        lines.append("advice:")
        lines.extend(f"  - {msg}" for msg in results["advice"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check current Python compatibility with legacy Keras-GAN scripts.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    results = collect()
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(render_text(results))
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
