#!/usr/bin/env python3
"""Classify PINTO_model_zoo conversion/quantization script text.

The helper is intentionally stdlib-only. It inspects Python or shell script text
and reports conversion families plus dataset, network, and hardware risks. It
never imports TensorFlow, ONNX, OpenVINO, CoreML, TensorRT, or other heavy
frameworks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

SCRIPT_SUFFIXES = {".py", ".sh", ".bash", ".zsh", ".txt", ".md"}

HINTS: Dict[str, Dict[str, object]] = {
    "tensorflow_lite_converter": {
        "label": "TensorFlow Lite converter / TFLite artifact",
        "patterns": [
            r"\bTFLiteConverter\b",
            r"\btf\.lite\b",
            r"\btflite_convert\b",
            r"\.tflite\b",
            r"(?<![A-Za-z0-9])tflite(?![A-Za-z0-9])",
            r"\btflite2tensorflow\b",
            r"\btfliteiorewriter\b",
        ],
    },
    "representative_dataset": {
        "label": "Representative dataset or calibration",
        "patterns": [
            r"\brepresentative_dataset\b",
            r"\brepresentative_dataset_gen\b",
            r"\bCalibrationDataReader\b",
            r"\bcalibration(?:_|\b)",
            r"\bcalibdata\b",
            r"\bquantize_static\b",
        ],
    },
    "saved_model": {
        "label": "TensorFlow SavedModel / frozen graph source",
        "patterns": [
            r"\bfrom_saved_model\b",
            r"\bsaved_model_cli\b",
            r"\bsaved_model\b",
            r"\bSavedModel\b",
            r"\.pb\b",
            r"\.h5\b",
        ],
    },
    "onnx": {
        "label": "ONNX conversion or artifact",
        "patterns": [
            r"(?<![A-Za-z0-9])onnx(?![A-Za-z0-9])",
            r"\.onnx\b",
            r"\bonnxruntime\b",
            r"\bonnx2tf\b",
            r"\btf2onnx\b",
            r"\bonnxsim\b",
            r"\bquantize_static\b",
        ],
    },
    "openvino": {
        "label": "OpenVINO IR or runtime",
        "patterns": [
            r"(?<![A-Za-z0-9])openvino(?![A-Za-z0-9])",
            r"\bOpenVINO\b",
            r"\bmo(?:\.py)?\b",
            r"\.xml\b",
            r"\.bin\b",
            r"\bbenchmark_app\b",
            r"\bmyriad\b",
            r"\boak\b",
        ],
    },
    "coreml": {
        "label": "CoreML artifact or converter",
        "patterns": [
            r"(?<![A-Za-z0-9])coreml(?![A-Za-z0-9])",
            r"\bcoremltools\b",
            r"\.mlmodel\b",
            r"\.mlpackage\b",
        ],
    },
    "tfjs": {
        "label": "TensorFlow.js artifact or converter",
        "patterns": [
            r"(?<![A-Za-z0-9])tfjs(?![A-Za-z0-9])",
            r"\btensorflowjs_converter\b",
            r"\bmodel\.json\b",
            r"\bgroup\d+-shard\d+of\d+\.bin\b",
        ],
    },
    "tf_trt": {
        "label": "TensorFlow-TensorRT / TensorRT",
        "patterns": [
            r"(?<![A-Za-z0-9])tf[-_]?trt(?![A-Za-z0-9])",
            r"\bTF[-_]?TRT\b",
            r"\btensorrt\b",
            r"\bTensorRT\b",
            r"\btrt_convert\b",
            r"\bTrtGraphConverter\b",
        ],
    },
    "edgetpu_compiler": {
        "label": "EdgeTPU compiler/runtime path",
        "patterns": [
            r"\bedgetpu_compiler\b",
            r"(?<![A-Za-z0-9])edgetpu(?![A-Za-z0-9])",
            r"\bEdgeTPU\b",
            r"\blibedgetpu\b",
            r"\bcoral\b",
            r"_edgetpu\.tflite\b",
        ],
    },
}

RISKS: Dict[str, Dict[str, object]] = {
    "dataset_risk": {
        "label": "Dataset/calibration data dependency",
        "patterns": [
            r"\btensorflow_datasets\b",
            r"\btfds\b",
            r"\bCOCO\b|\bcoco/",
            r"\bCityscapes\b|\bcityscapes\b",
            r"\bVOC\b|\bpascal\b",
            r"\bTFDS\b",
            r"\bcalibdata\b",
            r"\.npy\b",
        ],
    },
    "network_risk": {
        "label": "Network/download side effect",
        "patterns": [
            r"\bcurl\b",
            r"\bwget\b",
            r"\bgdown\b",
            r"\bdrive\.google\b",
            r"\bs3[./-]",
            r"\bgit clone\b",
            r"\bpip install\b",
            r"\bapt(?:-get)? install\b",
        ],
    },
    "hardware_risk": {
        "label": "Hardware-specific runtime requirement",
        "patterns": [
            r"\bGPU\b|\bgpu\b",
            r"\bCUDA\b|\bcuda\b",
            r"\bTensorRT\b|\btensorrt\b",
            r"(?<![A-Za-z0-9])edgetpu(?![A-Za-z0-9])|\bEdgeTPU\b|\bcoral\b",
            r"\bRaspberry\s*Pi\b|\braspbian\b|\baarch64\b|\barmv7l\b",
            r"\bcamera\b|\bwebcam\b",
            r"(?<![A-Za-z0-9])myriad(?![A-Za-z0-9])|(?<![A-Za-z0-9])oak(?![A-Za-z0-9])",
            r"\bWebGL\b|\bwebgl\b",
        ],
    },
}


def _compile(patterns: Iterable[str]) -> List[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


COMPILED_HINTS = {
    key: (str(spec["label"]), _compile(spec["patterns"]))
    for key, spec in HINTS.items()
}
COMPILED_RISKS = {
    key: (str(spec["label"]), _compile(spec["patterns"]))
    for key, spec in RISKS.items()
}


def read_text(path: Path, max_bytes: int) -> Tuple[str, bool]:
    data = path.read_bytes()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace"), truncated


def iter_paths(inputs: List[str], recursive: bool) -> List[Path]:
    paths: List[Path] = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            globber = p.rglob("*") if recursive else p.glob("*")
            for child in globber:
                if child.is_file() and child.suffix.lower() in SCRIPT_SUFFIXES:
                    paths.append(child)
        else:
            paths.append(p)
    return paths


def collect_matches(text: str, compiled: Dict[str, Tuple[str, List[re.Pattern[str]]]]) -> Dict[str, Dict[str, object]]:
    lines = text.splitlines()
    results: Dict[str, Dict[str, object]] = {}
    for key, (label, patterns) in compiled.items():
        hits: List[Dict[str, object]] = []
        for lineno, line in enumerate(lines, start=1):
            for pattern in patterns:
                if pattern.search(line):
                    snippet = line.strip()
                    if len(snippet) > 180:
                        snippet = snippet[:177] + "..."
                    hits.append({"line": lineno, "pattern": pattern.pattern, "snippet": snippet})
                    break
            if len(hits) >= 8:
                break
        if hits:
            results[key] = {"label": label, "matches": hits}
    return results


def infer_routes(hints: Dict[str, object], risks: Dict[str, object]) -> List[str]:
    routes: List[str] = []
    if "onnx" in hints and "tensorflow_lite_converter" in hints:
        routes.append("ONNX/TensorFlow-to-TFLite conversion path detected; verify layout, shapes, and target precision.")
    elif "onnx" in hints:
        routes.append("ONNX path detected; check opset, dynamic shapes, and runtime-specific postprocessing.")
    if "representative_dataset" in hints:
        routes.append("Representative/calibration data is required for the detected quantization path.")
    if "edgetpu_compiler" in hints:
        routes.append("EdgeTPU path detected; require full-integer TFLite, compiler success, and hardware/runtime proof.")
    if "openvino" in hints:
        routes.append("OpenVINO path detected; validate XML/BIN pairing or target IR/runtime compatibility.")
    if "coreml" in hints:
        routes.append("CoreML path detected; device execution proof requires Apple runtime support.")
    if "tfjs" in hints:
        routes.append("TFJS path detected; keep model.json with all shards and verify browser/Node loading.")
    if "tf_trt" in hints:
        routes.append("TF-TRT/TensorRT path detected; require NVIDIA GPU and compatible CUDA/TensorRT/TensorFlow stack.")
    if "dataset_risk" in risks:
        routes.append("Dataset/calibration dependency detected; stop before large or unapproved data acquisition.")
    if "network_risk" in risks:
        routes.append("Network or install side effect detected; route acquisition/approval before execution.")
    if "hardware_risk" in risks:
        routes.append("Hardware-specific requirement detected; do not claim target execution without that hardware.")
    return routes


def classify_path(path: Path, max_bytes: int) -> Dict[str, object]:
    report: Dict[str, object] = {"path": str(path)}
    if not path.exists():
        report.update({"error": "path does not exist"})
        return report
    if not path.is_file():
        report.update({"error": "path is not a file"})
        return report
    text, truncated = read_text(path, max_bytes)
    hints = collect_matches(text, COMPILED_HINTS)
    risks = collect_matches(text, COMPILED_RISKS)
    report.update(
        {
            "bytes_read": min(path.stat().st_size, max_bytes),
            "truncated": truncated,
            "hints": hints,
            "risks": risks,
            "recommended_notes": infer_routes(hints, risks),
        }
    )
    return report


def print_text_report(reports: List[Dict[str, object]]) -> None:
    for idx, report in enumerate(reports):
        if idx:
            print()
        print(f"File: {report.get('path')}")
        if "error" in report:
            print(f"  ERROR: {report['error']}")
            continue
        if report.get("truncated"):
            print("  Note: input was truncated by --max-bytes")
        hints = report.get("hints", {})
        risks = report.get("risks", {})
        if not hints and not risks:
            print("  No conversion/deployment hints detected.")
            continue
        if hints:
            print("  Hints:")
            for key, detail in hints.items():
                matches = detail["matches"]  # type: ignore[index]
                lines = ", ".join(str(m["line"]) for m in matches[:5])  # type: ignore[index]
                print(f"    - {key}: {detail['label']} (lines {lines})")  # type: ignore[index]
        if risks:
            print("  Risks:")
            for key, detail in risks.items():
                matches = detail["matches"]  # type: ignore[index]
                lines = ", ".join(str(m["line"]) for m in matches[:5])  # type: ignore[index]
                print(f"    - {key}: {detail['label']} (lines {lines})")  # type: ignore[index]
        notes = report.get("recommended_notes", [])
        if notes:
            print("  Recommended notes:")
            for note in notes:
                print(f"    - {note}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect PINTO_model_zoo conversion/quantization scripts and report backend hints.",
    )
    parser.add_argument("paths", nargs="+", help="Script files or directories to inspect.")
    parser.add_argument("--recursive", action="store_true", help="When a path is a directory, inspect scripts recursively.")
    parser.add_argument("--max-bytes", type=int, default=2_000_000, help="Maximum bytes to read per file (default: 2000000).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")

    paths = iter_paths(args.paths, args.recursive)
    reports = [classify_path(path, args.max_bytes) for path in paths]
    output = {"files": reports, "count": len(reports)}
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print_text_report(reports)
    return 1 if any("error" in report for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
