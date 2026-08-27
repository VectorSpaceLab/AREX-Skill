#!/usr/bin/env python3
"""Generate local QAIRT/QNN commands for AIMET ONNX exports.

The script is intentionally non-mutating: it resolves model/encoding paths,
prints commands, and can emit JSON. It does not invoke Qualcomm SDK tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
from typing import Any


def find_one(paths: list[Path], label: str) -> Path | None:
    if not paths:
        return None
    if len(paths) > 1:
        raise SystemExit(f"Multiple {label} candidates found; pass one explicitly: {', '.join(str(p) for p in paths)}")
    return paths[0]


def resolve_export(path: Path, model: str | None, encodings: str | None) -> tuple[Path, Path | None]:
    path = path.expanduser().resolve()
    if model:
        model_path = Path(model).expanduser().resolve()
    elif path.is_file() and path.suffix == ".onnx":
        model_path = path
    elif path.is_dir():
        model_path = find_one(sorted(path.glob("*.onnx")), "ONNX model")
        if model_path is None:
            # GenAILab exports often nest ONNX models under backbone/ or visual/.
            nested = sorted(p for p in path.rglob("*.onnx") if "__pycache__" not in p.parts)
            model_path = find_one(nested, "nested ONNX model")
    else:
        raise SystemExit(f"Export path is neither a directory nor an ONNX model: {path}")
    if model_path is None:
        raise SystemExit(f"No ONNX model found under {path}")
    if not model_path.is_file():
        raise SystemExit(f"ONNX model not found: {model_path}")

    if encodings:
        enc_path = Path(encodings).expanduser().resolve()
        if not enc_path.is_file():
            raise SystemExit(f"encodings file not found: {enc_path}")
    elif path.is_file() and path.suffix in {".encodings", ".json"}:
        enc_path = path
    else:
        candidates = sorted(model_path.parent.glob(model_path.stem + "*.encodings"))
        candidates += sorted(model_path.parent.glob("*.encodings"))
        candidates += sorted(model_path.parent.glob("*encodings*.json"))
        enc_path = find_one(list(dict.fromkeys(candidates)), "encodings")
    return model_path, enc_path


def q(parts: list[str | Path]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", help="AIMET export directory or ONNX model path")
    parser.add_argument("--model", help="Explicit ONNX model path")
    parser.add_argument("--encodings", help="Explicit AIMET .encodings/.json path")
    parser.add_argument("--output-dir", default="qairt_artifacts", help="Directory for generated DLC/context/output files")
    parser.add_argument("--model-name", default="aimet_model", help="Base name for DLC/context files")
    parser.add_argument("--sdk-root", default=None, help="Qualcomm AI Runtime/QNN SDK root used to form library paths")
    parser.add_argument("--backend-lib", default=None, help="Path to QNN backend library, e.g. libQnnHtp.so")
    parser.add_argument("--model-lib", default=None, help="Path to libQnnModelDlc.so")
    parser.add_argument("--input-list", default="input_list.txt", help="qnn-net-run input list path")
    parser.add_argument("--quantizer-extra", action="append", default=[], help="Extra qairt-quantizer option; repeatable")
    parser.add_argument("--converter-extra", action="append", default=[], help="Extra qairt-converter option; repeatable")
    parser.add_argument("--context-extra", action="append", default=[], help="Extra qnn-context-binary-generator option; repeatable")
    parser.add_argument("--net-run-extra", action="append", default=[], help="Extra qnn-net-run option; repeatable")
    parser.add_argument("--allow-missing-encodings", action="store_true", help="Print QDQ/float-path commands when no encodings file is found")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of shell commands")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_path, enc_path = resolve_export(Path(args.export), args.model, args.encodings)
    if enc_path is None and not args.allow_missing_encodings:
        raise SystemExit("No AIMET encodings found; pass --encodings or --allow-missing-encodings for QDQ/float-path flows")

    out_dir = Path(args.output_dir).expanduser().resolve()
    non_quant_dlc = out_dir / f"{args.model_name}.dlc"
    quant_dlc = out_dir / f"{args.model_name}_quantized.dlc"
    context_dir = out_dir / "qnn_context"
    binary_name = f"{args.model_name}.bin"

    if args.sdk_root:
        sdk = Path(args.sdk_root).expanduser().resolve()
        backend_lib = args.backend_lib or str(sdk / "lib" / "x86_64-linux-clang" / "libQnnHtp.so")
        model_lib = args.model_lib or str(sdk / "lib" / "x86_64-linux-clang" / "libQnnModelDlc.so")
    else:
        backend_lib = args.backend_lib or "libQnnHtp.so"
        model_lib = args.model_lib or "libQnnModelDlc.so"

    converter_cmd: list[str | Path] = [
        "qairt-converter",
        "--input_network", model_path,
        "--output_path", non_quant_dlc,
    ]
    if enc_path is not None:
        converter_cmd.extend(["--quantization_overrides", enc_path])
    converter_cmd.extend(args.converter_extra)

    quantizer_cmd: list[str | Path] = [
        "qairt-quantizer",
        "--input_dlc", non_quant_dlc,
        "--output_dlc", quant_dlc,
        "--float_fallback",
    ]
    quantizer_cmd.extend(args.quantizer_extra)

    context_cmd: list[str | Path] = [
        "qnn-context-binary-generator",
        "--model", model_lib,
        "--backend", backend_lib,
        "--dlc_path", quant_dlc,
        "--output_dir", context_dir,
        "--binary_file", binary_name,
    ]
    context_cmd.extend(args.context_extra)

    net_run_cmd: list[str | Path] = [
        "qnn-net-run",
        "--backend", backend_lib,
        "--retrieve_context", context_dir / binary_name,
        "--input_list", Path(args.input_list).expanduser(),
        "--output_dir", out_dir / "qnn_outputs",
    ]
    net_run_cmd.extend(args.net_run_extra)

    payload: dict[str, Any] = {
        "model": str(model_path),
        "encodings": str(enc_path) if enc_path else None,
        "output_dir": str(out_dir),
        "requires_sdk_on_path": ["qairt-converter", "qairt-quantizer", "qnn-context-binary-generator", "qnn-net-run"],
        "commands": {
            "prepare": f"mkdir -p {shlex.quote(str(out_dir))}",
            "convert": q(converter_cmd),
            "quantize": q(quantizer_cmd),
            "compile_context": q(context_cmd),
            "run_inference": q(net_run_cmd),
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("# Validate AIMET export first, then source the QAIRT/QNN SDK environment.")
        print("# Model:", model_path)
        print("# Encodings:", enc_path or "not provided (QDQ/float-path flow)")
        print(payload["commands"]["prepare"])
        print(payload["commands"]["convert"])
        print(payload["commands"]["quantize"])
        print(payload["commands"]["compile_context"])
        print(payload["commands"]["run_inference"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
