#!/usr/bin/env python3
"""Safe ClearerVoice-Studio training config inspector.

This script reads YAML or JSON configs, summarizes likely task fields, detects
path-valued keys, and optionally checks whether referenced paths exist. It does
not import repository training modules and does not launch training.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TASK_CHOICES = [
    "speech-enhancement",
    "speech-separation",
    "speech-super-resolution",
    "target-speaker-extraction",
    "target-speaker-extraction-online",
    "auto",
]

PATH_KEY_RE = re.compile(
    r"(^|[_\-.])(path|dir|direc|directory|list|lst|scp|checkpoint|init_from|init_checkpoint|config_json|output|input|data)([_\-.]|$)",
    re.IGNORECASE,
)
PATH_SUFFIX_RE = re.compile(r"\.(wav|flac|mp3|m4a|ogg|opus|aac|aiff|wma|webm|mp4|avi|mov|mkv|npy|json|ya?ml|scp|csv|txt|pt|pth)$", re.IGNORECASE)
NONE_STRINGS = {"", "none", "null", "nil", "false"}


def load_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except Exception:
            return simple_yaml_parse(text)
        return yaml.safe_load(text)
    # Try JSON first, then YAML/fallback.
    try:
        return json.loads(text)
    except Exception:
        try:
            import yaml  # type: ignore
        except Exception:
            return simple_yaml_parse(text)
        return yaml.safe_load(text)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"none", "null"}:
        return "None"
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value.replace("'", '"'))
        except Exception:
            return value
    try:
        if any(ch in value for ch in [".", "e", "E"]):
            return float(value)
        return int(value)
    except Exception:
        return value


def simple_yaml_parse(text: str) -> Dict[str, Any]:
    """Small YAML subset parser for simple ClearerVoice-style configs.

    It supports indentation-based dictionaries and scalar values. It is a
    fallback only; install PyYAML for full YAML support.
    """
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: Dict[str, Any] = {}
            parent[key.strip()] = child
            stack.append((indent, child))
        else:
            parent[key.strip()] = parse_scalar(value)
    return root


def flatten(data: Any, prefix: str = "") -> List[Tuple[str, Any]]:
    if isinstance(data, dict):
        out: List[Tuple[str, Any]] = []
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.extend(flatten(value, new_prefix))
        return out
    if isinstance(data, list):
        return [(prefix, data)]
    return [(prefix, data)]


def top_keys(data: Any) -> List[str]:
    return [str(k) for k in data.keys()] if isinstance(data, dict) else []


def get(flat: Dict[str, Any], key: str, default: Any = None) -> Any:
    return flat.get(key, default)


def detect_task(flat: Dict[str, Any], config_path: Path) -> str:
    path_text = "/".join(config_path.parts).lower()
    network = str(get(flat, "network", "")).lower()
    cue = str(get(flat, "network_reference.cue", "")).lower()
    if "target_speaker_extraction_online" in path_text:
        return "target-speaker-extraction-online"
    if "target_speaker_extraction" in path_text or cue:
        return "target-speaker-extraction"
    if "speech_super_resolution" in path_text or "_sr_" in network or get(flat, "config_json") is not None:
        return "speech-super-resolution"
    if "speech_separation" in path_text or "_ss_" in network or get(flat, "num_spks") is not None:
        return "speech-separation"
    if "speech_enhancement" in path_text or "_se_" in network:
        return "speech-enhancement"
    return "auto"


def task_requirements(task: str, mode: str) -> Dict[str, List[str]]:
    trainish = mode != "inference"
    req: Dict[str, List[str]] = {"required": [], "recommended": [], "notes": []}
    if task == "speech-enhancement":
        req["required"] = ["mode", "network", "sampling_rate"]
        req["required"] += ["tr_list", "cv_list"] if trainish else ["checkpoint_dir", "input_path", "output_dir"]
        req["recommended"] = ["batch_size", "effec_batch_size", "max_epoch", "init_learning_rate", "finetune_learning_rate"] if trainish else ["one_time_decode_length", "decode_window"]
        req["notes"].append("SE train rows are noisy_path clean_path with optional duration; inference rows may be one path per line.")
        req["notes"].append("For MossFormer2_SE_48K, confirm lists contain 48 kHz material or an intentional resampling plan.")
    elif task == "speech-separation":
        req["required"] = ["mode", "network", "sampling_rate", "num_spks"]
        req["required"] += ["load_type", "tr_list", "cv_list"] if trainish else ["checkpoint_dir", "input_path", "output_dir"]
        req["recommended"] = ["batch_size", "effec_batch_size", "max_epoch"] if trainish else ["one_time_decode_length", "decode_window"]
        req["notes"].append("SS two-speaker rows are mix_path source1_path source2_path when load_type is one_input_multi_outputs.")
    elif task == "speech-super-resolution":
        req["required"] = ["mode", "network", "config_json", "checkpoint_dir"]
        req["required"] += ["tr_list", "cv_list"] if trainish else ["input_path", "output_dir", "sampling_rate"]
        req["recommended"] = ["batch_size", "effec_batch_size", "max_epoch"] if trainish else ["one_time_decode_length", "decode_window"]
        req["notes"].append("SR YAML should point to a JSON config with sampling_rate, num_gpus, batch_size, upsample, FFT, and mel settings.")
        req["notes"].append("The included SR launcher may pass init_checkpoint_path even when the parser does not accept it; inspect before launch.")
    elif task == "target-speaker-extraction":
        req["required"] = ["speaker_no", "mix_lst_path", "audio_direc", "reference_direc", "audio_sr", "ref_sr", "network_reference.cue", "network_audio.backbone", "init_from"]
        req["recommended"] = ["batch_size", "effec_batch_size", "max_length", "init_learning_rate", "max_epoch", "clip_grad_norm"]
        req["notes"].append("Offline TSE requires cue-specific reference data: lip .mp4, gesture .npy, EEG arrays, or speech-reference scp files.")
        req["notes"].append("Fine-tune init_from is a checkpoint directory containing last_best_checkpoint.pt, not a checkpoint file.")
    elif task == "target-speaker-extraction-online":
        req["required"] = ["speaker_no", "mix_lst_path", "audio_direc", "reference_direc", "audio_sr", "ref_sr", "network_reference.cue", "network_audio.backbone", "init_from"]
        req["recommended"] = ["batch_size", "effec_batch_size", "max_length", "network_audio.image_size", "network_audio.segment_size"]
        req["notes"].append("Online TSE configs are lip/video based; verify mp4 reference files and image-size settings.")
    else:
        req["notes"].append("Task could not be inferred confidently; pass --expect-task explicitly for task-specific checks.")
    return req


def is_path_value(key: str, value: Any) -> bool:
    if isinstance(value, (dict, list, tuple, bool, int, float)) or value is None:
        return False
    text = str(value).strip()
    if text.lower() in NONE_STRINGS:
        return False
    key_leaf = key.split(".")[-1]
    if PATH_KEY_RE.search(key_leaf) or PATH_KEY_RE.search(key):
        return True
    if "/" in text or "\\" in text or PATH_SUFFIX_RE.search(text):
        return True
    return False


def task_dir_candidates(config_path: Path) -> List[Path]:
    candidates = [Path.cwd(), config_path.parent]
    parts = list(config_path.parts)
    if "config" in parts:
        idx = len(parts) - 1 - list(reversed(parts)).index("config")
        if idx > 0:
            candidates.append(Path(*parts[:idx]))
    # Also try parent levels for configs nested as config/train/file.yaml.
    for parent in list(config_path.parents)[:4]:
        candidates.append(parent)
    unique: List[Path] = []
    seen = set()
    for cand in candidates:
        resolved = cand.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def resolve_existing(value: str, bases: Iterable[Path]) -> Tuple[bool, List[str]]:
    text = os.path.expanduser(os.path.expandvars(value.strip()))
    if not text or text.lower() in NONE_STRINGS:
        return True, []
    p = Path(text)
    tried: List[str] = []
    if p.is_absolute():
        tried.append(str(p))
        return p.exists(), tried
    for base in bases:
        cand = (base / p).resolve()
        tried.append(str(cand))
        if cand.exists():
            return True, tried
    return False, tried


def summarize_value(value: Any) -> Any:
    if isinstance(value, list):
        return {"type": "list", "length": len(value), "preview": value[:5]}
    if isinstance(value, dict):
        return {"type": "dict", "keys": list(value.keys())}
    return value


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect ClearerVoice-Studio YAML/JSON training configs without importing training modules.")
    parser.add_argument("--config", required=True, help="YAML or JSON config file to inspect")
    parser.add_argument("--expect-task", choices=TASK_CHOICES, default="auto", help="Expected task family for required-field hints")
    parser.add_argument("--check-paths", action="store_true", help="Warn when likely path-valued fields do not exist")
    parser.add_argument("--as-json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser().resolve()
    result: Dict[str, Any] = {
        "config": str(config_path),
        "exists": config_path.exists(),
        "warnings": [],
        "errors": [],
    }
    if not config_path.exists():
        result["errors"].append("Config file does not exist")
        print(json.dumps(result, indent=2) if args.as_json else f"ERROR: {result['errors'][0]}")
        return 2

    try:
        data = load_config(config_path)
    except Exception as exc:
        result["errors"].append(f"Failed to parse config: {exc}")
        print(json.dumps(result, indent=2) if args.as_json else f"ERROR: {result['errors'][0]}")
        return 2

    flat_pairs = flatten(data)
    flat = {key: value for key, value in flat_pairs if key}
    detected_task = detect_task(flat, config_path)
    task = detected_task if args.expect_task == "auto" else args.expect_task
    mode = str(flat.get("mode", "train")).lower()
    req = task_requirements(task, mode)
    if task == "speech-super-resolution" and config_path.suffix.lower() == ".json":
        req = {
            "required": ["sampling_rate", "num_gpus", "batch_size", "upsample_rates", "upsample_kernel_sizes", "upsample_initial_channel", "num_mels", "n_fft", "hop_size", "win_size"],
            "recommended": ["supported_sampling_rates", "dist_config", "num_workers", "fmax_for_loss"],
            "notes": [
                "This is the SR JSON architecture/training config; pair it with an SR YAML that supplies mode, network, checkpoint_dir, and list/input paths.",
                "Check JSON sampling_rate, supported_sampling_rates, upsample factors, FFT/mel settings, and num_gpus before launch.",
            ],
        }

    missing_required = [key for key in req["required"] if key not in flat]
    missing_recommended = [key for key in req["recommended"] if key not in flat]
    path_fields = [(key, value) for key, value in flat_pairs if key and is_path_value(key, value)]

    result.update({
        "top_keys": top_keys(data),
        "key_count": len(flat_pairs),
        "detected_task": detected_task,
        "task_used": task,
        "mode": mode,
        "important_fields": {key: summarize_value(flat[key]) for key in sorted(flat) if any(token in key.lower() for token in ["mode", "network", "sampling", "sr", "spk", "list", "lst", "scp", "path", "dir", "checkpoint", "init", "batch", "epoch", "cue", "backbone", "config_json"] )},
        "path_fields": [{"key": key, "value": value} for key, value in path_fields],
        "required_fields": req["required"],
        "recommended_fields": req["recommended"],
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "task_notes": req["notes"],
    })

    if missing_required:
        result["warnings"].append("Missing required task fields: " + ", ".join(missing_required))

    if args.check_paths:
        bases = task_dir_candidates(config_path)
        checks = []
        for key, value in path_fields:
            ok, tried = resolve_existing(str(value), bases)
            checks.append({"key": key, "value": value, "exists": ok, "tried": tried})
            # Output directories and fresh checkpoint directories may not exist yet; keep warning useful but not fatal.
            if not ok:
                result["warnings"].append(f"Path field {key} does not exist yet or is relative to a different launch directory: {value}")
        result["path_checks"] = checks

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Config: {result['config']}")
        print(f"Detected task: {detected_task}; task used: {task}; mode: {mode}")
        print(f"Top keys: {', '.join(result['top_keys']) if result['top_keys'] else '(none)'}")
        print(f"Flattened key count: {result['key_count']}")
        print("\nImportant fields:")
        for key, value in result["important_fields"].items():
            print(f"  - {key}: {value!r}")
        print("\nTask-specific required fields:")
        for key in req["required"]:
            mark = "OK" if key in flat else "MISSING"
            print(f"  - [{mark}] {key}")
        if req["recommended"]:
            print("\nRecommended fields:")
            for key in req["recommended"]:
                mark = "OK" if key in flat else "missing"
                print(f"  - [{mark}] {key}")
        print("\nLikely path fields:")
        if path_fields:
            for key, value in path_fields:
                print(f"  - {key}: {value}")
        else:
            print("  (none detected)")
        if args.check_paths and "path_checks" in result:
            print("\nPath checks:")
            for item in result["path_checks"]:
                print(f"  - [{'OK' if item['exists'] else 'MISSING'}] {item['key']}: {item['value']}")
        print("\nTask notes:")
        for note in req["notes"]:
            print(f"  - {note}")
        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
