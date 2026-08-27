#!/usr/bin/env python3
"""Report whether a lightweight PaddleGAN runtime is available.

This diagnostic intentionally imports only Paddle and ``ppgan``. Optional
packages are discovered without importing them, and no model is constructed,
weights are downloaded, or repository-local module is required.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - Python 3.7 with the backport installed
    import importlib_metadata  # type: ignore


OPTIONAL_MODULES: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    ("numpy", ("numpy",), "array support"),
    ("cv2", ("opencv-python", "opencv-contrib-python", "opencv-python-headless"), "OpenCV image/video I/O"),
    ("PIL", ("Pillow",), "Pillow image I/O"),
    ("yaml", ("PyYAML",), "YAML configuration parsing"),
    ("scipy", ("scipy",), "scientific image/audio operations"),
    ("skimage", ("scikit-image",), "image metrics and transforms"),
    ("imageio", ("imageio",), "media I/O"),
    ("librosa", ("librosa",), "audio processing"),
    ("decord", ("decord",), "video decoding"),
    ("dlib", ("dlib",), "optional face utilities"),
    ("clip", ("clip",), "optional CLIP-guided editing"),
)


def _distribution_version(candidates: Iterable[str]) -> Optional[str]:
    """Return the first installed distribution version without importing it."""
    for distribution in candidates:
        try:
            return importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            continue
        except Exception:
            # Broken package metadata should not make a diagnostic crash.
            continue
    return None


def _exception_text(exc: BaseException) -> str:
    text = str(exc).strip()
    return type(exc).__name__ if not text else "{}: {}".format(type(exc).__name__, text)


def probe_import(module_name: str, distributions: Sequence[str]) -> Tuple[Dict[str, Any], Optional[Any]]:
    """Import one core module and return serializable details plus the module."""
    result: Dict[str, Any] = {
        "module": module_name,
        "imported": False,
        "version": _distribution_version(distributions),
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        result["error"] = _exception_text(exc)
        return result, None

    result["imported"] = True
    module_version = getattr(module, "__version__", None)
    if module_version is not None:
        result["version"] = str(module_version)
    module_file = getattr(module, "__file__", None)
    if module_file:
        result["location"] = os.path.abspath(str(module_file))
    return result, module


def probe_optional(module_name: str, distributions: Sequence[str], purpose: str) -> Dict[str, Any]:
    """Discover an optional top-level module without importing it."""
    result: Dict[str, Any] = {
        "module": module_name,
        "purpose": purpose,
        "available": False,
        "version": _distribution_version(distributions),
        "imported": False,
    }
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:
        result["error"] = _exception_text(exc)
        return result

    result["available"] = spec is not None
    if spec is not None and spec.origin not in (None, "built-in", "frozen"):
        result["location"] = os.path.abspath(str(spec.origin))
    return result


def probe_cuda(paddle_module: Optional[Any]) -> Dict[str, Any]:
    """Query Paddle's CUDA build flag and visible device count when possible."""
    result: Dict[str, Any] = {
        "compiled_with_cuda": None,
        "device_count": None,
        "available": None,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    if paddle_module is None:
        result["error"] = "Paddle was not imported; CUDA status is unknown"
        return result

    compiled_probe = getattr(paddle_module, "is_compiled_with_cuda", None)
    if not callable(compiled_probe):
        device_namespace = getattr(paddle_module, "device", None)
        compiled_probe = getattr(device_namespace, "is_compiled_with_cuda", None)

    if callable(compiled_probe):
        try:
            result["compiled_with_cuda"] = bool(compiled_probe())
        except Exception as exc:
            result["compilation_probe_error"] = _exception_text(exc)
    else:
        result["compilation_probe_error"] = "this Paddle version exposes no CUDA compilation probe"

    try:
        cuda_namespace = getattr(getattr(paddle_module, "device"), "cuda")
        count_probe = getattr(cuda_namespace, "device_count")
        result["device_count"] = int(count_probe())
    except Exception as exc:
        # CPU-only builds commonly cannot answer this question. Preserve the
        # build result while explicitly marking device availability unknown.
        result["device_probe_error"] = _exception_text(exc)

    if result["compiled_with_cuda"] is False:
        result["available"] = False
    elif result["device_count"] is not None:
        result["available"] = bool(result["compiled_with_cuda"] and result["device_count"] > 0)
    return result


def probe_program(name: str) -> Dict[str, Any]:
    """Run a bounded version query for an external media program."""
    executable = shutil.which(name)
    result: Dict[str, Any] = {"program": name, "available": False, "path": executable}
    if executable is None:
        result["error"] = "not found on PATH"
        return result

    try:
        completed = subprocess.run(
            [executable, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "version query timed out after 5 seconds"
        return result
    except OSError as exc:
        result["error"] = _exception_text(exc)
        return result

    output = completed.stdout or completed.stderr
    lines = output.splitlines() if output else []
    result["available"] = completed.returncode == 0
    result["returncode"] = completed.returncode
    if lines:
        result["version_line"] = lines[0].strip()
    if completed.returncode != 0:
        result["error"] = "{} -version exited with status {}".format(name, completed.returncode)
    return result


def build_report() -> Dict[str, Any]:
    """Build the report without loading data, models, or weights."""
    paddle_info, paddle_module = probe_import("paddle", ("paddlepaddle-gpu", "paddlepaddle"))
    ppgan_info, _ = probe_import("ppgan", ("ppgan", "paddlegan"))
    return {
        "python": {
            "version": platform.python_version(),
            "version_detail": sys.version.replace("\n", " "),
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "imports": {"paddle": paddle_info, "ppgan": ppgan_info},
        "cuda": probe_cuda(paddle_module),
        "programs": {name: probe_program(name) for name in ("ffmpeg", "ffprobe")},
        "optional_modules": {
            name: probe_optional(name, distributions, purpose)
            for name, distributions, purpose in OPTIONAL_MODULES
        },
        "safety": {
            "models_executed": False,
            "downloads_attempted": False,
            "optional_modules_imported": False,
        },
    }


def evaluate_report(
    report: Dict[str, Any],
    require_cuda: bool,
    require_media_tools: bool,
    required_modules: Sequence[str],
) -> Tuple[int, List[str]]:
    """Return an exit status and a list of failed checks."""
    core_failures = [
        "{} import failed: {}".format(name, details.get("error", "unknown error"))
        for name, details in report["imports"].items()
        if not details.get("imported")
    ]
    requirement_failures: List[str] = []

    if require_cuda and report["cuda"].get("available") is not True:
        requirement_failures.append("a visible CUDA device was required but was not detected")
    if require_media_tools:
        for name in ("ffmpeg", "ffprobe"):
            if not report["programs"][name].get("available"):
                requirement_failures.append("{} was required but is unavailable".format(name))
    for module_name in required_modules:
        if not report["optional_modules"][module_name].get("available"):
            requirement_failures.append("optional module {!r} was required but is unavailable".format(module_name))

    # 1 means the core PaddleGAN runtime is broken, 2 means an explicitly
    # requested capability is missing, and 3 means both conditions apply.
    exit_code = (1 if core_failures else 0) + (2 if requirement_failures else 0)
    return exit_code, core_failures + requirement_failures


def _display_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def print_human(report: Dict[str, Any]) -> None:
    """Print a compact report intended for terminal users."""
    python = report["python"]
    print("PaddleGAN installation check")
    print("Python: {} ({})".format(python["version_detail"], python["executable"]))
    print("Platform: {}".format(python["platform"]))

    print("\nCore imports:")
    for name in ("paddle", "ppgan"):
        item = report["imports"][name]
        state = "OK" if item["imported"] else "FAIL"
        details = []
        if item.get("version"):
            details.append("version {}".format(item["version"]))
        if item.get("location"):
            details.append(item["location"])
        if item.get("error"):
            details.append(item["error"])
        print("  {:8} {:4} {}".format(name, state, "; ".join(details)))

    cuda = report["cuda"]
    print("\nCUDA:")
    print("  compiled with CUDA: {}".format(_display_value(cuda.get("compiled_with_cuda"))))
    print("  visible device count: {}".format(_display_value(cuda.get("device_count"))))
    print("  usable CUDA device: {}".format(_display_value(cuda.get("available"))))
    if cuda.get("cuda_visible_devices") is not None:
        print("  CUDA_VISIBLE_DEVICES: {}".format(cuda["cuda_visible_devices"]))
    for key in ("error", "compilation_probe_error", "device_probe_error"):
        if cuda.get(key):
            print("  note: {}".format(cuda[key]))

    print("\nMedia tools:")
    for name in ("ffmpeg", "ffprobe"):
        item = report["programs"][name]
        state = "OK" if item["available"] else "MISSING"
        detail = item.get("version_line") or item.get("error", "")
        print("  {:8} {:7} {}".format(name, state, detail))

    print("\nOptional modules (discovery only; not imported):")
    for name, _, _ in OPTIONAL_MODULES:
        item = report["optional_modules"][name]
        state = "found" if item["available"] else "missing"
        version = " version {}".format(item["version"]) if item.get("version") else ""
        print("  {:8} {:7}{} - {}".format(name, state, version, item["purpose"]))


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check Python, Paddle/ppgan imports, CUDA visibility, media tools, "
            "and optional PaddleGAN dependencies without running a model or downloading files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Exit status: 0 ready, 1 core import failure, 2 requested capability missing, 3 both.",
    )
    parser.add_argument("--json", action="store_true", help="emit the complete report as JSON")
    parser.add_argument(
        "--require-cuda",
        "--require-gpu",
        action="store_true",
        help="require Paddle to see at least one usable CUDA device",
    )
    parser.add_argument(
        "--require-ffmpeg",
        action="store_true",
        help="require both ffmpeg and ffprobe on PATH",
    )
    parser.add_argument(
        "--require",
        action="append",
        choices=[item[0] for item in OPTIONAL_MODULES],
        default=[],
        metavar="MODULE",
        help="require a selected optional module (repeatable)",
    )
    parser.add_argument(
        "--require-face",
        dest="require",
        action="append_const",
        const="dlib",
        help="require the optional dlib face utilities",
    )
    parser.add_argument(
        "--require-clip",
        dest="require",
        action="append_const",
        const="clip",
        help="require the optional CLIP module",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = make_parser().parse_args(argv)
    report = build_report()
    exit_code, issues = evaluate_report(
        report,
        require_cuda=args.require_cuda,
        require_media_tools=args.require_ffmpeg,
        required_modules=args.require,
    )
    report["status"] = {"ok": exit_code == 0, "exit_code": exit_code, "issues": issues}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
        print("\nResult: {} (exit {})".format("READY" if exit_code == 0 else "NOT READY", exit_code))
        for issue in issues:
            print("  - {}".format(issue))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
