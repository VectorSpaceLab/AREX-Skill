#!/usr/bin/env python
"""Check a Python environment for text2vec workflows without downloading models.

Examples:
  python check_text2vec_env.py
  python check_text2vec_env.py --expect-cuda
  python check_text2vec_env.py --local-model /path/to/local/hf-model
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"ok": True, "module": module, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"ok": False, "module": module, "error": f"{type(exc).__name__}: {exc}"}


def check_text2vec_api(local_model: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        from text2vec import BM25, EncoderType, SentenceModel, cos_sim, semantic_search
        import torch

        result["encoder_types"] = [e.name for e in EncoderType]
        scores = BM25(["hello world", "文本 测试"]).get_scores("hello", top_k=1)
        result["bm25_top"] = scores[0][0] if scores else None
        a = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        b = torch.tensor([[1.0, 0.0], [1.0, 1.0]])
        result["cos_sim_shape"] = list(cos_sim(a, b).shape)
        result["semantic_search_first"] = semantic_search(a, b, top_k=1)[0][0]
        if local_model:
            model_path = Path(local_model)
            if not model_path.exists():
                result["local_model"] = {"ok": False, "error": "path does not exist"}
            else:
                model = SentenceModel(str(model_path), device="cpu", max_seq_length=16)
                emb = model.encode(["hello", "world"], show_progress_bar=False)
                result["local_model"] = {"ok": True, "embedding_shape": list(emb.shape)}
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a text2vec environment without downloading default models.")
    parser.add_argument("--expect-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--local-model", help="Optional local HF-compatible model directory for a no-network SentenceModel smoke test.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in [
            "text2vec", "torch", "transformers", "datasets", "pandas", "scikit-learn", "jieba",
            "gensim", "kenlm", "fastapi", "uvicorn", "jina", "gradio", "sentence-transformers"
        ]},
        "imports": {module: import_status(module) for module in [
            "text2vec", "torch", "transformers", "datasets", "pandas", "sklearn", "jieba"
        ]},
        "optional_imports": {module: import_status(module) for module in [
            "gensim", "kenlm", "fastapi", "uvicorn", "jina", "gradio", "sentence_transformers"
        ]},
        "torch_backend": {},
        "text2vec_api": {},
        "ok": True,
        "errors": [],
        "warnings": [],
    }

    try:
        import torch

        report["torch_backend"] = {
            "version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        }
        if args.expect_cuda and not torch.cuda.is_available():
            report["ok"] = False
            report["errors"].append("--expect-cuda was set but torch.cuda.is_available() is false.")
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["errors"].append(f"torch import/backend check failed: {type(exc).__name__}: {exc}")

    for module, status in report["imports"].items():
        if not status["ok"]:
            report["ok"] = False
            report["errors"].append(f"required import failed: {module}: {status.get('error')}")

    report["text2vec_api"] = check_text2vec_api(args.local_model)
    if "error" in report["text2vec_api"]:
        report["ok"] = False
        report["errors"].append(f"text2vec API smoke failed: {report['text2vec_api']['error']}")

    if not report["optional_imports"]["gensim"]["ok"]:
        report["warnings"].append("Word2Vec needs optional gensim plus a local or downloaded word2vec file.")
    if not report["optional_imports"]["kenlm"]["ok"]:
        report["warnings"].append("NGram needs optional kenlm plus a large language-model file.")
    if not (report["optional_imports"]["fastapi"]["ok"] and report["optional_imports"]["uvicorn"]["ok"]):
        report["warnings"].append("FastAPI serving needs optional fastapi and uvicorn.")

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
