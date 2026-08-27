#!/usr/bin/env python3
"""Safe Parametric UMAP dependency and tiny-smoke checker.

By default this script performs import and metadata checks only. It does not
train, download data, contact the network, or write persistent files. Pass
--tiny-smoke explicitly to run a very small local ParametricUMAP fit when
TensorFlow/Keras are available.
"""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import json
import os
import subprocess
import sys
import textwrap
from typing import Any

# Keep TensorFlow logs quieter when TensorFlow is present; users can override.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def _run_probe(code: str, timeout: int = 45) -> dict[str, Any]:
    """Run a child Python probe and capture JSON or the failure summary."""
    env = os.environ.copy()
    env.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )
    result: dict[str, Any] = {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    try:
        result["data"] = json.loads(proc.stdout)
    except Exception:
        result["data"] = None
    return result


def _probe_json(code: str, label: str, timeout: int = 45) -> dict[str, Any]:
    """Parse a probe result, falling back to a crash summary when needed."""
    proc = _run_probe(code, timeout=timeout)
    data = proc.get("data")
    if isinstance(data, dict):
        return data
    stderr_tail = "\n".join(proc.get("stderr", "").splitlines()[-12:])
    stdout_tail = "\n".join(proc.get("stdout", "").splitlines()[-12:])
    return {
        "module": label,
        "available": False,
        "error_type": "SubprocessCrash" if proc.get("returncode", 1) != 0 else "ProbeParseError",
        "error": stderr_tail or stdout_tail or "probe produced no JSON output",
        "returncode": proc.get("returncode"),
    }


def _distribution_version(name: str) -> dict[str, Any]:
    try:
        return {"name": name, "available": True, "version": importlib_metadata.version(name)}
    except importlib_metadata.PackageNotFoundError:
        return {"name": name, "available": False, "error": "distribution not found"}
    except Exception as exc:
        return {
            "name": name,
            "available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def _status_text(item: dict[str, Any]) -> str:
    if item.get("available"):
        version = item.get("version")
        return f"ok ({version})" if version else "ok"
    err = item.get("error") or item.get("error_type") or "missing"
    return f"missing/error: {err}"


def _module_probe_code(module_name: str, attr: str | None = None) -> str:
    attr_literal = repr(attr)
    return textwrap.dedent(
        f"""
        import importlib
        import inspect
        import json
        import warnings

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            data = {{"module": {module_name!r}, "available": False}}
            try:
                module = importlib.import_module({module_name!r})
                data["available"] = True
                data["version"] = getattr(module, "__version__", None)
                if {attr_literal} is not None:
                    data["has_attr"] = hasattr(module, {attr_literal})
                    if data["has_attr"]:
                        try:
                            data["signature"] = str(inspect.signature(getattr(module, {attr_literal})))
                        except Exception as exc:
                            data["signature_error_type"] = type(exc).__name__
                            data["signature_error"] = str(exc)
            except Exception as exc:
                data["error_type"] = type(exc).__name__
                data["error"] = str(exc)
            if captured:
                data["warnings"] = [str(item.message) for item in captured]
        print(json.dumps(data))
        """
    )


def probe_module(module_name: str, attr: str | None = None, timeout: int = 30) -> dict[str, Any]:
    """Probe a module import and optional attribute signature in a subprocess."""
    return _probe_json(_module_probe_code(module_name, attr=attr), module_name, timeout=timeout)


def probe_root_parametric(timeout: int = 45) -> dict[str, Any]:
    """Inspect root import behavior and the dummy-class fallback when present."""
    code = textwrap.dedent(
        """
        import inspect
        import json
        import warnings

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            data = {"import": "from umap import ParametricUMAP", "available": False}
            try:
                from umap import ParametricUMAP

                data["available"] = True
                data["class_module"] = getattr(ParametricUMAP, "__module__", None)
                data["class_name"] = getattr(ParametricUMAP, "__name__", None)
                data["constructor_signature"] = str(inspect.signature(ParametricUMAP))
                data["is_probable_dummy"] = data["class_module"] == "umap"
                try:
                    ParametricUMAP()
                    data["constructor_ok"] = True
                except Exception as exc:
                    data["constructor_ok"] = False
                    data["constructor_error_type"] = type(exc).__name__
                    data["constructor_error"] = str(exc)
            except Exception as exc:
                data["error_type"] = type(exc).__name__
                data["error"] = str(exc)
            if captured:
                data["warnings"] = [str(item.message) for item in captured]
        print(json.dumps(data))
        """
    )
    result = _probe_json(code, "umap-root-parametric", timeout=timeout)
    if result.get("available") and (result.get("is_probable_dummy") or result.get("constructor_error_type") == "ImportError"):
        result["explanation"] = (
            "The root umap package can expose a dummy ParametricUMAP when TensorFlow/Keras are absent. "
            "Install the parametric extra and confirm direct import from umap.parametric_umap before training."
        )
    if not result.get("available") and result.get("error_type") == "SubprocessCrash":
        result["explanation"] = (
            "Importing the root ParametricUMAP path crashed in a child process, which usually means the "
            "TensorFlow/Keras stack is missing or unstable. Use the stack checker after repairing the optional stack."
        )
    return result


def probe_direct_parametric(timeout: int = 45) -> dict[str, Any]:
    """Import the real parametric module and collect public signatures."""
    code = textwrap.dedent(
        """
        import inspect
        import json
        import warnings

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            data = {"import": "umap.parametric_umap", "available": False}
            try:
                import umap.parametric_umap as module

                cls = getattr(module, "ParametricUMAP")
                data["available"] = True
                data["class_module"] = getattr(cls, "__module__", None)
                data["constructor_signature"] = str(inspect.signature(cls))
                methods = {}
                for name in [
                    "fit",
                    "fit_transform",
                    "transform",
                    "inverse_transform",
                    "save",
                    "add_landmarks",
                    "remove_landmarks",
                    "to_ONNX",
                ]:
                    if hasattr(cls, name):
                        methods[name] = str(inspect.signature(getattr(cls, name)))
                data["method_signatures"] = methods
                load_fn = getattr(module, "load_ParametricUMAP", None)
                data["load_ParametricUMAP_signature"] = str(inspect.signature(load_fn)) if load_fn else None
                data["torch_imported_flag"] = getattr(module, "torch_imported", None)
            except Exception as exc:
                data["error_type"] = type(exc).__name__
                data["error"] = str(exc)
            if captured:
                data["warnings"] = [str(item.message) for item in captured]
        print(json.dumps(data))
        """
    )
    result = _probe_json(code, "umap.parametric_umap", timeout=timeout)
    if not result.get("available"):
        result["explanation"] = (
            "Direct umap.parametric_umap import requires TensorFlow and Keras. Use pip install 'umap-learn[parametric_umap]' "
            "in the active environment and confirm the import again."
        )
    return result


def probe_onnx_stack(timeout: int = 30) -> dict[str, Any]:
    """Probe optional Torch and torchvision imports used by the ONNX export path."""
    code = textwrap.dedent(
        """
        import importlib
        import json

        modules = {}
        for name in ["torch", "torch.onnx", "torchvision"]:
            item = {"available": False}
            try:
                module = importlib.import_module(name)
                item["available"] = True
                item["version"] = getattr(module, "__version__", None)
            except Exception as exc:
                item["error_type"] = type(exc).__name__
                item["error"] = str(exc)
            modules[name] = item
        print(json.dumps({"modules": modules}))
        """
    )
    result = _probe_json(code, "onnx-stack", timeout=timeout)
    modules = result.get("modules", {}) if isinstance(result, dict) else {}
    return {
        "available": bool(
            modules.get("torch", {}).get("available")
            and modules.get("torch.onnx", {}).get("available")
            and modules.get("torchvision", {}).get("available")
        ),
        "torch": modules.get("torch", {"available": False, "error": "probe missing"}),
        "torch_onnx": modules.get("torch.onnx", {"available": False, "error": "probe missing"}),
        "torchvision": modules.get("torchvision", {"available": False, "error": "probe missing"}),
        "explanation": (
            "ONNX export through ParametricUMAP.to_ONNX is optional, imports Torch and torchvision, and is intended for "
            "the default dense encoder path rather than arbitrary custom networks."
        ),
    }


def probe_tiny_smoke(timeout: int = 180) -> dict[str, Any]:
    """Run a tiny local fit only when optional neural dependencies are present."""
    code = textwrap.dedent(
        """
        import json
        import warnings

        import numpy as np

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            data = {"requested": True, "ran": False}
            try:
                from umap.parametric_umap import ParametricUMAP

                theta = np.linspace(0.0, np.pi, 32, dtype="float32")
                arc_a = np.stack([np.cos(theta), np.sin(theta)], axis=1)
                arc_b = np.stack([1.0 - np.cos(theta), 0.5 - np.sin(theta)], axis=1)
                X = np.concatenate([arc_a, arc_b], axis=0).astype("float32")

                model = ParametricUMAP(
                    n_components=2,
                    n_neighbors=5,
                    n_epochs=3,
                    batch_size=8,
                    random_state=42,
                    verbose=False,
                )
                # These are attributes in umap-learn 0.5.12, not verified constructor args.
                model.loss_report_frequency = 1
                model.n_training_epochs = 1

                embedding = model.fit_transform(X)
                transformed = model.transform(X[:4], batch_size=4)
                data.update(
                    {
                        "ran": True,
                        "embedding_shape": list(getattr(embedding, "shape", ())),
                        "transform_shape": list(getattr(transformed, "shape", ())),
                        "embedding_finite": bool(np.isfinite(embedding).all()),
                        "transform_finite": bool(np.isfinite(transformed).all()),
                        "history_keys": sorted(getattr(model, "_history", {}).keys()),
                    }
                )
            except Exception as exc:
                data.update(
                    {
                        "ran": False,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
            if captured:
                data["warnings"] = [str(item.message) for item in captured]
        print(json.dumps(data))
        """
    )
    result = _probe_json(code, "parametric-tiny-smoke", timeout=timeout)
    if not result.get("ran") and not result.get("error"):
        result["error"] = "Tiny smoke did not run or did not produce a report."
    return result


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    tensorflow = probe_module("tensorflow", timeout=30)
    keras = probe_module("keras", timeout=30)
    keras_ops = probe_module("keras.ops", timeout=30)
    report: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "executable_basename": os.path.basename(sys.executable),
        },
        "distributions": {"umap-learn": _distribution_version("umap-learn")},
        "umap_import": probe_module("umap", timeout=30),
        "tensorflow": tensorflow,
        "keras": keras,
        "keras_ops": keras_ops,
        "root_parametric_import": probe_root_parametric(timeout=45),
        "direct_parametric_import": probe_direct_parametric(timeout=45),
        "onnx_stack": probe_onnx_stack(timeout=30),
        "notes": [
            "Base umap-learn works without TensorFlow; ParametricUMAP is optional.",
            "CPU TensorFlow can validate correctness, but neural training may be slow.",
            "This script performs no training unless --tiny-smoke is passed.",
        ],
    }
    if args.tiny_smoke:
        deps_ok = bool(
            tensorflow.get("available")
            and keras.get("available")
            and keras_ops.get("available")
            and report["direct_parametric_import"].get("available")
        )
        if deps_ok:
            report["tiny_smoke"] = probe_tiny_smoke(timeout=180)
        else:
            report["tiny_smoke"] = {
                "requested": True,
                "ran": False,
                "reason": "TensorFlow, Keras, and direct umap.parametric_umap import must succeed before running the tiny smoke.",
            }
    else:
        report["tiny_smoke"] = {"requested": False, "ran": False}
    return report


