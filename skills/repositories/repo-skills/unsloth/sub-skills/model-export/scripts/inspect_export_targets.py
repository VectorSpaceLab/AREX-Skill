#!/usr/bin/env python3
"""Static preflight for Unsloth checkpoint export targets.

This helper validates paths, format choices, tokenizer artifacts, optional Hub
flags, and GGUF tool availability without importing Unsloth, loading a model,
contacting the network, creating output directories, or running converters.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path, PureWindowsPath
from typing import Any


EXPORT_FORMATS = {"lora", "merged-16bit", "merged-4bit", "gguf", "base"}
CLI_EXPORT_FORMATS = {"lora", "merged-16bit", "merged-4bit", "gguf"}
GGUF_QUANTS = {
    "not_quantized",
    "fast_quantized",
    "quantized",
    "f32",
    "bf16",
    "f16",
    "q8_0",
    "q4_k_m",
    "q5_k_m",
    "q2_k",
    "q2_k_l",
    "q3_k_l",
    "q3_k_m",
    "q3_k_s",
    "q4_0",
    "q4_1",
    "q4_k_s",
    "q4_k",
    "q5_k",
    "q5_0",
    "q5_1",
    "q5_k_s",
    "q6_k",
    "q3_k_xs",
}
CLI_GGUF_QUANTS = {"q4_k_m", "q5_k_m", "q8_0", "f16"}
TOKENIZER_FILES = {
    "tokenizer_config.json",
    "tokenizer.json",
    "special_tokens_map.json",
    "tokenizer.model",
    "vocab.json",
    "merges.txt",
    "chat_template.json",
    "preprocessor_config.json",
}
REPO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")


def _empty_result() -> dict[str, Any]:
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "info": [],
        "checkpoint": {},
        "output": {},
        "format": {},
        "hub": {},
        "tools": {},
        "commands": [],
        "checkpoints": [],
    }


def _add_error(result: dict[str, Any], message: str) -> None:
    result["errors"].append(message)
    result["ok"] = False


def _add_warning(result: dict[str, Any], message: str) -> None:
    result["warnings"].append(message)


def _add_info(result: dict[str, Any], message: str) -> None:
    result["info"].append(message)


def _raw_path_parts(raw_value: str) -> list[str]:
    normalized = raw_value.replace("\\", "/")
    parts: list[str] = []
    parts.extend(Path(raw_value).expanduser().parts)
    parts.extend(PureWindowsPath(raw_value).parts)
    parts.extend(normalized.split("/"))
    return parts


def validate_save_directory(raw_value: str, result: dict[str, Any]) -> dict[str, Any]:
    details: dict[str, Any] = {"raw": raw_value}
    if raw_value is None:
        _add_error(result, "output directory is required")
        return details

    raw_text = str(raw_value).strip()
    details["raw"] = raw_text
    if not raw_text:
        _add_error(result, "output directory must not be empty")
        return details
    if "\x00" in raw_text:
        _add_error(result, "output directory may not contain null bytes")
    if any(control in raw_text for control in ("\r", "\n")):
        _add_error(result, "output directory may not contain CR/LF control characters")

    path_parts = _raw_path_parts(raw_text)
    if any(part == ".." for part in path_parts):
        _add_error(result, "output directory may not contain '..' segments")
    long_parts = [part for part in path_parts if part not in ("", ".", "/", "\\") and len(part) > 255]
    if long_parts:
        _add_error(result, "output directory has path component(s) longer than 255 characters")

    output_path = Path(raw_text).expanduser()
    details["expanded"] = str(output_path)
    try:
        details["resolved"] = str(output_path.resolve(strict=False))
    except OSError as exc:
        _add_error(result, f"could not resolve output directory: {exc}")
    return details


def validate_checkpoint_string(raw_value: str, result: dict[str, Any]) -> None:
    if raw_value is None or not str(raw_value).strip():
        _add_error(result, "checkpoint is required")
        return
    raw_text = str(raw_value).strip()
    if "\x00" in raw_text:
        _add_error(result, "checkpoint path may not contain null bytes")
    if any(control in raw_text for control in ("\r", "\n")):
        _add_error(result, "checkpoint path may not contain CR/LF control characters")
    if any(part == ".." for part in _raw_path_parts(raw_text)):
        _add_error(result, "checkpoint path may not contain '..' segments")


def _looks_like_remote_repo(raw_value: str) -> bool:
    return REPO_ID_RE.match(raw_value.strip()) is not None and not Path(raw_value).expanduser().exists()


def _safe_read_json(json_path: Path) -> dict[str, Any]:
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _glob_names(directory: Path, patterns: list[str]) -> list[str]:
    names: set[str] = set()
    for pattern in patterns:
        for candidate in directory.glob(pattern):
            if candidate.is_file():
                names.add(candidate.name)
    return sorted(names)


def inspect_checkpoint(raw_value: str, result: dict[str, Any]) -> dict[str, Any]:
    details: dict[str, Any] = {"raw": raw_value, "kind": "unknown"}
    validate_checkpoint_string(raw_value, result)
    raw_text = str(raw_value).strip()
    if not raw_text:
        return details

    if _looks_like_remote_repo(raw_text):
        details.update({"kind": "remote_repo", "repo_id": raw_text})
        _add_warning(result, "remote checkpoint/repo id was not inspected locally; verify adapter/tokenizer files before export")
        return details

    checkpoint_path = Path(raw_text).expanduser()
    details["expanded"] = str(checkpoint_path)
    try:
        details["resolved"] = str(checkpoint_path.resolve(strict=False))
    except OSError as exc:
        _add_error(result, f"could not resolve checkpoint path: {exc}")

    if not checkpoint_path.exists():
        _add_error(result, f"checkpoint path does not exist: {checkpoint_path}")
        return details

    if checkpoint_path.is_file():
        details["kind"] = "gguf_file" if checkpoint_path.suffix.lower() == ".gguf" else "file"
        if checkpoint_path.suffix.lower() != ".gguf":
            _add_error(result, "checkpoint is a file, not a directory or .gguf artifact")
        return details

    if not checkpoint_path.is_dir():
        _add_error(result, "checkpoint path is neither a directory nor a regular file")
        return details

    adapter_config = checkpoint_path / "adapter_config.json"
    config_json = checkpoint_path / "config.json"
    trainer_state = checkpoint_path / "trainer_state.json"
    tokenizer_names = sorted(name for name in TOKENIZER_FILES if (checkpoint_path / name).is_file())
    weight_names = _glob_names(
        checkpoint_path,
        [
            "adapter_model*.safetensors",
            "adapter_model*.bin",
            "model*.safetensors",
            "pytorch_model*.bin",
            "*.safetensors",
            "*.bin",
        ],
    )
    gguf_names = _glob_names(checkpoint_path, ["*.gguf"])

    details.update(
        {
            "kind": "directory",
            "has_adapter_config": adapter_config.is_file(),
            "has_config_json": config_json.is_file(),
            "has_trainer_state": trainer_state.is_file(),
            "tokenizer_files": tokenizer_names,
            "weight_files": weight_names,
            "gguf_files": gguf_names,
            "is_peft_lora": adapter_config.is_file(),
            "is_full_or_base_model": config_json.is_file() and not adapter_config.is_file(),
        }
    )

    if adapter_config.is_file():
        adapter_data = _safe_read_json(adapter_config)
        details["adapter_metadata"] = {
            "base_model_name_or_path": adapter_data.get("base_model_name_or_path"),
            "peft_type": adapter_data.get("peft_type"),
            "r": adapter_data.get("r"),
        }
    if config_json.is_file():
        config_data = _safe_read_json(config_json)
        details["config_metadata"] = {
            "model_type": config_data.get("model_type"),
            "_name_or_path": config_data.get("_name_or_path"),
            "quantized": isinstance(config_data.get("quantization_config"), dict),
        }

    if not (adapter_config.is_file() or config_json.is_file() or weight_names or gguf_names):
        _add_error(result, "checkpoint directory lacks adapter/config, model weights, or GGUF files")
    if gguf_names and not (adapter_config.is_file() or config_json.is_file()):
        _add_warning(result, "checkpoint already appears to contain GGUF artifacts; route to runtime loading rather than export conversion")
    return details


def validate_format(args: argparse.Namespace, checkpoint: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    requested_format = args.format
    details = {"requested": requested_format}
    if requested_format not in EXPORT_FORMATS:
        _add_error(result, f"unsupported export format: {requested_format}")
        return details

    if requested_format == "base":
        _add_warning(result, "format 'base' is a Studio/direct-Python concept; `unsloth export` CLI supports lora, merged-16bit, merged-4bit, and gguf")
    elif requested_format not in CLI_EXPORT_FORMATS:
        _add_warning(result, f"format {requested_format!r} is not part of the CLI export format set")

    is_local_directory = checkpoint.get("kind") == "directory"
    has_adapter = bool(checkpoint.get("has_adapter_config"))
    has_config = bool(checkpoint.get("has_config_json"))
    if is_local_directory:
        if requested_format == "lora" and not has_adapter:
            _add_error(result, "LoRA export expects adapter_config.json / PEFT adapter metadata")
        if requested_format in {"merged-16bit", "merged-4bit"} and not has_adapter:
            _add_warning(result, "CLI/Studio merged export expects a PEFT adapter; use base/direct export for non-PEFT checkpoints")
        if requested_format == "base" and has_adapter:
            _add_warning(result, "base export was selected for a PEFT adapter; merged or lora export is usually correct")
        if requested_format == "gguf" and checkpoint.get("kind") == "gguf_file":
            _add_warning(result, "input is already a GGUF file; conversion is probably unnecessary")
        if requested_format == "base" and not has_config:
            _add_warning(result, "base export usually expects config.json for a full model")

    quantization = args.quantization.lower() if args.quantization else None
    if requested_format == "gguf":
        if not quantization:
            quantization = "q4_k_m"
        details["quantization"] = quantization
        if quantization.startswith("iq2"):
            _add_error(result, "Unsloth GGUF export does not support iq2 quantization variants in this path")
        elif quantization not in GGUF_QUANTS:
            _add_error(result, f"unsupported GGUF quantization: {quantization}")
        elif quantization not in CLI_GGUF_QUANTS:
            _add_warning(result, f"quantization {quantization!r} is supported by Python save paths but not advertised by the CLI export command")
    elif quantization:
        details["quantization"] = quantization
        _add_warning(result, "quantization is ignored unless --format gguf")

    if requested_format == "merged-4bit":
        _add_warning(result, "merged 4-bit is a final-artifact choice; prefer merged-16bit before GGUF or repeated conversions")

    return details


def validate_tokenizer(args: argparse.Namespace, checkpoint: dict[str, Any], result: dict[str, Any]) -> None:
    if checkpoint.get("kind") != "directory":
        return
    tokenizer_files = set(checkpoint.get("tokenizer_files", []))
    has_primary_tokenizer = bool({"tokenizer_config.json", "tokenizer.json", "tokenizer.model", "preprocessor_config.json"} & tokenizer_files)
    if args.format == "gguf" and not has_primary_tokenizer:
        _add_error(result, "GGUF export requires a tokenizer; no primary tokenizer files were found in the checkpoint directory")
    elif not has_primary_tokenizer:
        _add_warning(result, "no primary tokenizer files found; exported artifacts may not reload with the trained tokenizer")
    if "tokenizer.model" not in tokenizer_files and args.format == "gguf":
        _add_warning(result, "SentencePiece-based models need tokenizer.model; if this model uses SentencePiece, restore it before GGUF conversion")
    if "tokenizer_config.json" not in tokenizer_files:
        _add_warning(result, "tokenizer_config.json is missing; EOS/chat-template preservation cannot be verified statically")


def validate_output_relationship(args: argparse.Namespace, checkpoint: dict[str, Any], output: dict[str, Any], result: dict[str, Any]) -> None:
    output_path = Path(output.get("expanded", "")).expanduser() if output.get("expanded") else None
    if output_path is None:
        return

    if args.format == "gguf" and output_path.suffix.lower() == ".gguf":
        _add_error(result, "GGUF export output should be a directory, not a .gguf file path")

    if output_path.exists() and output_path.is_file():
        _add_error(result, "output path already exists as a file; export expects a directory")
    elif output_path.exists() and output_path.is_dir():
        output["exists"] = True
        output["non_empty"] = any(output_path.iterdir())
        if output["non_empty"] and not args.allow_existing_output:
            _add_warning(result, "output directory already exists and is non-empty; use a fresh directory or --allow-existing-output")
    else:
        output["exists"] = False
        parent = output_path.parent
        output["parent_exists"] = parent.exists()
        if not parent.exists():
            _add_warning(result, f"output parent directory does not exist yet: {parent}")

    checkpoint_resolved = checkpoint.get("resolved")
    output_resolved = output.get("resolved")
    if not checkpoint_resolved or not output_resolved:
        return
    checkpoint_path = Path(checkpoint_resolved)
    resolved_output = Path(output_resolved)
    try:
        if checkpoint_path == resolved_output:
            _add_error(result, "output directory resolves to the same path as the checkpoint")
        elif resolved_output.is_relative_to(checkpoint_path):
            _add_warning(result, "output directory is inside the checkpoint tree; prefer a sibling exports directory")
        elif checkpoint_path.is_relative_to(resolved_output):
            _add_warning(result, "checkpoint is inside the output tree; avoid overwriting source artifacts")
    except AttributeError:
        try:
            resolved_output.relative_to(checkpoint_path)
            _add_warning(result, "output directory is inside the checkpoint tree; prefer a sibling exports directory")
        except ValueError:
            pass


def validate_hub(args: argparse.Namespace, result: dict[str, Any]) -> dict[str, Any]:
    details = {
        "push_to_hub": bool(args.push_to_hub),
        "repo_id": args.repo_id,
        "private": bool(args.private),
        "token_env": args.hf_token_env,
        "token_env_present": bool(os.environ.get(args.hf_token_env or "")),
    }
    if not args.push_to_hub:
        if args.repo_id:
            _add_warning(result, "repo_id was supplied but --push-to-hub is false")
        if args.private:
            _add_warning(result, "--private has no effect unless --push-to-hub is set")
        return details

    if not args.repo_id:
        _add_error(result, "--repo-id is required when --push-to-hub is set")
    elif not REPO_ID_RE.match(args.repo_id):
        _add_error(result, "repo_id should look like 'namespace/model-name' with no spaces or traversal")
    if not details["token_env_present"] and not args.no_token_check:
        _add_warning(result, f"environment variable {args.hf_token_env} is not set; Hub upload will need a token")
    return details


def inspect_tools(args: argparse.Namespace, result: dict[str, Any]) -> dict[str, Any]:
    if args.format != "gguf" or args.skip_tool_checks:
        return {"checked": False}
    tool_names = ["llama-quantize", "llama-cli", "ollama", "curl", "cmake", "make"]
    tools = {name: shutil.which(name) for name in tool_names}
    missing_llama = [name for name in ("llama-quantize", "llama-cli") if tools.get(name) is None]
    if missing_llama:
        _add_warning(result, "llama.cpp executables are not on PATH; Unsloth may install/use bundled locations during real GGUF export")
    if tools.get("ollama") is None:
        _add_warning(result, "ollama is not on PATH; GGUF export can still succeed, but Ollama model creation is not available from this shell")
    scripts_dir = os.environ.get("UNSLOTH_LLAMA_CPP_SCRIPTS_DIR")
    return {"checked": True, "which": tools, "UNSLOTH_LLAMA_CPP_SCRIPTS_DIR": scripts_dir}


def build_commands(args: argparse.Namespace, result: dict[str, Any]) -> None:
    if not args.checkpoint or not args.output:
        return
    command = ["unsloth", "export", args.checkpoint, args.output, "--format", args.format]
    if args.format == "gguf":
        command.extend(["--quantization", (args.quantization or "q4_k_m")])
    if args.push_to_hub:
        command.append("--push-to-hub")
        if args.repo_id:
            command.extend(["--repo-id", args.repo_id])
        command.extend(["--hf-token", f"${args.hf_token_env}"])
        if args.private:
            command.append("--private")
    if args.format == "base":
        result["commands"].append("# CLI does not expose base export; use Studio /export/base or direct Python save_pretrained")
    else:
        result["commands"].append(" ".join(_shell_quote(part) for part in command))


def _shell_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_@%+=:,./~$-]+", value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def list_checkpoints(outputs_dir: str, result: dict[str, Any]) -> None:
    outputs_path = Path(outputs_dir).expanduser()
    if not outputs_path.exists():
        _add_error(result, f"outputs directory does not exist: {outputs_path}")
        return
    if not outputs_path.is_dir():
        _add_error(result, f"outputs path is not a directory: {outputs_path}")
        return

    discovered: list[dict[str, Any]] = []
    for run_dir in sorted(outputs_path.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True):
        if not run_dir.is_dir():
            continue
        adapter_config = run_dir / "adapter_config.json"
        config_json = run_dir / "config.json"
        if not (adapter_config.exists() or config_json.exists()):
            continue
        entry = {
            "run": run_dir.name,
            "path": str(run_dir),
            "has_adapter_config": adapter_config.exists(),
            "has_config_json": config_json.exists(),
            "checkpoints": [],
        }
        for checkpoint_dir in sorted(run_dir.iterdir()):
            if not checkpoint_dir.is_dir() or not checkpoint_dir.name.startswith("checkpoint-"):
                continue
            if not ((checkpoint_dir / "adapter_config.json").exists() or (checkpoint_dir / "config.json").exists()):
                continue
            checkpoint_entry = {"name": checkpoint_dir.name, "path": str(checkpoint_dir)}
            trainer_state = _safe_read_json(checkpoint_dir / "trainer_state.json") if (checkpoint_dir / "trainer_state.json").exists() else {}
            log_history = trainer_state.get("log_history") if isinstance(trainer_state, dict) else None
            if isinstance(log_history, list) and log_history:
                checkpoint_entry["loss"] = log_history[-1].get("loss")
            entry["checkpoints"].append(checkpoint_entry)
        discovered.append(entry)
    result["checkpoints"] = discovered
    if not discovered:
        _add_warning(result, "no Unsloth-style training runs found under outputs directory")


def run_preflight(args: argparse.Namespace) -> dict[str, Any]:
    result = _empty_result()
    if args.list_checkpoints:
        list_checkpoints(args.list_checkpoints, result)
        return result

    if not args.checkpoint:
        _add_error(result, "--checkpoint is required unless --list-checkpoints is used")
    if not args.output:
        _add_error(result, "--output is required unless --list-checkpoints is used")
    if not args.format:
        _add_error(result, "--format is required unless --list-checkpoints is used")
    if result["errors"]:
        return result

    checkpoint = inspect_checkpoint(args.checkpoint, result)
    output = validate_save_directory(args.output, result)
    result["checkpoint"] = checkpoint
    result["output"] = output
    result["format"] = validate_format(args, checkpoint, result)
    validate_tokenizer(args, checkpoint, result)
    validate_output_relationship(args, checkpoint, output, result)
    result["hub"] = validate_hub(args, result)
    result["tools"] = inspect_tools(args, result)
    build_commands(args, result)

    if result["ok"]:
        _add_info(result, "static export preflight passed; no model was loaded and no conversion was run")
    return result


def print_human(result: dict[str, Any]) -> None:
    status = "OK" if result.get("ok") else "FAILED"
    print(f"Unsloth export preflight: {status}")
    for title, key in (("Errors", "errors"), ("Warnings", "warnings"), ("Info", "info")):
        items = result.get(key) or []
        if items:
            print(f"\n{title}:")
            for item in items:
                print(f"- {item}")

    checkpoint = result.get("checkpoint") or {}
    if checkpoint:
        print("\nCheckpoint:")
        for field_name in ("kind", "resolved", "repo_id", "has_adapter_config", "has_config_json", "tokenizer_files", "weight_files", "gguf_files"):
            if field_name in checkpoint:
                print(f"- {field_name}: {checkpoint[field_name]}")

    output = result.get("output") or {}
    if output:
        print("\nOutput:")
        for field_name in ("resolved", "exists", "non_empty", "parent_exists"):
            if field_name in output:
                print(f"- {field_name}: {output[field_name]}")

    if result.get("commands"):
        print("\nSuggested command:")
        for command in result["commands"]:
            print(command)

    if result.get("checkpoints"):
        print("\nDiscovered checkpoints:")
        for run_entry in result["checkpoints"]:
            print(f"- {run_entry['run']}: {run_entry['path']}")
            for checkpoint_entry in run_entry.get("checkpoints", []):
                loss = checkpoint_entry.get("loss")
                suffix = f" (loss: {loss})" if loss is not None else ""
                print(f"  - {checkpoint_entry['name']}: {checkpoint_entry['path']}{suffix}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Unsloth export checkpoint/output targets without loading models or running conversion.",
    )
    parser.add_argument("--checkpoint", help="Local checkpoint directory/.gguf file or remote repo id to export from.")
    parser.add_argument("--output", help="Output directory for exported artifacts; not created by this helper.")
    parser.add_argument("--format", choices=sorted(EXPORT_FORMATS), help="Export format to validate.")
    parser.add_argument("--quantization", help="GGUF quantization name; default for GGUF is q4_k_m.")
    parser.add_argument("--push-to-hub", action="store_true", help="Validate Hub upload flags as part of preflight.")
    parser.add_argument("--repo-id", help="Hugging Face Hub repo id, normally namespace/model-name.")
    parser.add_argument("--private", action="store_true", help="Mark the intended Hub repo as private.")
    parser.add_argument("--hf-token-env", default="HF_TOKEN", help="Environment variable expected to hold the Hub token; value is never printed.")
    parser.add_argument("--no-token-check", action="store_true", help="Do not warn when the token environment variable is absent.")
    parser.add_argument("--allow-existing-output", action="store_true", help="Suppress warning for non-empty existing output directories.")
    parser.add_argument("--skip-tool-checks", action="store_true", help="Skip PATH checks for GGUF/Ollama helper executables.")
    parser.add_argument("--list-checkpoints", metavar="OUTPUTS_DIR", help="List Unsloth-style runs/checkpoints under an outputs directory, then exit.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of human-readable text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_preflight(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
