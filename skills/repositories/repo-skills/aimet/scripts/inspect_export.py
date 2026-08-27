#!/usr/bin/env python3
"""Inspect AIMET exported ONNX and encodings artifacts.

Accepts an AIMET export directory, a GenAILab export root with nested
backbone/visual ONNX files, a single .onnx model, or an encodings JSON file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


ENC_SUFFIXES = {".encodings", ".json"}


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        path = path.resolve()
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def _enc_candidates_for(onnx_path: Path) -> list[Path]:
    candidates: list[Path] = []
    candidates.extend(sorted(onnx_path.parent.glob(onnx_path.stem + "*.encodings")))
    candidates.extend(sorted(onnx_path.parent.glob("*.encodings")))
    candidates.extend(sorted(onnx_path.parent.glob("*encodings*.json")))
    return [p for p in _dedupe(candidates) if p.is_file()]


def _pick_single(paths: list[Path], label: str, context: Path) -> Path | None:
    if not paths:
        return None
    if len(paths) > 1:
        names = ", ".join(str(p.relative_to(context) if context.is_dir() and p.is_relative_to(context) else p) for p in paths)
        raise SystemExit(f"Multiple {label} files found for {context}; pass a specific path: {names}")
    return paths[0]


def find_pairs(path: Path) -> list[tuple[Path | None, Path | None]]:
    path = path.expanduser().resolve()
    if path.is_dir():
        onnx_paths = sorted(p for p in path.rglob("*.onnx") if "__pycache__" not in p.parts)
        pairs: list[tuple[Path | None, Path | None]] = []
        for onnx_path in onnx_paths:
            pairs.append((onnx_path, _pick_single(_enc_candidates_for(onnx_path), "encodings", onnx_path.parent)))
        if not pairs:
            enc_paths = sorted(p for p in path.rglob("*.encodings") if "__pycache__" not in p.parts)
            enc_paths.extend(sorted(p for p in path.rglob("*encodings*.json") if "__pycache__" not in p.parts))
            for enc_path in _dedupe(enc_paths):
                pairs.append((None, enc_path))
        return pairs
    if path.is_file() and path.suffix == ".onnx":
        return [(path, _pick_single(_enc_candidates_for(path), "encodings", path.parent))]
    if path.is_file() and path.suffix in ENC_SUFFIXES:
        onnx = _pick_single(sorted(path.parent.glob("*.onnx")), "ONNX", path.parent)
        return [(onnx, path)]
    raise SystemExit(f"Unsupported path type: {path}")


def inspect_onnx(path: Path) -> None:
    try:
        import onnx
    except ImportError as exc:
        raise SystemExit("onnx is required to inspect model structure") from exc
    model = onnx.load_model(path)
    q_nodes = [n for n in model.graph.node if n.op_type in {"QuantizeLinear", "DequantizeLinear"}]
    print("onnx", path)
    print("  ir_version", model.ir_version, "opsets", [(o.domain or "ai.onnx", o.version) for o in model.opset_import])
    print("  nodes", len(model.graph.node), "qdq_nodes", len(q_nodes))
    print("  initializers", len(model.graph.initializer))
    print("  inputs", [i.name for i in model.graph.input])
    print("  outputs", [o.name for o in model.graph.output])


def inspect_encodings(path: Path) -> None:
    data = json.loads(path.read_text())
    print("encodings", path)
    if not isinstance(data, dict):
        raise SystemExit(f"Encodings file must contain a JSON object: {path}")
    print("  top_keys", sorted(data.keys()))
    if isinstance(data.get("activation_encodings"), dict):
        print("  activation_encodings", len(data["activation_encodings"]))
    if isinstance(data.get("param_encodings"), dict):
        print("  param_encodings", len(data["param_encodings"]))
    if isinstance(data.get("quantizer_args"), dict):
        print("  quantizer_args", sorted(data["quantizer_args"].keys()))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Export directory/root, .onnx model, or encodings JSON file")
    parser.add_argument("--all", action="store_true", help="Inspect every ONNX/encodings pair under a directory")
    parser.add_argument("--allow-missing-encodings", action="store_true", help="Return success when only the ONNX file is present")
    args = parser.parse_args(list(argv) if argv is not None else None)

    pairs = find_pairs(args.path)
    if not pairs:
        raise SystemExit("No ONNX or encodings artifacts found")
    if len(pairs) > 1 and not args.all:
        names = ", ".join(str(onnx or enc) for onnx, enc in pairs)
        raise SystemExit(f"Multiple candidate exports found; pass --all or a specific path: {names}")

    failures = 0
    for index, (onnx_path, enc_path) in enumerate(pairs, 1):
        if len(pairs) > 1:
            print(f"\n== artifact {index}/{len(pairs)} ==")
        if onnx_path is None:
            print("onnx missing")
            failures += 1
        else:
            inspect_onnx(onnx_path)
        if enc_path is None:
            if args.allow_missing_encodings:
                print("encodings missing: allowed")
            else:
                print("encodings missing")
                failures += 1
        else:
            inspect_encodings(enc_path)
    if failures:
        raise SystemExit(f"export_inspection_failed failures={failures}")
    print("export_inspection_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
