#!/usr/bin/env python3
"""Check RAGatouille imports and public API signatures without model side effects."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any


TARGETS = [
    ("ragatouille package", "ragatouille", None),
    ("RAGPretrainedModel", "ragatouille", "RAGPretrainedModel"),
    ("RAGTrainer", "ragatouille", "RAGTrainer"),
    ("TrainingDataProcessor", "ragatouille.data", "TrainingDataProcessor"),
    ("CorpusProcessor", "ragatouille.data", "CorpusProcessor"),
    ("LangChain legacy compressor path", "langchain.retrievers.document_compressors.base", "BaseDocumentCompressor"),
    ("LangChain core retriever", "langchain_core.retrievers", "BaseRetriever"),
    ("LangChain core documents", "langchain_core.documents", "Document"),
    ("ColBERT package", "colbert", None),
    ("Torch", "torch", None),
    ("FAISS", "faiss", None),
    ("fast_pytorch_kmeans", "fast_pytorch_kmeans", None),
    ("psutil", "psutil", None),
]

SIGNATURES = [
    ("ragatouille", "RAGPretrainedModel.from_pretrained"),
    ("ragatouille", "RAGPretrainedModel.from_index"),
    ("ragatouille", "RAGPretrainedModel.index"),
    ("ragatouille", "RAGPretrainedModel.search"),
    ("ragatouille", "RAGPretrainedModel.rerank"),
    ("ragatouille", "RAGPretrainedModel.encode"),
    ("ragatouille", "RAGPretrainedModel.search_encoded_docs"),
    ("ragatouille", "RAGTrainer.prepare_training_data"),
    ("ragatouille", "RAGTrainer.train"),
    ("ragatouille.data", "TrainingDataProcessor.process_raw_data"),
]


def check_import(label: str, module_name: str, attr: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"label": label, "module": module_name, "ok": False}
    if attr:
        result["attribute"] = attr
    try:
        module = importlib.import_module(module_name)
        if attr:
            getattr(module, attr)
        result["ok"] = True
        version = getattr(module, "__version__", None)
        if version:
            result["version"] = version
    except Exception as exc:  # noqa: BLE001 - diagnostic utility
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def get_attr(module_name: str, attr_path: str) -> Any:
    obj: Any = importlib.import_module(module_name)
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def check_signature(module_name: str, attr_path: str) -> dict[str, Any]:
    target = f"{module_name}.{attr_path}"
    result: dict[str, Any] = {"target": target, "ok": False}
    try:
        result["signature"] = str(inspect.signature(get_attr(module_name, attr_path)))
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - diagnostic utility
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def torch_backend() -> dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
        cuda = getattr(torch, "cuda", None)
        return {
            "ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(cuda and cuda.is_available()),
            "cuda_device_count": int(cuda.device_count()) if cuda else 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def build_report() -> dict[str, Any]:
    imports = [check_import(*target) for target in TARGETS]
    signatures = [check_signature(*target) for target in SIGNATURES]
    required_imports_ok = all(item["ok"] for item in imports)
    signatures_ok = all(item["ok"] for item in signatures)
    backend = torch_backend()
    return {
        "summary": {
            "ok": bool(required_imports_ok and signatures_ok),
            "required_imports_ok": required_imports_ok,
            "signatures_ok": signatures_ok,
            "model_downloads_attempted": False,
            "training_attempted": False,
            "uploads_attempted": False,
            "network_required": False,
        },
        "imports": imports,
        "signatures": signatures,
        "torch_backend": backend,
    }


def print_text(report: dict[str, Any]) -> None:
    print("RAGatouille environment check")
    print(f"overall ok: {report['summary']['ok']}")
    print("\nImports:")
    for item in report["imports"]:
        label = "ok" if item["ok"] else "FAIL"
        version = f" ({item['version']})" if item.get("version") else ""
        print(f"- {label}: {item['label']}{version}")
        if not item["ok"]:
            print(f"  {item.get('error_type')}: {item.get('error')}")
    print("\nSignatures:")
    for item in report["signatures"]:
        label = "ok" if item["ok"] else "FAIL"
        print(f"- {label}: {item['target']}")
        if item.get("signature"):
            print(f"  {item['signature']}")
        if not item["ok"]:
            print(f"  {item.get('error_type')}: {item.get('error')}")
    backend = report["torch_backend"]
    print("\nTorch backend:")
    if backend["ok"]:
        print(
            f"torch={backend.get('version')} cuda={backend.get('cuda_version')} "
            f"cuda_available={backend.get('cuda_available')} devices={backend.get('cuda_device_count')}"
        )
    else:
        print(f"FAIL {backend.get('error_type')}: {backend.get('error')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check RAGatouille import compatibility, public API signatures, and Torch backend "
            "without loading models, downloading checkpoints, training, or uploading artifacts."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required checks fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and not report["summary"]["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
