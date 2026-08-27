#!/usr/bin/env python3
"""Validate local SaProt model assets without downloading weights."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Dict, List


OPTIONAL_PACKAGES = {
    "torch": "required for all SaProt model execution and .pt checkpoints",
    "transformers": "required for Hugging Face EsmTokenizer/EsmForMaskedLM loading",
    "esm": "provided by fair-esm; required for utils.esm_loader.load_esm_saprot",
    "peft": "required only for LoRA adapter loading or setup",
}

HF_CONFIG_FILES = ("config.json",)
HF_TOKENIZER_HINTS = (
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.txt",
    "tokenizer.json",
    "vocab.json",
    "merges.txt",
)
HF_WEIGHT_HINTS = (
    "pytorch_model.bin",
    "model.safetensors",
    "pytorch_model.bin.index.json",
    "model.safetensors.index.json",
)


def package_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def dependency_report() -> Dict[str, Dict[str, Any]]:
    return {
        name: {
            "available": package_available(name),
            "guidance": guidance,
        }
        for name, guidance in OPTIONAL_PACKAGES.items()
    }


def infer_kind(path: Path) -> str:
    if path.is_dir():
        return "hf-dir"
    if path.is_file() and path.suffix == ".pt":
        return "esm-pt"
    if path.is_file():
        return "file"
    return "missing"


def list_present(directory: Path, filenames: tuple[str, ...]) -> List[str]:
    return [name for name in filenames if (directory / name).exists()]


def has_sharded_weights(directory: Path) -> List[str]:
    patterns = ("pytorch_model-*.bin", "model-*.safetensors")
    matches: List[str] = []
    for pattern in patterns:
        matches.extend(path.name for path in sorted(directory.glob(pattern)))
    return matches


def validate_hf_dir(path: Path) -> Dict[str, Any]:
    config_files = list_present(path, HF_CONFIG_FILES)
    tokenizer_files = list_present(path, HF_TOKENIZER_HINTS)
    weight_files = list_present(path, HF_WEIGHT_HINTS)
    sharded_weights = has_sharded_weights(path)

    missing: List[str] = []
    if not config_files:
        missing.append("config.json")
    if not tokenizer_files:
        missing.append("tokenizer metadata such as tokenizer_config.json, vocab.txt, or tokenizer.json")
    if not weight_files and not sharded_weights:
        missing.append("model weights such as pytorch_model.bin, model.safetensors, or shard files")

    return {
        "kind": "hf-dir",
        "ok": not missing,
        "present": {
            "config": config_files,
            "tokenizer": tokenizer_files,
            "weights": weight_files,
            "sharded_weights": sharded_weights,
        },
        "missing": missing,
    }


def validate_esm_pt(path: Path) -> Dict[str, Any]:
    return {
        "kind": "esm-pt",
        "ok": path.is_file() and path.suffix == ".pt",
        "suffix": path.suffix,
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "missing": [] if path.is_file() and path.suffix == ".pt" else ["local .pt checkpoint file"],
    }


def try_tokenizer(path: Path) -> Dict[str, Any]:
    if not package_available("transformers"):
        return {"attempted": False, "ok": False, "error": "transformers is not installed"}

    try:
        from transformers import EsmTokenizer  # type: ignore

        tokenizer = EsmTokenizer.from_pretrained(str(path), local_files_only=True)
        sample_tokens = tokenizer.tokenize("M#EvVp")
        return {
            "attempted": True,
            "ok": True,
            "class": type(tokenizer).__name__,
            "sample_tokens": sample_tokens,
        }
    except Exception as exc:  # pragma: no cover - depends on local model assets
        return {"attempted": True, "ok": False, "error": repr(exc)}


def build_report(path: Path, requested_kind: str, try_tokenizer_flag: bool) -> Dict[str, Any]:
    actual_kind = infer_kind(path)
    kind = actual_kind if requested_kind == "auto" else requested_kind

    report: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "actual_kind": actual_kind,
        "requested_kind": requested_kind,
        "dependencies": dependency_report(),
        "validation": {},
        "guidance": [],
    }

    if not path.exists():
        report["validation"] = {"ok": False, "missing": ["path does not exist"]}
        report["guidance"].append("Provide a local Hugging Face model directory or local .pt checkpoint path.")
        return report

    if kind == "hf-dir":
        if not path.is_dir():
            report["validation"] = {"kind": "hf-dir", "ok": False, "missing": ["directory path"]}
            report["guidance"].append("Hugging Face loading expects a model directory, not a .pt file.")
        else:
            report["validation"] = validate_hf_dir(path)
            if try_tokenizer_flag:
                report["tokenizer_check"] = try_tokenizer(path)
        report["guidance"].append("Use this path with EsmTokenizer/EsmForMaskedLM or SaProt model wrapper config_path.")
    elif kind == "esm-pt":
        report["validation"] = validate_esm_pt(path)
        report["guidance"].append("Use this path with utils.esm_loader.load_esm_saprot.")
    else:
        report["validation"] = {"kind": kind, "ok": False, "missing": ["recognized asset kind"]}
        report["guidance"].append("Use --kind hf-dir for a model directory or --kind esm-pt for a .pt checkpoint.")

    if actual_kind == "hf-dir" and requested_kind == "esm-pt":
        report["guidance"].append("A directory was provided but .pt loading was requested.")
    if actual_kind == "esm-pt" and requested_kind == "hf-dir":
        report["guidance"].append("A .pt file was provided but Hugging Face directory loading was requested.")

    return report


def print_text_report(report: Dict[str, Any]) -> None:
    print(f"Path: {report['path']}")
    print(f"Exists: {report['exists']}")
    print(f"Detected kind: {report['actual_kind']}")
    print(f"Requested kind: {report['requested_kind']}")

    validation = report.get("validation", {})
    print(f"Validation ok: {validation.get('ok', False)}")
    if validation.get("missing"):
        print("Missing:")
        for item in validation["missing"]:
            print(f"  - {item}")

    present = validation.get("present")
    if present:
        print("Present assets:")
        for group, names in present.items():
            joined = ", ".join(names) if names else "none detected"
            print(f"  - {group}: {joined}")

    tokenizer_check = report.get("tokenizer_check")
    if tokenizer_check:
        print(f"Tokenizer check ok: {tokenizer_check.get('ok', False)}")
        if tokenizer_check.get("sample_tokens"):
            print(f"Tokenizer sample tokens: {tokenizer_check['sample_tokens']}")
        if tokenizer_check.get("error"):
            print(f"Tokenizer error: {tokenizer_check['error']}")

    print("Optional dependency guidance:")
    for name, info in report["dependencies"].items():
        status = "available" if info["available"] else "missing"
        print(f"  - {name}: {status}; {info['guidance']}")

    if report.get("guidance"):
        print("Guidance:")
        for item in report["guidance"]:
            print(f"  - {item}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local SaProt Hugging Face directories or ESM .pt checkpoints without downloading weights.",
    )
    parser.add_argument("path", help="Local model directory or .pt checkpoint path to validate.")
    parser.add_argument(
        "--kind",
        choices=("auto", "hf-dir", "esm-pt"),
        default="auto",
        help="Expected asset kind. Defaults to auto-detecting from the path.",
    )
    parser.add_argument(
        "--try-tokenizer",
        action="store_true",
        help="Attempt EsmTokenizer.from_pretrained with local_files_only=True for Hugging Face directories.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(os.path.expanduser(args.path)).resolve()
    report = build_report(path, args.kind, args.try_tokenizer)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report.get("validation", {}).get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
