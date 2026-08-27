#!/usr/bin/env python3
"""
Classify MiniMind model artifacts and print safe conversion plans.

This helper performs path/schema/import checks only. It does not download models,
load large weights, convert checkpoints, start servers, or write output files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt", ".pth")
TRANSFORMERS_INDEX_FILES = ("model.safetensors.index.json", "pytorch_model.bin.index.json")


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def path_info(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"provided": False}
    return {"provided": True, "path": os.fspath(path), "exists": path.exists(), "is_dir": path.is_dir(), "is_file": path.is_file()}


def find_weight_files(model_dir: Path) -> List[str]:
    if not model_dir.is_dir():
        return []
    names = []
    for child in sorted(model_dir.iterdir()):
        if child.is_file() and (child.name in TRANSFORMERS_INDEX_FILES or child.suffix in WEIGHT_SUFFIXES):
            # Raw .pth files can appear in ad-hoc folders, but for a Transformers dir they still count as suspicious weights.
            names.append(child.name)
    return names


def chat_template_features(tokenizer_config: Dict[str, Any]) -> Dict[str, bool]:
    template = tokenizer_config.get("chat_template") or ""
    return {
        "has_chat_template": bool(template),
        "has_think_tags": "<think>" in template and "</think>" in template,
        "has_tool_call_tags": "<tool_call>" in template and "</tool_call>" in template,
        "has_tool_response_tags": "<tool_response>" in template and "</tool_response>" in template,
        "accepts_open_thinking": "open_thinking" in template,
        "mentions_tools": "tools" in template or "<tools>" in template,
    }


def inspect_transformers_dir(model_dir: Optional[Path], expect: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "kind": "transformers",
        "path": path_info(model_dir),
        "artifacts": {},
        "config_summary": {},
        "chat_template_features": {},
        "issues": [],
        "warnings": [],
    }
    if model_dir is None:
        if expect in {"transformers", "qwen3-transformers", "minimind-transformers"}:
            result["issues"].append("--model-dir is required for Transformers artifact checks")
        return result
    if not model_dir.exists():
        result["issues"].append("model directory does not exist")
        return result
    if not model_dir.is_dir():
        result["issues"].append("model path is not a directory")
        return result

    config_path = model_dir / "config.json"
    tok_cfg_path = model_dir / "tokenizer_config.json"
    tokenizer_json_path = model_dir / "tokenizer.json"
    special_tokens_path = model_dir / "special_tokens_map.json"
    generation_config_path = model_dir / "generation_config.json"
    weight_files = find_weight_files(model_dir)

    result["artifacts"] = {
        "config.json": config_path.exists(),
        "tokenizer_config.json": tok_cfg_path.exists(),
        "tokenizer.json": tokenizer_json_path.exists(),
        "special_tokens_map.json": special_tokens_path.exists(),
        "generation_config.json": generation_config_path.exists(),
        "weight_files": weight_files,
    }

    if not config_path.exists():
        result["issues"].append("missing config.json for Transformers-format model")
    else:
        config, error = read_json(config_path)
        if error:
            result["issues"].append(f"config.json is not valid JSON: {error}")
        else:
            assert config is not None
            model_type = config.get("model_type")
            architectures = config.get("architectures") or []
            auto_map = config.get("auto_map") or {}
            result["config_summary"] = {
                "model_type": model_type,
                "architectures": architectures,
                "hidden_size": config.get("hidden_size"),
                "num_hidden_layers": config.get("num_hidden_layers"),
                "use_moe": config.get("use_moe"),
                "rope_scaling": config.get("rope_scaling"),
                "has_auto_map": bool(auto_map),
            }
            model_type_text = str(model_type or "").lower()
            arch_text = " ".join(map(str, architectures)).lower()
            is_qwen3 = "qwen3" in model_type_text or "qwen3" in arch_text
            is_minimind = model_type_text == "minimind" or "minimind" in arch_text or bool(auto_map)
            result["config_summary"]["is_qwen3_compatible"] = is_qwen3
            result["config_summary"]["is_minimind_custom"] = is_minimind
            if expect == "qwen3-transformers" and not is_qwen3:
                result["issues"].append("expected Qwen3-compatible Transformers config but config does not look Qwen3-compatible")
            if expect == "minimind-transformers" and not is_minimind:
                result["issues"].append("expected MiniMind custom Transformers config but config does not look like MiniMind custom format")
            if is_minimind and not is_qwen3:
                result["warnings"].append("MiniMind custom Transformers format may require trust_remote_code=True or installed MiniMind classes")

    if not tokenizer_json_path.exists():
        result["warnings"].append("tokenizer.json not found; tokenizer loading may fail unless another tokenizer source is supplied")
    if not tok_cfg_path.exists():
        result["warnings"].append("tokenizer_config.json not found; chat template features cannot be verified")
    else:
        tok_cfg, error = read_json(tok_cfg_path)
        if error:
            result["issues"].append(f"tokenizer_config.json is not valid JSON: {error}")
        else:
            assert tok_cfg is not None
            features = chat_template_features(tok_cfg)
            result["chat_template_features"] = features
            if not features["has_chat_template"]:
                result["warnings"].append("tokenizer_config.json lacks chat_template")
            if not features["has_think_tags"]:
                result["warnings"].append("chat_template does not advertise complete <think> tags")
            if not features["has_tool_call_tags"]:
                result["warnings"].append("chat_template does not advertise <tool_call> tags")
            if not features["has_tool_response_tags"]:
                result["warnings"].append("chat_template does not advertise <tool_response> tags")

    if not weight_files:
        result["issues"].append("no model weight file or index found in Transformers directory")
    elif any(name.endswith(".pth") for name in weight_files):
        result["warnings"].append(".pth file found in model directory; ensure this is not a raw checkpoint mistaken for Transformers format")

    return result


def raw_checkpoint_name(weight: str, hidden_size: int, moe: bool) -> str:
    return f"{weight}_{hidden_size}{'_moe' if moe else ''}.pth"


def inspect_raw_artifacts(
    weights_dir: Optional[Path],
    tokenizer_dir: Optional[Path],
    weight: str,
    hidden_size: int,
    moe: bool,
    lora_weight: Optional[str],
    expect: str,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "kind": "raw-torch",
        "weights_dir": path_info(weights_dir),
        "tokenizer_dir": path_info(tokenizer_dir),
        "expected": {
            "weight": weight,
            "hidden_size": hidden_size,
            "moe": moe,
            "checkpoint_name": raw_checkpoint_name(weight, hidden_size, moe),
        },
        "artifacts": {},
        "issues": [],
        "warnings": [],
    }
    if weights_dir is None:
        if expect == "raw-torch":
            result["issues"].append("--weights-dir is required for raw torch checks")
        return result
    if not weights_dir.exists():
        result["issues"].append("weights directory does not exist")
        return result
    if not weights_dir.is_dir():
        result["issues"].append("weights path is not a directory")
        return result

    checkpoint = weights_dir / raw_checkpoint_name(weight, hidden_size, moe)
    result["artifacts"]["checkpoint"] = {"path": os.fspath(checkpoint), "exists": checkpoint.exists()}
    if not checkpoint.exists():
        result["issues"].append(f"missing raw checkpoint {checkpoint.name}")

    if tokenizer_dir is None:
        result["warnings"].append("--tokenizer-dir not supplied; raw inference still needs MiniMind tokenizer files")
    else:
        result["artifacts"]["tokenizer"] = {
            "tokenizer_config.json": (tokenizer_dir / "tokenizer_config.json").exists(),
            "tokenizer.json": (tokenizer_dir / "tokenizer.json").exists(),
        }
        if not tokenizer_dir.exists():
            result["issues"].append("tokenizer directory does not exist")
        elif not tokenizer_dir.is_dir():
            result["issues"].append("tokenizer path is not a directory")
        else:
            if not (tokenizer_dir / "tokenizer.json").exists():
                result["warnings"].append("tokenizer.json not found in tokenizer directory")
            tok_cfg = tokenizer_dir / "tokenizer_config.json"
            if tok_cfg.exists():
                data, error = read_json(tok_cfg)
                if error:
                    result["issues"].append(f"tokenizer_config.json is not valid JSON: {error}")
                else:
                    assert data is not None
                    result["chat_template_features"] = chat_template_features(data)
            else:
                result["warnings"].append("tokenizer_config.json not found in tokenizer directory")

    if lora_weight and lora_weight != "None":
        lora_name = raw_checkpoint_name(lora_weight, hidden_size, moe)
        candidates = [weights_dir / lora_name, weights_dir / "lora" / lora_name]
        result["expected"]["lora_checkpoint_name"] = lora_name
        result["artifacts"]["lora_candidates"] = [{"path": os.fspath(path), "exists": path.exists()} for path in candidates]
        if not any(path.exists() for path in candidates):
            result["issues"].append(f"missing LoRA checkpoint; checked {lora_name} and lora/{lora_name}")

    return result


def inspect_imports(expect: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"checks": {}, "issues": [], "warnings": []}
    try:
        import transformers  # type: ignore
        result["checks"]["transformers"] = {"ok": True, "version": getattr(transformers, "__version__", None)}
    except Exception as exc:
        result["checks"]["transformers"] = {"ok": False, "error": str(exc)}
        result["issues"].append("transformers import failed")
        return result

    try:
        from transformers import Qwen3Config, Qwen3ForCausalLM, Qwen3MoeConfig, Qwen3MoeForCausalLM  # noqa: F401
        result["checks"]["qwen3_classes"] = {"ok": True}
    except Exception as exc:
        result["checks"]["qwen3_classes"] = {"ok": False, "error": str(exc)}
        if expect in {"qwen3-transformers", "auto"}:
            result["warnings"].append("Qwen3/Qwen3MoE classes are unavailable; Qwen3-compatible export or serving may fail")

    try:
        import torch  # type: ignore
        result["checks"]["torch"] = {"ok": True, "version": getattr(torch, "__version__", None), "cuda_available": bool(torch.cuda.is_available())}
    except Exception as exc:
        result["checks"]["torch"] = {"ok": False, "error": str(exc)}
        result["warnings"].append("torch import failed; artifact checks can continue but inference cannot")

    return result


def conversion_plan(args: argparse.Namespace, raw: Dict[str, Any], tfm: Dict[str, Any]) -> Dict[str, Any]:
    weight_name = raw_checkpoint_name(args.weight, args.hidden_size, args.moe)
    lora_name = raw_checkpoint_name(args.lora_weight, args.hidden_size, args.moe) if args.lora_weight and args.lora_weight != "None" else None
    return {
        "performs_conversion": False,
        "raw_to_qwen3_transformers": {
            "when": "Use for vLLM, SGLang, llama.cpp/GGUF, Ollama, or any runtime that should not depend on MiniMind custom code.",
            "preconditions": [
                f"Raw checkpoint exists: WEIGHTS_DIR/{weight_name}",
                "Tokenizer directory contains tokenizer.json and tokenizer_config.json",
                "MiniMindConfig dimensions match checkpoint",
                "Transformers exposes Qwen3 and Qwen3MoE classes for the selected dense/MoE export",
            ],
            "template": [
                "Create MiniMindConfig(hidden_size=HIDDEN_SIZE, num_hidden_layers=LAYERS, use_moe=MOE).",
                "Load torch state_dict from WEIGHTS_DIR/<weight>_<hidden_size>[_moe].pth.",
                "Create Qwen3ForCausalLM for dense or Qwen3MoeForCausalLM for MoE with matching dimensions.",
                "Remap MoE expert tensors if required by the installed Transformers version.",
                "Load state_dict strictly, save_pretrained(EXPORT_DIR), and save tokenizer to EXPORT_DIR.",
                "Re-run this checker with --model-dir EXPORT_DIR --expect qwen3-transformers --check-imports.",
            ],
        },
        "raw_to_minimind_transformers": {
            "when": "Use when preserving MiniMind custom model identity is acceptable and consumers can use trust_remote_code or installed MiniMind classes.",
            "template": [
                "Register MiniMindConfig and MiniMindForCausalLM for auto classes.",
                "Load raw state_dict into MiniMindForCausalLM with matching config.",
                "save_pretrained(EXPORT_DIR) and save tokenizer files.",
                "Consumers should load with trust_remote_code=True unless the classes are installed.",
            ],
        },
        "merge_lora_then_export": {
            "when": "Use before portable serving if --lora-weight is set.",
            "lora_checkpoint": lora_name,
            "template": [
                "Load raw base checkpoint with matching MiniMindConfig.",
                "Apply LoRA modules, load LoRA checkpoint, and merge low-rank delta into base weights.",
                "Save a new full raw checkpoint such as merged_<name>_<hidden_size>[_moe].pth.",
                "Export the merged raw checkpoint to Qwen3-compatible Transformers format.",
            ],
        },
        "transformers_to_raw_torch": {
            "when": "Use only when a downstream raw MiniMind workflow specifically requires .pth.",
            "template": [
                "AutoModelForCausalLM.from_pretrained(MODEL_DIR, trust_remote_code=True).",
                "Save {k: v.cpu().half() for k, v in model.state_dict().items()} to WEIGHTS_DIR/<weight>_<hidden_size>[_moe].pth.",
            ],
        },
        "current_artifact_hints": {
            "raw_checkpoint_present": bool(raw.get("artifacts", {}).get("checkpoint", {}).get("exists")),
            "transformers_weight_files": tfm.get("artifacts", {}).get("weight_files", []),
        },
    }


def combine_status(result: Dict[str, Any]) -> None:
    issues: List[str] = []
    warnings: List[str] = []
    for section in ("transformers", "raw_torch", "imports"):
        data = result.get(section)
        if isinstance(data, dict):
            issues.extend(data.get("issues", []))
            warnings.extend(data.get("warnings", []))
    result["issues"] = issues
    result["warnings"] = warnings
    result["ok"] = not issues
    result["status"] = "ok" if not issues and not warnings else ("warning" if not issues else "error")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MiniMind model artifacts without loading weights or writing files.")
    parser.add_argument("--model-dir", type=Path, help="Transformers-format model directory to inspect.")
    parser.add_argument("--weights-dir", type=Path, help="Raw MiniMind .pth checkpoint directory to inspect.")
    parser.add_argument("--tokenizer-dir", type=Path, help="Tokenizer directory used with raw MiniMind checkpoints.")
    parser.add_argument(
        "--expect",
        choices=["auto", "transformers", "qwen3-transformers", "minimind-transformers", "raw-torch"],
        default="auto",
        help="Artifact type expected by the caller. Default: auto.",
    )
    parser.add_argument("--weight", default="full_sft", help="Raw checkpoint prefix. Default: full_sft.")
    parser.add_argument("--hidden-size", type=int, default=768, help="Raw checkpoint hidden size. Default: 768.")
    moe_group = parser.add_mutually_exclusive_group()
    moe_group.add_argument("--moe", dest="moe", action="store_true", help="Expect MoE raw checkpoint suffix.")
    moe_group.add_argument("--no-moe", dest="moe", action="store_false", help="Expect dense raw checkpoint without MoE suffix. Default.")
    parser.set_defaults(moe=False)
    parser.add_argument("--lora-weight", help="Optional LoRA checkpoint prefix to check, such as lora_identity.")
    parser.add_argument("--check-imports", action="store_true", help="Also import transformers/torch and Qwen3 classes. Does not load model weights.")
    parser.add_argument("--print-conversion-plan", action="store_true", help="Include safe conversion/export plan templates. Does not convert.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON. Pretty summary is used otherwise.")
    return parser


def pretty_print(result: Dict[str, Any]) -> None:
    print(f"Status: {result['status']} (ok={result['ok']})")
    if result.get("issues"):
        print("Issues:")
        for issue in result["issues"]:
            print(f"- {issue}")
    if result.get("warnings"):
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    print("\nTransformers artifacts:")
    print(dumps(result.get("transformers", {}).get("artifacts", {})))
    print("\nRaw artifacts:")
    print(dumps(result.get("raw_torch", {}).get("artifacts", {})))
    if result.get("imports"):
        print("\nImport checks:")
        print(dumps(result["imports"].get("checks", {})))
    if result.get("conversion_plan"):
        print("\nConversion plan:")
        print(dumps(result["conversion_plan"]))


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result: Dict[str, Any] = {
        "expect": args.expect,
        "transformers": inspect_transformers_dir(args.model_dir, args.expect),
        "raw_torch": inspect_raw_artifacts(args.weights_dir, args.tokenizer_dir, args.weight, args.hidden_size, args.moe, args.lora_weight, args.expect),
    }

    if args.expect == "auto" and args.model_dir is None and args.weights_dir is None:
        result.setdefault("raw_torch", {}).setdefault("warnings", []).append("no --model-dir or --weights-dir supplied; only help/plan output is meaningful")
    if args.check_imports:
        result["imports"] = inspect_imports(args.expect)
    if args.print_conversion_plan:
        result["conversion_plan"] = conversion_plan(args, result["raw_torch"], result["transformers"])

    combine_status(result)
    if args.json:
        print(dumps(result))
    else:
        pretty_print(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
