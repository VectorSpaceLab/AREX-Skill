#!/usr/bin/env python3
"""Probe a VSE source-run environment without running OCR or GUI windows."""
from __future__ import annotations
import argparse, importlib.util, json, os, platform, sys
from pathlib import Path

MODULES = [
    "cv2", "paddle", "paddleocr", "PySide6", "qfluentwidgets", "pysrt",
    "wordsegment", "Levenshtein", "skimage", "lmdb", "pyclipper", "shapely",
    "imageio_ffmpeg",
]
REQUIRED_PATHS = [
    "README.md", "requirements.txt", "gui.py", "backend/main.py",
    "backend/config.py", "backend/tools/ocr.py", "backend/sushi/__main__.py",
]

def module_status(name: str):
    spec = importlib.util.find_spec(name)
    return {"module": name, "available": spec is not None}

def main() -> int:
    ap = argparse.ArgumentParser(description="Check VSE dependency and source-layout readiness without running OCR.")
    ap.add_argument("--repo-root", default=".", help="VSE source checkout to inspect (default: current directory).")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    result = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "repo_root_checked": args.repo_root,
        "source_layout": {p: (repo / p).exists() for p in REQUIRED_PATHS},
        "modules": [module_status(m) for m in MODULES],
        "paddle": {},
        "onnxruntime": {},
    }
    try:
        import paddle  # type: ignore
        result["paddle"] = {
            "version": getattr(paddle, "__version__", None),
            "compiled_with_cuda": bool(paddle.is_compiled_with_cuda()),
        }
        if result["paddle"]["compiled_with_cuda"]:
            try:
                result["paddle"]["cuda_places"] = len(paddle.static.cuda_places())
            except Exception as exc:  # pragma: no cover - backend-specific
                result["paddle"]["cuda_places_error"] = str(exc)
    except Exception as exc:
        result["paddle"] = {"error": type(exc).__name__ + ": " + str(exc)}
    try:
        import onnxruntime as ort  # type: ignore
        result["onnxruntime"] = {"providers": ort.get_available_providers()}
    except Exception as exc:
        result["onnxruntime"] = {"error": type(exc).__name__ + ": " + str(exc)}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Python: {result['python']} on {result['platform']}")
        missing_paths = [p for p, ok in result["source_layout"].items() if not ok]
        print("VSE source layout:", "ok" if not missing_paths else "missing " + ", ".join(missing_paths))
        missing_mods = [m["module"] for m in result["modules"] if not m["available"]]
        print("Python modules:", "ok" if not missing_mods else "missing " + ", ".join(missing_mods))
        print("Paddle:", result["paddle"])
        print("ONNX Runtime:", result["onnxruntime"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
