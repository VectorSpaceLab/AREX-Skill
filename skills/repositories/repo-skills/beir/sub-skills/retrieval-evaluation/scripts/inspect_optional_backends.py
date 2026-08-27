#!/usr/bin/env python3
"""Inspect optional BEIR retrieval backends without contacting services."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sys
from importlib import metadata
from typing import Any


PACKAGE_CANDIDATES = {
    "faiss": ["faiss", "faiss-cpu", "faiss-gpu"],
    "elasticsearch": ["elasticsearch"],
    "cohere": ["cohere"],
    "voyageai": ["voyageai", "voyage"],
    "vllm": ["vllm"],
    "peft": ["peft"],
    "llm2vec": ["llm2vec"],
}

ENV_SIGNALS = {
    "cohere": ["COHERE_API_KEY"],
    "voyageai": ["VOYAGE_API_KEY", "VOYAGEAI_API_KEY"],
    "huggingface": ["HF_HOME", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"],
}


def distribution_version(distribution_names: list[str]) -> str | None:
    for distribution_name in distribution_names:
        try:
            return metadata.version(distribution_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def module_report(module_name: str, distribution_names: list[str]) -> dict[str, Any]:
    spec = importlib.util.find_spec(module_name)
    return {
        "present": spec is not None,
        "version": distribution_version(distribution_names),
    }


def env_report(names: list[str]) -> dict[str, bool]:
    return {name: bool(os.getenv(name)) for name in names}


def torch_report() -> dict[str, Any]:
    spec = importlib.util.find_spec("torch")
    report: dict[str, Any] = {
        "present": spec is not None,
        "version": distribution_version(["torch"]),
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_version": None,
    }
    if spec is None:
        return report

    try:
        import torch

        report.update(
            {
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
                "cuda_version": torch.version.cuda,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive environment probe
        report["probe_error"] = repr(exc)
    return report


def build_report() -> dict[str, Any]:
    packages = {
        module_name: module_report(module_name, distribution_names)
        for module_name, distribution_names in PACKAGE_CANDIDATES.items()
    }
    packages["torch"] = torch_report()

    return {
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "packages": packages,
        "environment_signals": {name: env_report(names) for name, names in ENV_SIGNALS.items()},
        "notes": [
            "This script performs import and environment-variable checks only.",
            "BM25 still requires a reachable Elasticsearch-compatible service even when elasticsearch imports.",
            "API wrappers still require valid credentials, network access, provider quota, and accepted costs.",
            "FAISS GPU availability depends on the installed FAISS build and hardware, not only torch CUDA.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']['implementation']} {report['python']['version']} on {report['python']['platform']}")
    print("\nPackages:")
    for name, info in sorted(report["packages"].items()):
        version = info.get("version") or "unknown"
        status = "present" if info.get("present") else "missing"
        extras = []
        if name == "torch":
            extras.append(f"cuda_available={info.get('cuda_available')}")
            extras.append(f"cuda_device_count={info.get('cuda_device_count')}")
            if info.get("cuda_version"):
                extras.append(f"cuda_version={info.get('cuda_version')}")
        if info.get("probe_error"):
            extras.append(f"probe_error={info['probe_error']}")
        extra_text = f" ({', '.join(extras)})" if extras else ""
        print(f"- {name}: {status}, version={version}{extra_text}")

    print("\nEnvironment signals:")
    for group, values in sorted(report["environment_signals"].items()):
        rendered = ", ".join(f"{key}={'set' if value else 'unset'}" for key, value in sorted(values.items()))
        print(f"- {group}: {rendered}")

    print("\nNotes:")
    for note in report["notes"]:
        print(f"- {note}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect optional BEIR retrieval dependencies without service calls.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
