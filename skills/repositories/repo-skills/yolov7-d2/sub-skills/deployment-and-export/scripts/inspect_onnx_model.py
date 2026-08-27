#!/usr/bin/env python3
"""Inspect ONNX graph IO and optional ONNXRuntime session IO.

Self-contained: does not import YOLOv7-d2 or depend on repository files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect ONNX model inputs/outputs and ORT providers.")
    p.add_argument("model", nargs="?", help="ONNX model path.")
    p.add_argument("--model", dest="model_opt", help="ONNX model path, named form.")
    p.add_argument("--provider", action="append", help="Requested ORT provider; repeat for priority order.")
    p.add_argument("--providers", action="store_true", help="Print ORT providers and create a CPU session when possible.")
    p.add_argument("--no-ort", action="store_true", help="Skip ONNXRuntime session creation.")
    p.add_argument("--check-model", action="store_true", help="Run onnx.checker.check_model.")
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def dim_list(value_info: Any) -> list[Any]:
    dims = []
    for dim in value_info.type.tensor_type.shape.dim:
        if dim.dim_param:
            dims.append(dim.dim_param)
        elif dim.HasField("dim_value"):
            dims.append(int(dim.dim_value))
        else:
            dims.append("?")
    return dims


def graph_io(model_path: Path, check: bool) -> dict[str, Any]:
    try:
        import onnx  # type: ignore
    except Exception as exc:
        raise RuntimeError("onnx package is required for graph inspection") from exc
    model = onnx.load(str(model_path))
    if check:
        onnx.checker.check_model(model)

    def one(value_info: Any) -> dict[str, Any]:
        elem = value_info.type.tensor_type.elem_type
        try:
            dtype = onnx.TensorProto.DataType.Name(elem)
        except Exception:
            dtype = str(elem)
        return {"name": value_info.name, "dtype": dtype, "shape": dim_list(value_info)}

    return {
        "path": str(model_path),
        "ir_version": int(model.ir_version),
        "opsets": [{"domain": op.domain or "ai.onnx", "version": int(op.version)} for op in model.opset_import],
        "inputs": [one(v) for v in model.graph.input],
        "outputs": [one(v) for v in model.graph.output],
        "num_nodes": len(model.graph.node),
    }


def ort_io(model_path: Path, providers: list[str] | None, cpu_default: bool) -> dict[str, Any]:
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as exc:
        return {"available": False, "error": f"onnxruntime import failed: {exc}"}
    available = ort.get_available_providers()
    requested = providers or (["CPUExecutionProvider"] if cpu_default and "CPUExecutionProvider" in available else [])
    missing = [x for x in requested if x not in available]
    if missing:
        return {"available": True, "providers_available": available, "error": f"requested provider(s) unavailable: {missing}"}
    try:
        sess = ort.InferenceSession(str(model_path), providers=requested or None)
    except Exception as exc:
        return {"available": True, "providers_available": available, "error": f"InferenceSession failed: {exc}"}

    def one(x: Any) -> dict[str, Any]:
        return {"name": x.name, "type": x.type, "shape": ["?" if d is None else d for d in x.shape]}

    return {
        "available": True,
        "providers_available": available,
        "providers_active": sess.get_providers(),
        "inputs": [one(x) for x in sess.get_inputs()],
        "outputs": [one(x) for x in sess.get_outputs()],
    }


def hint(outputs: list[dict[str, Any]]) -> str:
    names = {str(o.get("name", "")).lower() for o in outputs}
    dtypes = " ".join(str(o.get("dtype", o.get("type", ""))).lower() for o in outputs)
    last_dims = [o.get("shape", [None])[-1] if o.get("shape") else None for o in outputs]
    if {"masks", "scores", "labels"}.issubset(names) or "bool" in dtypes or any("mask" in n for n in names):
        return "SparseInst-like: map masks/scores/labels explicitly and threshold scores."
    if {"boxes", "scores", "labels"} & names or any(d == 6 for d in last_dims):
        return "DETR-like: verify box convention, then rescale boxes to original image size."
    if len(outputs) == 1 and isinstance(last_dims[0], int) and last_dims[0] >= 6:
        return "YOLOX-like dense output: apply grid/stride decode, objectness-class scores, xywh-to-xyxy, and NMS."
    return "Unknown: inspect raw outputs before reusing demo postprocessing."


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model_name = args.model_opt or args.model
    if not model_name:
        print("error: provide model path as positional argument or --model", file=sys.stderr)
        return 2
    model_path = Path(model_name)
    if not model_path.is_file():
        print(f"error: ONNX model not found: {model_path}", file=sys.stderr)
        return 2
    try:
        graph = graph_io(model_path, args.check_model)
    except Exception as exc:
        print(f"error: ONNX graph inspection failed: {exc}", file=sys.stderr)
        return 1
    ort = None if args.no_ort else ort_io(model_path, args.provider, args.providers)
    payload = {"onnx": graph, "onnxruntime": ort, "postprocess_hint": hint(graph["outputs"])}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"model: {graph['path']}")
        print(f"ir_version: {graph['ir_version']}  nodes: {graph['num_nodes']}")
        print(f"opsets: {[(o['domain'], o['version']) for o in graph['opsets']]}")
        print("inputs:")
        for x in graph["inputs"]:
            print(f"  {x['name']}: {x['dtype']} {x['shape']}")
        print("outputs:")
        for x in graph["outputs"]:
            print(f"  {x['name']}: {x['dtype']} {x['shape']}")
        if ort is not None:
            print("onnxruntime:")
            if ort.get("error"):
                print(f"  error: {ort['error']}")
            else:
                print(f"  providers_available: {ort.get('providers_available')}")
                print(f"  providers_active: {ort.get('providers_active')}")
                print(f"  inputs: {ort.get('inputs')}")
                print(f"  outputs: {ort.get('outputs')}")
        print(f"postprocess_hint: {payload['postprocess_hint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
