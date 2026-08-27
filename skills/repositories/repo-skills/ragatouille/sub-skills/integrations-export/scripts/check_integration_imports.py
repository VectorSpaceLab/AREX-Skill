#!/usr/bin/env python3
"""Check RAGatouille integration/export imports without downloads or uploads."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
HF_TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN")


def check_import(name: str, module: str, attr: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "module": module, "ok": False}
    if attr:
        result["attribute"] = attr
    try:
        imported = importlib.import_module(module)
        if attr:
            getattr(imported, attr)
        result["ok"] = True
        version = getattr(imported, "__version__", None)
        if version:
            result["version"] = version
    except Exception as exc:  # noqa: BLE001 - diagnostics should capture import failures
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def signature_for(module: str, attr_path: str) -> dict[str, Any]:
    result: dict[str, Any] = {"target": f"{module}.{attr_path}", "ok": False}
    try:
        obj: Any = importlib.import_module(module)
        for part in attr_path.split("."):
            obj = getattr(obj, part)
        result["signature"] = str(inspect.signature(obj))
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def inspect_path(path_arg: str) -> dict[str, Any]:
    path = Path(path_arg).expanduser()
    result: dict[str, Any] = {
        "input": path_arg,
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }
    if not path.exists():
        result["ok"] = False
        result["message"] = "Path does not exist."
        return result

    candidates = {
        "config_json": path / "config.json",
        "tokenizer_json": path / "tokenizer.json",
        "artifact_metadata": path / "artifact.metadata",
        "model_safetensors": path / "model.safetensors",
        "pytorch_model_bin": path / "pytorch_model.bin",
    }
    result["files"] = {name: candidate.exists() for name, candidate in candidates.items()}
    result["has_fast_tokenizer_file"] = bool(result["files"]["tokenizer_json"])
    result["has_common_model_weight_file"] = bool(
        result["files"]["model_safetensors"] or result["files"]["pytorch_model_bin"]
    )
    result["maybe_colbert_checkpoint"] = bool(
        result["files"]["config_json"] or result["files"]["artifact_metadata"]
    )
    result["ok"] = bool(result["is_dir"] and result["maybe_colbert_checkpoint"])
    if not result["ok"]:
        result["message"] = (
            "Path exists, but does not look like a local ColBERT checkpoint directory "
            "from lightweight file checks."
        )
    return result


def inspect_repo_name(repo: str) -> dict[str, Any]:
    ok = bool(REPO_PATTERN.match(repo))
    return {
        "input": repo,
        "ok": ok,
        "message": "Repo name matches 'owner/repo-name'." if ok else "Expected Hugging Face model repo format 'owner/repo-name'.",
    }


def inspect_hf_auth() -> dict[str, Any]:
    present_env = [name for name in HF_TOKEN_ENV_NAMES if os.environ.get(name)]
    result: dict[str, Any] = {
        "ok": bool(present_env),
        "token_env_present": present_env,
        "checked_env_names": list(HF_TOKEN_ENV_NAMES),
        "network_used": False,
    }
    try:
        from huggingface_hub import HfFolder  # type: ignore

        result["cached_token_present"] = bool(HfFolder.get_token())
        result["ok"] = bool(result["ok"] or result["cached_token_present"])
    except Exception as exc:  # noqa: BLE001
        result["cached_token_check_error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    imports = [
        check_import("langchain legacy compressor path", "langchain.retrievers.document_compressors.base", "BaseDocumentCompressor"),
        check_import("langchain core documents", "langchain_core.documents", "Document"),
        check_import("langchain core retriever", "langchain_core.retrievers", "BaseRetriever"),
        check_import("ragatouille package", "ragatouille"),
        check_import("ragatouille pretrained model", "ragatouille", "RAGPretrainedModel"),
        check_import("ragatouille langchain integrations", "ragatouille.integrations"),
        check_import("export helpers", "ragatouille.models.utils"),
        check_import("llama_index legacy package", "llama_index"),
        check_import("llama_index core package", "llama_index.core"),
        check_import("huggingface_hub", "huggingface_hub", "HfApi"),
        check_import("onnx", "onnx"),
    ]

    signatures = [
        signature_for("ragatouille", "RAGPretrainedModel.as_langchain_retriever"),
        signature_for("ragatouille", "RAGPretrainedModel.as_langchain_document_compressor"),
        signature_for("ragatouille.models.utils", "export_to_huggingface_hub"),
        signature_for("ragatouille.models.utils", "export_to_vespa_onnx"),
    ]

    report: dict[str, Any] = {
        "summary": {
            "network_used": False,
            "uploads_attempted": False,
            "model_downloads_attempted": False,
            "strict": args.strict,
        },
        "imports": imports,
        "signatures": signatures,
    }

    if args.repo:
        report["huggingface_repo"] = inspect_repo_name(args.repo)
    if args.require_hf_auth:
        report["huggingface_auth"] = inspect_hf_auth()
    if args.check_path:
        report["path"] = inspect_path(args.check_path)

    required_names = {
        "langchain legacy compressor path",
        "langchain core documents",
        "langchain core retriever",
        "ragatouille package",
        "ragatouille pretrained model",
        "ragatouille langchain integrations",
        "export helpers",
    }
    required_imports_ok = all(item["ok"] for item in imports if item["name"] in required_names)
    required_signatures_ok = all(item["ok"] for item in signatures)
    optional_ok = True
    if args.repo:
        optional_ok = bool(optional_ok and report["huggingface_repo"]["ok"])
    if args.require_hf_auth:
        optional_ok = bool(optional_ok and report["huggingface_auth"]["ok"])
    if args.check_path:
        optional_ok = bool(optional_ok and report["path"]["ok"])

    report["summary"].update(
        {
            "required_imports_ok": required_imports_ok,
            "required_signatures_ok": required_signatures_ok,
            "optional_checks_ok": optional_ok,
            "ok": bool(required_imports_ok and required_signatures_ok and optional_ok),
        }
    )
    return report


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("RAGatouille integration/export compatibility check")
    print(f"overall ok: {summary['ok']}")
    print(f"network used: {summary['network_used']}")
    print(f"uploads attempted: {summary['uploads_attempted']}")
    print(f"model downloads attempted: {summary['model_downloads_attempted']}")
    print("\nImports:")
    for item in report["imports"]:
        label = "ok" if item["ok"] else "FAIL"
        version = f" ({item['version']})" if item.get("version") else ""
        print(f"- {label}: {item['name']}{version}")
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
    if "huggingface_repo" in report:
        repo = report["huggingface_repo"]
        print(f"\nHugging Face repo shape: {'ok' if repo['ok'] else 'FAIL'} ({repo['input']})")
    if "huggingface_auth" in report:
        auth = report["huggingface_auth"]
        print(f"Hugging Face auth indicator: {'ok' if auth['ok'] else 'missing'}")
        if auth.get("token_env_present"):
            print(f"token env names present: {', '.join(auth['token_env_present'])}")
        print(f"cached token present: {auth.get('cached_token_present', False)}")
    if "path" in report:
        path = report["path"]
        print(f"\nCheckpoint/export path: {'ok' if path['ok'] else 'WARN'} ({path['input']})")
        print(f"exists: {path['exists']} dir: {path['is_dir']}")
        if path.get("files"):
            for name, exists in path["files"].items():
                print(f"- {name}: {exists}")
        if path.get("message"):
            print(path["message"])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check RAGatouille LangChain/LlamaIndex/export imports and optional "
            "Hugging Face/path preflight facts without downloads, uploads, or model loads."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable text.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required imports/signatures or requested optional checks fail.")
    parser.add_argument("--repo", help="Validate a Hugging Face model repo name such as 'owner/repo-name'.")
    parser.add_argument("--require-hf-auth", action="store_true", help="Require a local Hugging Face token indicator without making network calls.")
    parser.add_argument("--check-path", help="Inspect a local checkpoint/export directory with lightweight file checks only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and not report["summary"]["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
