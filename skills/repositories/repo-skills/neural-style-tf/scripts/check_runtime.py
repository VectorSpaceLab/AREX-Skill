#!/usr/bin/env python3
"""Check a candidate neural-style-tf runtime without running a render.

Run this with the Python environment that would execute neural_style.py. The
script checks legacy TensorFlow v1 symbols, OpenCV/SciPy/NumPy imports, optional
VGG weights, optional ffmpeg/ffprobe, and optional TensorFlow GPU visibility.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence


def module_version(name: str) -> Dict[str, object]:
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_tensorflow(check_gpu: bool) -> Dict[str, object]:
    result = module_version("tensorflow")
    if not result.get("ok"):
        return result
    import tensorflow as tf  # type: ignore

    result.update(
        {
            "hasSession": hasattr(tf, "Session"),
            "hasContribOptScipy": bool(
                hasattr(tf, "contrib")
                and hasattr(tf.contrib, "opt")
                and hasattr(tf.contrib.opt, "ScipyOptimizerInterface")
            ),
        }
    )
    if check_gpu:
        try:
            result["gpuDevices"] = [dev.name for dev in tf.config.list_physical_devices("GPU")]
        except Exception:
            try:
                from tensorflow.python.client import device_lib  # type: ignore

                result["gpuDevices"] = [d.name for d in device_lib.list_local_devices() if d.device_type == "GPU"]
            except Exception as exc:  # noqa: BLE001
                result["gpuError"] = f"{type(exc).__name__}: {exc}"
    return result


def run_script_help(script: Path, timeout: int) -> Dict[str, object]:
    if not script.exists():
        return {"ok": False, "error": f"script not found: {script}"}
    if not script.is_file():
        return {"ok": False, "error": f"script is not a file: {script}"}
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": proc.returncode == 0 and "--style_imgs" in proc.stdout,
        "returncode": proc.returncode,
        "stdoutContainsStyleImgs": "--style_imgs" in proc.stdout,
        "stderrTail": proc.stderr[-500:],
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check neural-style-tf runtime prerequisites without rendering.")
    parser.add_argument("--script", default="neural_style.py", help="Path to neural_style.py. Default: %(default)s")
    parser.add_argument("--model-weights", default=None, help="Optional VGG-19 .mat file path to check for existence.")
    parser.add_argument("--check-ffmpeg", action="store_true", help="Check ffmpeg and ffprobe executables for video planning.")
    parser.add_argument("--check-gpu", action="store_true", help="Check TensorFlow GPU visibility. Does not allocate large tensors.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for script --help check. Default: %(default)s seconds")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report: Dict[str, object] = {
        "pythonVersion": sys.version.split()[0],
        "modules": {
            "tensorflow": check_tensorflow(args.check_gpu),
            "cv2": module_version("cv2"),
            "scipy": module_version("scipy"),
            "numpy": module_version("numpy"),
        },
        "scriptHelp": run_script_help(Path(args.script).expanduser(), args.timeout),
        "modelWeights": None,
        "executables": {},
    }

    if args.model_weights:
        p = Path(args.model_weights).expanduser()
        report["modelWeights"] = {"pathProvided": True, "exists": p.is_file(), "suffix": p.suffix}
    else:
        report["modelWeights"] = {"pathProvided": False, "exists": None}

    if args.check_ffmpeg:
        report["executables"] = {"ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "avconv": shutil.which("avconv")}

    tf_info = report["modules"]["tensorflow"]  # type: ignore[index]
    required_ok = bool(
        isinstance(tf_info, dict)
        and tf_info.get("ok")
        and tf_info.get("hasSession")
        and tf_info.get("hasContribOptScipy")
        and report["modules"]["cv2"].get("ok")  # type: ignore[index, union-attr]
        and report["modules"]["scipy"].get("ok")  # type: ignore[index, union-attr]
        and report["modules"]["numpy"].get("ok")  # type: ignore[index, union-attr]
        and report["scriptHelp"].get("ok")  # type: ignore[union-attr]
    )
    report["readyForCliAndCommandPlanning"] = required_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if not required_ok:
            print("runtime check failed: TensorFlow v1 symbols, image deps, or neural_style.py --help are missing", file=sys.stderr)
    return 0 if required_ok else 1


if __name__ == "__main__":
    sys.exit(main())
