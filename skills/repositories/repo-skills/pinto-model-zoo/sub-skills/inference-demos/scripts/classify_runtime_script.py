#!/usr/bin/env python3
"""Classify PINTO_model_zoo runtime/demo scripts without importing heavy backends.

This helper is intentionally stdlib-only. It reads Python script text and
reports import/backend clues, likely artifact extensions, input/output wrapper
clues, and network/hardware/headless risks. It never imports TensorFlow,
OpenVINO, ONNX Runtime, OpenCV, or other optional runtime packages.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

MODEL_EXTS = {
    ".tflite",
    ".onnx",
    ".xml",
    ".bin",
    ".pb",
    ".h5",
    ".keras",
    ".mlmodel",
    ".mlpackage",
    ".json",
    ".blob",
    ".engine",
    ".plan",
}
INPUT_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".gif",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".wav",
    ".flac",
    ".mp3",
}
AUX_EXTS = {".txt", ".csv", ".npy", ".npz", ".yaml", ".yml", ".pbtxt"}
SCRIPT_SUFFIXES = {".py", ".txt", ".md"}

BACKEND_HINTS: Dict[str, Dict[str, object]] = {
    "tensorflow_tflite": {
        "label": "TensorFlow / TensorFlow Lite runtime",
        "import_prefixes": ["tensorflow", "tflite_runtime"],
        "patterns": [
            r"\btf\.lite\b",
            r"\bInterpreter\s*\(\s*model_path\s*=",
            r"\btflite_runtime\b",
            r"\.tflite\b",
            r"(?<![A-Za-z0-9])tflite(?![A-Za-z0-9])",
            r"\btf\.saved_model\b",
            r"\btensorflow\.saved_model\b",
            r"\.pb\b",
            r"\.h5\b",
        ],
        "filename_patterns": [r"tflite", r"tensorflow", r"tf_"],
    },
    "onnx_runtime": {
        "label": "ONNX Runtime / ONNX artifact",
        "import_prefixes": ["onnxruntime", "onnx"],
        "patterns": [
            r"\bInferenceSession\b",
            r"\bonnxruntime\b",
            r"\.onnx\b",
            r"\bCPUExecutionProvider\b",
            r"\bCUDAExecutionProvider\b",
            r"\bTensorrtExecutionProvider\b",
        ],
        "filename_patterns": [r"onnx"],
    },
    "openvino": {
        "label": "OpenVINO runtime or OpenCV Inference Engine",
        "import_prefixes": ["openvino"],
        "patterns": [
            r"\bIECore\b",
            r"\bIENetwork\b",
            r"\bopenvino\b",
            r"\binference_engine\b",
            r"\breadNetFromModelOptimizer\b",
            r"\bDNN_BACKEND_INFERENCE_ENGINE\b",
            r"\.xml\b",
            r"\.bin\b",
            r"\bMYRIAD\b",
        ],
        "filename_patterns": [r"openvino"],
    },
    "tfjs_browser": {
        "label": "TensorFlow.js / browser runtime",
        "import_prefixes": [],
        "patterns": [
            r"(?<![A-Za-z0-9])tfjs(?![A-Za-z0-9])",
            r"\btensorflowjs\b",
            r"\bmodel\.json\b",
            r"\bgroup\d+-shard\d+of\d+\.bin\b",
            r"\bWebGL\b",
            r"\bwebgl\b",
            r"\bbrowser\b",
            r"\bcanvas\b",
        ],
        "filename_patterns": [r"tfjs", r"browser", r"webgl"],
    },
    "opencv_io": {
        "label": "OpenCV image/video/camera wrapper",
        "import_prefixes": ["cv2"],
        "patterns": [
            r"\bcv2?\.VideoCapture\s*\(",
            r"\bcv2?\.imshow\s*\(",
            r"\bcv2?\.waitKey\s*\(",
            r"\bcv2?\.imread\s*\(",
            r"\bcv2?\.imwrite\s*\(",
            r"\bcv2?\.VideoWriter\s*\(",
            r"\bopencv\b",
        ],
        "filename_patterns": [r"camera", r"webcam", r"video", r"image"],
    },
    "mediapipe_family": {
        "label": "MediaPipe-style model family or wrapper",
        "import_prefixes": ["mediapipe"],
        "patterns": [
            r"\bMediaPipe\b",
            r"\bmediapipe\b",
            r"\bFaceMesh\b",
            r"\bObjectron\b",
            r"\bBlazePose\b",
            r"\bBlazeFace\b",
            r"\bhand_landmark\b",
        ],
        "filename_patterns": [r"mediapipe", r"facemesh", r"objectron", r"blaze"],
    },
    "pytorch_support": {
        "label": "PyTorch used in runtime or post-processing",
        "import_prefixes": ["torch"],
        "patterns": [r"\btorch\b", r"\btorch\.nn\b", r"\.pt\b", r"\.pth\b"],
        "filename_patterns": [r"torch", r"pytorch"],
    },
    "coreml": {
        "label": "CoreML artifact/runtime clue",
        "import_prefixes": ["coremltools"],
        "patterns": [r"\bcoreml\b", r"\.mlmodel\b", r"\.mlpackage\b"],
        "filename_patterns": [r"coreml"],
    },
}

IO_HINTS: Dict[str, Dict[str, object]] = {
    "live_camera": {
        "label": "Live camera/webcam input",
        "patterns": [
            r"VideoCapture\s*\(\s*0\s*\)",
            r"--camera\b",
            r"--device\b",
            r"usbcam",
            r"webcam",
            r"USB Camera",
            r"cap\.read\s*\(",
        ],
    },
    "video_file": {
        "label": "Video file input or output",
        "patterns": [
            r"--movie_file\b",
            r"--video\b",
            r"VideoCapture\s*\(",
            r"VideoWriter\s*\(",
            r"\.mp4\b",
            r"\.avi\b",
            r"\.mov\b",
            r"\.mkv\b",
        ],
    },
    "image_file": {
        "label": "Image file input or output",
        "patterns": [
            r"\bimread\s*\(",
            r"\bImage\.open\s*\(",
            r"--image\b",
            r"--images\b",
            r"image_file",
            r"\.jpg\b",
            r"\.jpeg\b",
            r"\.png\b",
            r"\.bmp\b",
            r"\.webp\b",
        ],
    },
    "display_gui": {
        "label": "Interactive display/window usage",
        "patterns": [r"\bimshow\s*\(", r"\bwaitKey\s*\(", r"\bnamedWindow\s*\("],
    },
    "auxiliary_assets": {
        "label": "Labels, anchors, metadata, or sidecar assets",
        "patterns": [
            r"labels?[_-]?map",
            r"labels?\.txt\b",
            r"anchors?\.csv\b",
            r"classes?\.csv\b",
            r"\.npy\b",
            r"\.csv\b",
            r"\.txt\b",
        ],
    },
}

RISK_HINTS: Dict[str, Dict[str, object]] = {
    "network_or_download": {
        "label": "Network/download/install side effect",
        "patterns": [
            r"\bcurl\b",
            r"\bwget\b",
            r"\bgdown\b",
            r"\brequests\.",
            r"\burllib\.",
            r"drive\.google",
            r"\bdownload\b",
            r"\bpip install\b",
            r"\bapt(?:-get)? install\b",
        ],
    },
    "hardware_specific": {
        "label": "Hardware/accelerator/platform-specific requirement",
        "patterns": [
            r"\bCUDA\b|\bcuda\b",
            r"\bGPU\b|\bgpu\b",
            r"\bTensorRT\b|\btensorrt\b|\bTRT\b",
            r"\bEdgeTPU\b|\bedgetpu\b|\blibedgetpu\b|\bcoral\b",
            r"\bMYRIAD\b|\bVPU\b",
            r"\bRaspberry\s*Pi\b|\braspbian\b|\baarch64\b|\barmv7l\b",
            r"\bOpenGL\b|\bWebGL\b|\bwebgl\b",
            r"\bv4l2\b|\bpicamera\b|\blibcamera\b",
        ],
    },
    "headless_ci": {
        "label": "Headless CI/display risk",
        "patterns": [r"\bimshow\s*\(", r"\bwaitKey\s*\(", r"\bnamedWindow\s*\(", r"VideoCapture\s*\(\s*0\s*\)"],
    },
    "conversion_or_export": {
        "label": "Conversion/export/quantization rather than demo execution",
        "patterns": [
            r"\bTFLiteConverter\b",
            r"\brepresentative_dataset\b",
            r"\bonnxsim\b",
            r"\bonnx2tf\b",
            r"\btf2onnx\b",
            r"\bcoremltools\b",
            r"\btensorflowjs_converter\b",
            r"\bedgetpu_compiler\b",
            r"\bquantiz(?:e|ation)\b",
            r"\bconvert(?:er|_script)?\b",
        ],
    },
}


def _compile(patterns: Iterable[str]) -> List[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


COMPILED_BACKENDS = {
    key: (
        str(spec["label"]),
        list(spec.get("import_prefixes", [])),
        _compile(spec.get("patterns", [])),
        _compile(spec.get("filename_patterns", [])),
    )
    for key, spec in BACKEND_HINTS.items()
}
COMPILED_IO = {
    key: (str(spec["label"]), _compile(spec["patterns"]))
    for key, spec in IO_HINTS.items()
}
COMPILED_RISKS = {
    key: (str(spec["label"]), _compile(spec["patterns"]))
    for key, spec in RISK_HINTS.items()
}


def read_text(path: Path, max_bytes: int) -> Tuple[str, bool]:
    data = path.read_bytes()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace"), truncated


def iter_paths(inputs: Sequence[str], recursive: bool) -> List[Path]:
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


def extract_imports(text: str) -> Tuple[List[Dict[str, object]], str | None]:
    imports: List[Dict[str, object]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = re.match(r"\s*(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+(.+))", line)
            if not m:
                continue
            if m.group(1):
                imports.append({"module": m.group(1), "line": lineno})
            else:
                for chunk in m.group(2).split(","):
                    mod = chunk.strip().split()[0]
                    if mod:
                        imports.append({"module": mod, "line": lineno})
        return imports, f"syntax-error: {exc.msg} at line {exc.lineno}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "line": getattr(node, "lineno", None)})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append({"module": module, "line": getattr(node, "lineno", None)})
    imports.sort(key=lambda item: (int(item.get("line") or 0), str(item.get("module"))))
    return imports, None


def extract_string_literals(text: str) -> List[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        values = re.findall(r"['\"]([^'\"]{1,300})['\"]", text)
        return sorted(set(values))
    values: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return sorted(set(values))


def line_matches(text: str, patterns: List[re.Pattern[str]], limit: int = 8) -> List[Dict[str, object]]:
    hits: List[Dict[str, object]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            if pattern.search(line):
                snippet = line.strip()
                if len(snippet) > 180:
                    snippet = snippet[:177] + "..."
                hits.append({"source": "text", "line": lineno, "pattern": pattern.pattern, "snippet": snippet})
                break
        if len(hits) >= limit:
            break
    return hits


def match_import_prefix(module: str, prefixes: Sequence[str]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


def collect_backend_hints(path: Path, text: str, imports: List[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    results: Dict[str, Dict[str, object]] = {}
    filename = path.name.lower()
    for key, (label, import_prefixes, patterns, filename_patterns) in COMPILED_BACKENDS.items():
        evidence: List[Dict[str, object]] = []
        for item in imports:
            module = str(item.get("module") or "")
            if match_import_prefix(module, import_prefixes):
                evidence.append({"source": "import", "line": item.get("line"), "snippet": module})
        evidence.extend(line_matches(text, patterns))
        for pattern in filename_patterns:
            if pattern.search(filename):
                evidence.append({"source": "filename", "line": None, "pattern": pattern.pattern, "snippet": path.name})
        if evidence:
            results[key] = {"label": label, "evidence": evidence[:12]}
    return results


def collect_matches(text: str, compiled: Dict[str, Tuple[str, List[re.Pattern[str]]]]) -> Dict[str, Dict[str, object]]:
    results: Dict[str, Dict[str, object]] = {}
    for key, (label, patterns) in compiled.items():
        hits = line_matches(text, patterns)
        if hits:
            results[key] = {"label": label, "evidence": hits}
    return results


def classify_literals(literals: List[str], text: str) -> Dict[str, object]:
    model_paths: List[str] = []
    input_paths: List[str] = []
    aux_paths: List[str] = []
    output_paths: List[str] = []
    model_exts = set()
    input_exts = set()
    aux_exts = set()

    tokens = set(literals)
    # Include bare extension mentions that are not string literals.
    for ext in sorted(MODEL_EXTS | INPUT_EXTS | AUX_EXTS, key=len, reverse=True):
        if re.search(re.escape(ext) + r"\b", text, flags=re.IGNORECASE):
            tokens.add("*" + ext)
    for value in sorted(tokens):
        lower = value.lower()
        suffix = Path(lower).suffix
        if (
            lower == "saved_model"
            or lower.startswith("saved_model/")
            or "/saved_model/" in lower
            or lower.endswith("/saved_model")
        ):
            if "saved_model directory" not in model_paths:
                model_paths.append("saved_model directory")
        if suffix in MODEL_EXTS or any(lower.endswith(ext) for ext in MODEL_EXTS):
            ext = suffix if suffix in MODEL_EXTS else next(ext for ext in MODEL_EXTS if lower.endswith(ext))
            model_exts.add(ext)
            if len(value) <= 240 and value not in model_paths:
                model_paths.append(value)
        elif suffix in INPUT_EXTS or any(lower.endswith(ext) for ext in INPUT_EXTS):
            ext = suffix if suffix in INPUT_EXTS else next(ext for ext in INPUT_EXTS if lower.endswith(ext))
            input_exts.add(ext)
            if len(value) <= 240 and value not in input_paths:
                input_paths.append(value)
        elif suffix in AUX_EXTS or any(lower.endswith(ext) for ext in AUX_EXTS):
            ext = suffix if suffix in AUX_EXTS else next(ext for ext in AUX_EXTS if lower.endswith(ext))
            aux_exts.add(ext)
            if len(value) <= 240 and value not in aux_paths:
                aux_paths.append(value)
        if re.search(r"(?:output|result|record|save)", lower) and (suffix in INPUT_EXTS or suffix in {".mp4", ".avi", ".mov"}):
            if value not in output_paths:
                output_paths.append(value)

    return {
        "model_extensions": sorted(model_exts),
        "model_paths_or_tokens": model_paths[:24],
        "input_extensions": sorted(input_exts),
        "input_paths_or_tokens": input_paths[:24],
        "auxiliary_extensions": sorted(aux_exts),
        "auxiliary_paths_or_tokens": aux_paths[:24],
        "output_paths_or_tokens": output_paths[:12],
    }


def infer_notes(
    backend_hints: Dict[str, object],
    artifact_hints: Dict[str, object],
    io_hints: Dict[str, object],
    risks: Dict[str, object],
) -> List[str]:
    notes: List[str] = []
    model_exts = set(artifact_hints.get("model_extensions", []))
    if model_exts:
        notes.append("Preflight every referenced model artifact path before importing the runtime.")
    if ".xml" in model_exts or ".bin" in model_exts or "openvino" in backend_hints:
        notes.append("For OpenVINO, validate that XML and BIN files are a matching pair in the selected folder.")
    if "tensorflow_tflite" in backend_hints:
        notes.append("TensorFlow/TFLite detected; distinguish full TensorFlow needs from lightweight tflite-runtime-only scripts.")
    if "onnx_runtime" in backend_hints:
        notes.append("ONNX Runtime detected; choose CPU/GPU/TensorRT providers explicitly and record fallback behavior.")
    if "tfjs_browser" in backend_hints:
        notes.append("TFJS/browser detected; use a static-server/browser plan and keep model.json with all shard files.")
    if "live_camera" in io_hints or "display_gui" in io_hints:
        notes.append("Camera/display behavior detected; for CI, replace it with fixed image/clip fixtures and saved outputs.")
    if "network_or_download" in risks:
        notes.append("Network/download side effect detected; route artifact acquisition through model-acquisition before execution.")
    if "conversion_or_export" in risks:
        notes.append("Conversion/export keywords detected; route conversion or quantization work to conversion-and-deployment.")
    if "hardware_specific" in risks:
        notes.append("Hardware-specific clues detected; do not claim backend proof without the concrete device/runtime.")
    if not notes:
        notes.append("No heavyweight runtime was executed; this is static inspection only.")
    return notes


def classify_path(path: Path, max_bytes: int) -> Dict[str, object]:
    report: Dict[str, object] = {"path": str(path)}
    if not path.exists():
        report["error"] = "path does not exist"
        return report
    if not path.is_file():
        report["error"] = "path is not a file"
        return report
    text, truncated = read_text(path, max_bytes)
    imports, parse_warning = extract_imports(text)
    literals = extract_string_literals(text)
    backend_hints = collect_backend_hints(path, text, imports)
    io_hints = collect_matches(text, COMPILED_IO)
    risks = collect_matches(text, COMPILED_RISKS)
    artifact_hints = classify_literals(literals, text)
    report.update(
        {
            "bytes_read": min(path.stat().st_size, max_bytes),
            "truncated": truncated,
            "parse_warning": parse_warning,
            "imports": imports[:80],
            "backend_hints": backend_hints,
            "artifact_hints": artifact_hints,
            "io_hints": io_hints,
            "risks": risks,
            "recommended_notes": infer_notes(backend_hints, artifact_hints, io_hints, risks),
        }
    )
    return report


def _format_evidence(detail: Dict[str, object], limit: int = 5) -> str:
    evidence = detail.get("evidence", [])
    parts: List[str] = []
    if isinstance(evidence, list):
        for item in evidence[:limit]:
            if not isinstance(item, dict):
                continue
            line = item.get("line")
            source = item.get("source")
            snippet = item.get("snippet")
            prefix = f"{source}" if source else "evidence"
            if line:
                prefix += f":{line}"
            parts.append(f"{prefix}={snippet}")
    return "; ".join(parts)


def print_text_report(reports: List[Dict[str, object]]) -> None:
    for index, report in enumerate(reports):
        if index:
            print()
        print(f"File: {report.get('path')}")
        if "error" in report:
            print(f"  ERROR: {report['error']}")
            continue
        if report.get("truncated"):
            print("  Note: input was truncated by --max-bytes")
        if report.get("parse_warning"):
            print(f"  Parse warning: {report['parse_warning']}")
        imports = report.get("imports", [])
        if imports:
            import_names = [str(item.get("module")) for item in imports[:12] if isinstance(item, dict)]
            print(f"  Imports: {', '.join(import_names)}")
        backend_hints = report.get("backend_hints", {})
        if backend_hints:
            print("  Backend hints:")
            for key, detail in backend_hints.items():
                print(f"    - {key}: {detail['label']} ({_format_evidence(detail)})")  # type: ignore[index]
        else:
            print("  Backend hints: none detected")
        artifact_hints = report.get("artifact_hints", {})
        if artifact_hints:
            print("  Artifact hints:")
            print(f"    - model extensions: {', '.join(artifact_hints.get('model_extensions', [])) or 'none'}")  # type: ignore[union-attr]
            model_paths = artifact_hints.get("model_paths_or_tokens", [])  # type: ignore[union-attr]
            if model_paths:
                print(f"    - model paths/tokens: {', '.join(str(x) for x in model_paths[:8])}")
            print(f"    - input extensions: {', '.join(artifact_hints.get('input_extensions', [])) or 'none'}")  # type: ignore[union-attr]
            input_paths = artifact_hints.get("input_paths_or_tokens", [])  # type: ignore[union-attr]
            if input_paths:
                print(f"    - input paths/tokens: {', '.join(str(x) for x in input_paths[:8])}")
            aux_paths = artifact_hints.get("auxiliary_paths_or_tokens", [])  # type: ignore[union-attr]
            if aux_paths:
                print(f"    - auxiliary paths/tokens: {', '.join(str(x) for x in aux_paths[:8])}")
        io_hints = report.get("io_hints", {})
        if io_hints:
            print("  I/O hints:")
            for key, detail in io_hints.items():
                print(f"    - {key}: {detail['label']} ({_format_evidence(detail)})")  # type: ignore[index]
        risks = report.get("risks", {})
        if risks:
            print("  Risks:")
            for key, detail in risks.items():
                print(f"    - {key}: {detail['label']} ({_format_evidence(detail)})")  # type: ignore[index]
        notes = report.get("recommended_notes", [])
        if notes:
            print("  Recommended notes:")
            for note in notes:
                print(f"    - {note}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statically inspect PINTO_model_zoo Python demo scripts for backend, asset, I/O, and risk clues.",
    )
    parser.add_argument("paths", nargs="+", help="Python script files or directories to inspect.")
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
