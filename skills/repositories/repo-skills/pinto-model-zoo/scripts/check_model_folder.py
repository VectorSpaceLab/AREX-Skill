#!/usr/bin/env python3
"""Inspect a selected PINTO_model_zoo model folder without downloads.

The helper is stdlib-only and safe by default. It summarizes license/readme
presence, model artifact extensions, common script families, OpenVINO XML/BIN
pairing, and likely backend hints. It does not import ML frameworks, execute
scripts, or access the network.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ARTIFACT_HINTS = {
    ".onnx": "ONNX / ONNX Runtime / conversion source",
    ".tflite": "TensorFlow Lite / EdgeTPU when filename indicates edgetpu",
    ".xml": "OpenVINO IR model graph; requires matching .bin weights in most cases",
    ".bin": "OpenVINO IR weights or binary data; pair with .xml when applicable",
    ".pb": "TensorFlow frozen graph or protobuf artifact",
    ".h5": "Keras/TensorFlow model artifact",
    ".mlmodel": "CoreML model artifact",
    ".mlpackage": "CoreML package artifact",
    ".json": "Could be TFJS model.json, config, anchors, labels, or metadata",
    ".flatbuffers": "FlatBuffers schema/binary support artifact",
    ".npy": "NumPy support tensor, anchor, prior, or postprocess artifact",
}

SCRIPT_HINTS = [
    ("download", "artifact acquisition"),
    ("tflite", "TensorFlow Lite conversion or runtime"),
    ("quant", "quantization"),
    ("openvino", "OpenVINO conversion or runtime"),
    ("onnx", "ONNX conversion or runtime"),
    ("coreml", "CoreML conversion"),
    ("tfjs", "TensorFlow.js conversion or runtime"),
    ("tftrt", "TensorFlow-TensorRT"),
    ("tensorrt", "TensorRT / TF-TRT"),
    ("demo", "demo or inference"),
    ("infer", "inference"),
    ("test", "smoke test"),
    ("camera", "camera/video runtime"),
    ("video", "video runtime"),
    ("usbcam", "USB camera runtime"),
]


def relname(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def classify_script(path: Path) -> list[str]:
    name = path.name.casefold()
    labels = [label for token, label in SCRIPT_HINTS if token in name]
    if path.suffix == ".sh" and "download" not in name:
        labels.append("shell workflow")
    if path.suffix == ".py" and not labels:
        labels.append("python helper or workflow")
    return sorted(set(labels))


def inspect_folder(folder: Path, max_files: int) -> dict[str, Any]:
    folder = folder.resolve()
    if not folder.exists():
        raise SystemExit(f"Folder does not exist: {folder}")
    if not folder.is_dir():
        raise SystemExit(f"Not a directory: {folder}")

    files = [p for p in folder.rglob("*") if p.is_file()]
    licenses = [p for p in files if p.name.casefold().startswith(("license", "notice", "copying"))]
    readmes = [p for p in files if p.name.casefold().startswith("readme") or p.suffix.casefold() == ".md"]
    scripts = [p for p in files if p.suffix.casefold() in {".py", ".sh", ".bash", ".zsh"}]
    artifacts = [p for p in files if p.suffix.casefold() in ARTIFACT_HINTS]

    by_ext: dict[str, list[str]] = {}
    for p in artifacts:
        by_ext.setdefault(p.suffix.casefold(), []).append(relname(p, folder))
    for values in by_ext.values():
        values.sort()
        if max_files >= 0 and len(values) > max_files:
            del values[max_files:]

    xml_stems = {p.with_suffix("").name for p in artifacts if p.suffix.casefold() == ".xml"}
    bin_stems = {p.with_suffix("").name for p in artifacts if p.suffix.casefold() == ".bin"}
    openvino_pairing = {
        "xml_count": len(xml_stems),
        "bin_count": len(bin_stems),
        "xml_without_same_stem_bin": sorted(xml_stems - bin_stems),
        "bin_without_same_stem_xml": sorted(bin_stems - xml_stems),
        "note": "OpenVINO IR commonly needs an .xml graph and .bin weights pair; some files may be support binaries rather than IR weights.",
    }

    script_summaries = []
    for p in sorted(scripts)[: None if max_files < 0 else max_files]:
        script_summaries.append({"path": relname(p, folder), "hints": classify_script(p)})

    backend_hints = sorted({ARTIFACT_HINTS[p.suffix.casefold()] for p in artifacts})
    if any("edgetpu" in p.name.casefold() for p in artifacts):
        backend_hints.append("EdgeTPU-compiled or EdgeTPU-targeted artifact")
    if any("model.json" == p.name.casefold() for p in artifacts):
        backend_hints.append("TensorFlow.js model.json candidate")

    return {
        "folder": str(folder),
        "file_count": len(files),
        "license_files": [relname(p, folder) for p in sorted(licenses)],
        "readme_or_note_files": [relname(p, folder) for p in sorted(readmes)[: None if max_files < 0 else max_files]],
        "artifact_counts": {ext: len(paths) for ext, paths in sorted(by_ext.items())},
        "artifact_examples": by_ext,
        "backend_hints": backend_hints,
        "scripts": script_summaries,
        "download_script_count": sum(1 for p in scripts if p.name.startswith("download")),
        "openvino_pairing": openvino_pairing,
        "warnings": [
            "This helper did not execute downloads, demos, conversion scripts, or ML runtimes.",
            "Review per-folder license files before use or redistribution.",
            "Catalog flags show upstream availability, not proof that this local folder already contains every artifact.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a PINTO_model_zoo model folder for artifacts, scripts, and license/readme files without executing anything.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("folder", type=Path, help="selected model directory to inspect")
    parser.add_argument("--max-files", type=int, default=60, help="maximum example paths/scripts to include per section; -1 for all")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    info = inspect_folder(args.folder, args.max_files)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    print(f"Folder: {info['folder']}")
    print(f"Files: {info['file_count']}")
    print("License files:", ", ".join(info["license_files"]) or "none found")
    print("README/note files:", ", ".join(info["readme_or_note_files"]) or "none found")
    print("Artifact counts:")
    for ext, count in info["artifact_counts"].items():
        print(f"  {ext}: {count}")
    print("Backend hints:")
    for hint in info["backend_hints"]:
        print(f"  - {hint}")
    print("Scripts:")
    for script in info["scripts"]:
        print(f"  - {script['path']}: {', '.join(script['hints']) or 'unclassified'}")
    pair = info["openvino_pairing"]
    if pair["xml_count"] or pair["bin_count"]:
        print("OpenVINO pair check:")
        print(f"  xml={pair['xml_count']} bin={pair['bin_count']}")
        if pair["xml_without_same_stem_bin"]:
            print("  xml without same-stem bin:", ", ".join(pair["xml_without_same_stem_bin"]))
        if pair["bin_without_same_stem_xml"]:
            print("  bin without same-stem xml:", ", ".join(pair["bin_without_same_stem_xml"]))
    print("Warnings:")
    for warning in info["warnings"]:
        print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