def print_text(report: dict[str, Any]) -> None:
    print("Parametric UMAP stack check")
    print(f"Python: {report['python']['version']}")
    print(f"umap-learn distribution: {_status_text(report['distributions']['umap-learn'])}")
    print(f"umap import: {_status_text(report['umap_import'])}")
    print(f"TensorFlow: {_status_text(report['tensorflow'])}")
    print(f"Keras: {_status_text(report['keras'])}")
    print(f"Keras ops: {_status_text(report['keras_ops'])}")

    root = report["root_parametric_import"]
    print("\nRoot ParametricUMAP import:")
    print(f"  available: {root.get('available')}")
    print(f"  class module: {root.get('class_module')}")
    print(f"  probable dummy: {root.get('is_probable_dummy')}")
    print(f"  constructor ok: {root.get('constructor_ok')}")
    if root.get("constructor_error"):
        print(f"  constructor error: {root.get('constructor_error')}")
    if root.get("explanation"):
        print(f"  note: {root.get('explanation')}")

    direct = report["direct_parametric_import"]
    print("\nDirect umap.parametric_umap import:")
    print(f"  available: {direct.get('available')}")
    if direct.get("constructor_signature"):
        print(f"  signature: {direct.get('constructor_signature')}")
    if direct.get("error"):
        print(f"  error: {direct.get('error')}")
    if direct.get("explanation"):
        print(f"  note: {direct.get('explanation')}")

    onnx = report["onnx_stack"]
    print("\nOptional ONNX export stack:")
    print(f"  available: {onnx.get('available')}")
    print(f"  torch: {_status_text(onnx['torch'])}")
    print(f"  torch.onnx: {_status_text(onnx['torch_onnx'])}")
    print(f"  torchvision: {_status_text(onnx['torchvision'])}")
    print(f"  note: {onnx.get('explanation')}")

    smoke = report["tiny_smoke"]
    print("\nTiny smoke:")
    print(f"  requested: {smoke.get('requested')}")
    print(f"  ran: {smoke.get('ran')}")
    if smoke.get("ran"):
        print(f"  embedding shape: {smoke.get('embedding_shape')}")
        print(f"  transform shape: {smoke.get('transform_shape')}")
        print(f"  finite: embedding={smoke.get('embedding_finite')} transform={smoke.get('transform_finite')}")
    elif smoke.get("reason"):
        print(f"  reason: {smoke.get('reason')}")
    elif smoke.get("error"):
        print(f"  error: {smoke.get('error')}")

    print(
        "\nInstall hint: pip install 'umap-learn[parametric_umap]' for ParametricUMAP; install torch/torchvision only when to_ONNX is required."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check optional TensorFlow/Keras ParametricUMAP dependencies and root dummy-class behavior. "
            "No training runs unless --tiny-smoke is explicitly requested."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument(
        "--tiny-smoke",
        action="store_true",
        help="If TensorFlow/Keras are available, run a tiny local fit/transform smoke test. No downloads.",
    )
    parser.add_argument(
        "--check-onnx",
        action="store_true",
        help="Accepted for clarity; Torch/torchvision ONNX readiness is reported by default.",
    )
    parser.add_argument(
        "--require-parametric",
        action="store_true",
        help="Exit non-zero if direct ParametricUMAP import is unavailable or the tiny smoke fails when requested.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.require_parametric:
        direct_ok = bool(report["direct_parametric_import"].get("available"))
        smoke = report.get("tiny_smoke", {})
        smoke_ok = (not args.tiny_smoke) or bool(
            smoke.get("ran") and smoke.get("embedding_finite") and smoke.get("transform_finite")
        )
        if not (direct_ok and smoke_ok):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
