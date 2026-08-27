#!/usr/bin/env python3
"""Safe MiniMind-V CLI inference preflight checker."""
from __future__ import annotations
import argparse, shlex, sys
from pathlib import Path
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")
WEIGHT_EXTENSIONS = (".bin", ".safetensors")

def parse_args():
    p = argparse.ArgumentParser(description="Check MiniMind-V eval inputs and print the expected command without loading a model.")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--load-from", default="model")
    p.add_argument("--save-dir", default="out")
    p.add_argument("--weight", default="sft_vlm", choices=["sft_vlm", "pretrain_vlm"])
    p.add_argument("--hidden-size", default=768, type=int)
    p.add_argument("--use-moe", default=0, type=int, choices=[0, 1])
    p.add_argument("--image-dir", default="dataset/eval_images")
    p.add_argument("--vision-model", default="model/siglip2-base-p32-256-ve")
    p.add_argument("--max-new-tokens", default=64, type=int)
    p.add_argument("--device", default="cpu")
    return p.parse_args()

def resolve(repo: Path, value: str) -> Path:
    p = Path(value).expanduser(); return p if p.is_absolute() else repo / p

def quote(parts): return " ".join(shlex.quote(str(x)) for x in parts)
def has_tf_weight(path: Path) -> bool:
    return path.is_dir() and (any(p.is_file() and p.name.endswith(WEIGHT_EXTENSIONS) for p in path.iterdir()) or (path/"model.safetensors.index.json").is_file())
def supported_images(path: Path):
    return [] if not path.is_dir() else [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]

def main() -> int:
    a = parse_args(); repo = Path(a.repo_root).expanduser().resolve()
    native = "model" in a.load_from
    moe = "_moe" if a.use_moe else ""
    expected = resolve(repo, a.save_dir) / f"{a.weight}_{a.hidden_size}{moe}.pth"
    load_from = resolve(repo, a.load_from); image_dir = resolve(repo, a.image_dir); vision = resolve(repo, a.vision_model)
    command = ["python", "eval_vlm.py", "--load_from", a.load_from, "--save_dir", a.save_dir, "--weight", a.weight, "--hidden_size", a.hidden_size, "--use_moe", a.use_moe, "--image_dir", a.image_dir, "--max_new_tokens", a.max_new_tokens, "--device", a.device]
    ok=[]; warn=[]; err=[]
    def rec(cond,msg): (ok if cond else err).append(msg)
    rec(repo.is_dir(), "repo root exists")
    rec((repo/"eval_vlm.py").is_file(), "eval_vlm.py exists")
    rec((repo/"model"/"model_vlm.py").is_file(), "model/model_vlm.py exists")
    rec(vision.is_dir(), f"vision model directory exists: {a.vision_model}")
    if native:
        rec(load_from.is_dir(), f"native tokenizer/load_from directory exists: {a.load_from}")
        rec(expected.is_file(), f"expected native weight exists: {expected.name}")
        alt = resolve(repo, a.save_dir) / f"{a.weight}_{a.hidden_size}{'' if a.use_moe else '_moe'}.pth"
        if not expected.is_file() and alt.is_file(): warn.append(f"opposite MoE convention weight exists: {alt.name}")
        if load_from.is_dir() and has_tf_weight(load_from) and not expected.is_file(): warn.append("load_from looks like Transformers but contains 'model', so native mode will be selected")
    else:
        rec(load_from.is_dir(), f"Transformers load_from directory exists: {a.load_from}")
        if load_from.is_dir():
            rec((load_from/"config.json").is_file(), "Transformers config.json exists")
            rec(has_tf_weight(load_from), "Transformers weight or safetensors index exists")
    rec(image_dir.is_dir(), f"image_dir exists: {a.image_dir}")
    imgs = supported_images(image_dir)
    if image_dir.is_dir() and not imgs: warn.append("image_dir contains no supported images")
    print("MiniMind-V eval preflight")
    print("Mode:", "native PyTorch .pth" if native else "Transformers-format")
    print("Expected command from a MiniMind-V checkout:")
    print(quote(command))
    if ok:
        print("OK:"); [print("  -", x) for x in ok]
    if warn:
        print("Warnings:"); [print("  -", x) for x in warn]
    if err:
        print("Errors:"); [print("  -", x) for x in err]; return 1
    print("Preflight passed. No model was loaded and no generation was run.")
    return 0
if __name__ == "__main__": sys.exit(main())
