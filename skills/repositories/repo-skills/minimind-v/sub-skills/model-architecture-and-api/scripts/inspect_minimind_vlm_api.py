#!/usr/bin/env python3
"""Inspect MiniMind-V API signatures without loading weights or downloading resources."""
from __future__ import annotations
import argparse, importlib, inspect, json, sys
from pathlib import Path

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inspect MiniMind-V model/VLM API signatures and config defaults safely.")
    p.add_argument("--repo-root", default=".", help="MiniMind-V checkout root (default: current directory).")
    p.add_argument("--vision-model-path", default="model/siglip2-base-p32-256-ve", help="Relative/local SigLIP2 path to check with --check-vision-path.")
    p.add_argument("--check-vision-path", action="store_true", help="Check local vision directory files; do not load it.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return p

def add_repo(repo: Path) -> None:
    root = str(repo.resolve())
    if root not in sys.path: sys.path.insert(0, root)

def sig(obj) -> str:
    try: return str(inspect.signature(obj))
    except Exception as exc: return f"<unavailable: {type(exc).__name__}: {exc}>"

def collect(args) -> dict:
    repo = Path(args.repo_root).expanduser().resolve()
    if not repo.is_dir(): raise SystemExit(f"repo root does not exist: {args.repo_root}")
    add_repo(repo)
    try:
        mm = importlib.import_module("model.model_minimind")
        vlm = importlib.import_module("model.model_vlm")
    except Exception as exc:
        raise SystemExit(f"Failed to import MiniMind-V source modules: {type(exc).__name__}: {exc}") from exc
    cfg = vlm.VLMConfig(); base = mm.MiniMindConfig()
    report = {
        "modules_imported": ["model.model_minimind", "model.model_vlm"],
        "signatures": {
            "MiniMindConfig": sig(mm.MiniMindConfig),
            "VLMConfig": sig(vlm.VLMConfig),
            "MMVisionProjector": sig(vlm.MMVisionProjector),
            "MiniMindVLM.__init__": sig(vlm.MiniMindVLM.__init__),
            "MiniMindVLM.forward": sig(vlm.MiniMindVLM.forward),
            "MiniMindVLM.generate": sig(vlm.MiniMindVLM.generate),
            "MiniMindVLM.image2tensor": sig(vlm.MiniMindVLM.image2tensor),
            "MiniMindVLM.get_image_embeddings": sig(vlm.MiniMindVLM.get_image_embeddings),
        },
        "vlm_defaults": {k: getattr(cfg, k, None) for k in ["model_type", "image_special_token", "image_ids", "image_hidden_size", "image_token_len", "hidden_size", "num_hidden_layers", "use_moe"]},
        "base_defaults": {k: getattr(base, k, None) for k in ["hidden_size", "num_hidden_layers", "vocab_size", "num_attention_heads", "num_key_value_heads", "max_position_embeddings", "use_moe", "num_experts", "num_experts_per_tok"]},
    }
    if args.check_vision_path:
        supplied = Path(args.vision_model_path).expanduser()
        cand = supplied if supplied.is_absolute() else repo / supplied
        report["vision_path_status"] = {"input": args.vision_model_path, "exists": cand.exists(), "is_dir": cand.is_dir(), "has_config": (cand / "config.json").is_file(), "has_processor_config": (cand / "preprocessor_config.json").is_file(), "has_model_file": any((cand / n).is_file() for n in ["model.safetensors", "pytorch_model.bin", "model.safetensors.index.json"])}
    return report

def main(argv=None) -> int:
    args = parser().parse_args(argv); report = collect(args)
    if args.json: print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("MiniMind-V API inspection")
        for name, value in report["signatures"].items(): print(f"{name}: {value}")
        print("VLM defaults:", report["vlm_defaults"])
        print("Base defaults:", report["base_defaults"])
        if "vision_path_status" in report: print("Vision path status:", report["vision_path_status"])
    return 0
if __name__ == "__main__": raise SystemExit(main())
