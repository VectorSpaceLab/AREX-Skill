#!/usr/bin/env python3
"""Scan MiniMind-V WebUI model directories without importing Gradio or loading weights."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
MODEL_WEIGHT_EXTENSIONS = (".bin", ".safetensors")
INDEX_NAME = "model.safetensors.index.json"

def scan(base_dir: Path, include_hidden: bool = False) -> dict[str, str]:
    models: dict[str, str] = {}
    if not base_dir.is_dir(): return models
    for child in sorted(base_dir.iterdir(), key=lambda p: p.name, reverse=True):
        if not child.is_dir(): continue
        if not include_hidden and (child.name.startswith(".") or child.name.startswith("_")): continue
        try: files = [p.name for p in child.iterdir() if p.is_file()]
        except OSError: continue
        if any(f.endswith(MODEL_WEIGHT_EXTENSIONS) for f in files) or INDEX_NAME in files:
            models[child.name] = str(child)
    return models

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Scan immediate child directories for MiniMind-V WebUI model candidates.")
    p.add_argument("base_dir", nargs="?", default=".", help="Base directory to scan.")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--include-hidden", action="store_true")
    p.add_argument("--require", action="store_true", help="Exit 1 if no candidates are found.")
    a = p.parse_args(argv); base = Path(a.base_dir).expanduser().resolve(); models = scan(base, a.include_hidden)
    if a.format == "json": print(json.dumps(models, indent=2, sort_keys=True))
    else:
        print(f"Scanned base directory: {base}")
        print("Rule: immediate child directories containing .bin, .safetensors, or model.safetensors.index.json")
        if models:
            print(f"Found {len(models)} model director{'y' if len(models)==1 else 'ies'}:")
            for name, path in models.items(): print(f"  {name}\t{path}")
        else:
            print("Found 0 model directories. The WebUI does not scan the base directory itself or nested grandchildren.")
    return 1 if a.require and not models else 0
if __name__ == "__main__": sys.exit(main())
