#!/usr/bin/env python3
"""Report Ludwig serving/export optional dependencies without starting services."""
import importlib.util
import json

PACKAGES = ["fastapi", "uvicorn", "python_multipart", "prometheus_client", "ray", "kserve", "vllm", "mlflow", "onnx", "huggingface_hub"]


def main() -> int:
    found = {name: bool(importlib.util.find_spec(name)) for name in PACKAGES}
    advice = []
    if not found["fastapi"] or not found["uvicorn"]:
        advice.append("Local ludwig serve needs FastAPI/uvicorn dependencies.")
    if not found["ray"]:
        advice.append("Ray Serve deployment needs Ray with serve support.")
    if not found["kserve"]:
        advice.append("KServe shim needs the kserve package and a serving environment.")
    if not found["vllm"]:
        advice.append("vLLM serving needs vLLM and compatible GPU/model runtime.")
    if not found["onnx"]:
        advice.append("ONNX export may need onnx/onnxruntime dependencies.")
    print(json.dumps({"packages": found, "advice": advice}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
