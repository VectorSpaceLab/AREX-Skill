#!/usr/bin/env python3
"""Check Photo2Cartoon portrait inference assets and runtime contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

DEFAULT_PT = Path("models/photo2cartoon_weights.pt")
DEFAULT_ONNX = Path("models/photo2cartoon_weights.onnx")
DEFAULT_SEG = Path("utils/seg_model_384.pb")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Photo2Cartoon portrait inference asset set and the "
            "expected model contracts."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository checkout root used to resolve default asset paths.",
    )
    parser.add_argument(
        "--weights-pt",
        type=Path,
        help="Explicit path to photo2cartoon_weights.pt.",
    )
    parser.add_argument(
        "--weights-onnx",
        type=Path,
        help="Explicit path to photo2cartoon_weights.onnx.",
    )
    parser.add_argument(
        "--seg-model",
        type=Path,
        help="Explicit path to seg_model_384.pb.",
    )
    parser.add_argument(
        "--mode",
        choices=("all", "pytorch", "onnx"),
        default="all",
        help="Which asset subset to validate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary after the human-readable report.",
    )
    return parser


def resolve_path(explicit: Optional[Path], repo_root: Path, default_rel: Path) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    return (repo_root / default_rel).expanduser()


def file_status(path: Path) -> Dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
    }


def inspect_torch_checkpoint(path: Path) -> Dict[str, Any]:
    result = {"status": "unchecked", "detail": ""}
    if not path.exists():
        result.update(status="missing", detail="checkpoint file not found")
        return result

    try:
        import torch
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(
            status="dependency-missing",
            detail=f"torch import failed: {exc}",
        )
        return result

    try:
        payload = torch.load(path, map_location="cpu")
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(status="unloadable", detail=f"torch.load failed: {exc}")
        return result

    if isinstance(payload, dict):
        keys = sorted(str(key) for key in payload.keys())
        has_gen = "genA2B" in payload
        result.update(
            status="ok" if has_gen else "missing-key",
            detail=f"keys={keys[:12]}{'...' if len(keys) > 12 else ''}",
            keys=keys,
            has_genA2B=has_gen,
        )
    else:
        result.update(
            status="unexpected-type",
            detail=f"expected dict checkpoint, got {type(payload).__name__}",
        )
    return result


def inspect_onnx_model(path: Path) -> Dict[str, Any]:
    result = {"status": "unchecked", "detail": ""}
    if not path.exists():
        result.update(status="missing", detail="onnx file not found")
        return result

    try:
        import onnxruntime as ort
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(
            status="dependency-missing",
            detail=f"onnxruntime import failed: {exc}",
        )
        return result

    try:
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(status="unloadable", detail=f"onnxruntime failed: {exc}")
        return result

    inputs = [
        {"name": item.name, "shape": item.shape, "type": item.type}
        for item in session.get_inputs()
    ]
    outputs = [
        {"name": item.name, "shape": item.shape, "type": item.type}
        for item in session.get_outputs()
    ]
    expected_input = inputs[0]["name"] if inputs else None
    expected_output = outputs[0]["name"] if outputs else None
    result.update(
        status="ok" if expected_input == "input" and expected_output == "output" else "name-mismatch",
        detail=f"inputs={inputs}; outputs={outputs}",
        inputs=inputs,
        outputs=outputs,
        expected_input=expected_input,
        expected_output=expected_output,
    )
    return result


def inspect_segmentation_model(path: Path) -> Dict[str, Any]:
    result = {"status": "unchecked", "detail": ""}
    if not path.exists():
        result.update(status="missing", detail="segmentation graph not found")
        return result

    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(
            status="dependency-missing",
            detail=f"TensorFlow import failed: {exc}",
        )
        return result

    try:
        graph = tf.Graph()
        with graph.as_default():
            with tf.io.gfile.GFile(path, "rb") as handle:
                graph_def = tf.compat.v1.GraphDef()
                graph_def.ParseFromString(handle.read())
                tf.import_graph_def(graph_def, name="")
        graph.get_tensor_by_name("input_1:0")
        graph.get_tensor_by_name("sigmoid/Sigmoid:0")
    except Exception as exc:  # pragma: no cover - runtime dependency error
        result.update(status="unloadable", detail=f"TensorFlow graph check failed: {exc}")
        return result

    result.update(status="ok", detail="found input_1:0 and sigmoid/Sigmoid:0")
    return result


def print_block(label: str, status: Dict[str, Any]) -> None:
    state = status.get("status", "unknown")
    detail = status.get("detail", "")
    print(f"- {label}: {state}")
    if detail:
        print(f"  {detail}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.expanduser()
    pt_path = resolve_path(args.weights_pt, repo_root, DEFAULT_PT)
    onnx_path = resolve_path(args.weights_onnx, repo_root, DEFAULT_ONNX)
    seg_path = resolve_path(args.seg_model, repo_root, DEFAULT_SEG)

    checks: Dict[str, Any] = {}
    print("Photo2Cartoon asset check")
    print(f"repo-root: {repo_root}")
    print(f"mode: {args.mode}")

    seg_status = inspect_segmentation_model(seg_path)
    pt_status = None
    onnx_status = None

    if args.mode in {"all", "pytorch"}:
        pt_status = inspect_torch_checkpoint(pt_path)
        print_block("PT checkpoint", pt_status)
        print_block("Segmentation graph", seg_status)
        checks["pytorch"] = {
            "weights_pt": file_status(pt_path),
            "seg_model": file_status(seg_path),
            "checkpoint_status": pt_status,
            "segmentation_status": seg_status,
        }
    if args.mode in {"all", "onnx"}:
        onnx_status = inspect_onnx_model(onnx_path)
        print_block("ONNX graph", onnx_status)
        print_block("Segmentation graph", seg_status)
        checks["onnx"] = {
            "weights_onnx": file_status(onnx_path),
            "seg_model": file_status(seg_path),
            "onnx_status": onnx_status,
            "segmentation_status": seg_status,
        }

    failures = []  # type: List[str]
    if args.mode in {"all", "pytorch"}:
        if not pt_path.exists():
            failures.append(f"missing PT checkpoint: {pt_path}")
        elif pt_status is not None and pt_status.get("status") != "ok":
            failures.append("PT checkpoint exists but could not be validated")
    if args.mode in {"all", "onnx"}:
        if not onnx_path.exists():
            failures.append(f"missing ONNX graph: {onnx_path}")
        elif onnx_status is not None and onnx_status.get("status") != "ok":
            failures.append("ONNX graph exists but could not be validated")
    if not seg_path.exists():
        failures.append(f"missing segmentation graph: {seg_path}")
    elif seg_status.get("status") != "ok":
        failures.append("segmentation graph exists but could not be validated")

    if args.json:
        print(json.dumps({"repo_root": str(repo_root), "mode": args.mode, "checks": checks, "failures": failures}, indent=2))

    if failures:
        print("Summary: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("Summary: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
