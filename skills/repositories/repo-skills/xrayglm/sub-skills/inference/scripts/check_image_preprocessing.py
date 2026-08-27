#!/usr/bin/env python3
"""Check XrayGLM's image-marker and tiny PIL preprocessing contracts.

This is a no-weight, no-network, no-server check. It reads source text and
uses a generated in-memory PIL image; it does not import the model package.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify image tags and a tiny RGB/PIL preprocessing contract without loading weights."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root containing model/chat.py (default: infer from this script)",
    )
    return parser.parse_args()


def infer_root() -> Path:
    # scripts/inference/sub-skills/xrayglm/disco/skills/<repo-root>
    return Path(__file__).resolve().parents[6]


def main() -> int:
    args = parse_args()
    root = (args.repo_root or infer_root()).expanduser().resolve()
    chat_path = root / "model" / "chat.py"
    blip_path = root / "model" / "blip2.py"
    if not chat_path.is_file() or not blip_path.is_file():
        fail(f"expected model/chat.py and model/blip2.py under {root}")
    chat_source = chat_path.read_text(encoding="utf-8")
    blip_source = blip_path.read_text(encoding="utf-8")
    if 'r"<img>(.*?)</img>"' not in chat_source and 'r\'<img>(.*?)</img>\'' not in chat_source:
        fail("chat.py does not contain the expected <img>...</img> parser")
    if "Image.open(BytesIO(response.content))" not in chat_source:
        fail("chat.py does not show URL image decoding through PIL")
    if "Image.open(image_path)" not in chat_source:
        fail("chat.py does not show local-path image decoding through PIL")
    if "image.convert('RGB')" not in chat_source and 'image.convert("RGB")' not in chat_source:
        fail("chat.py does not convert images to RGB before processing")
    if "Resize" not in blip_source or "ToTensor" not in blip_source or "Normalize" not in blip_source:
        fail("blip2.py is missing resize, tensor, or normalization stages")

    try:
        from PIL import Image
        from PIL import ImageOps
    except ImportError as exc:
        fail(f"Pillow is required for the tiny contract check: {exc}")

    # Exercise the relevant PIL properties without invoking any model code.
    sample = Image.new("RGBA", (7, 3), (12, 34, 56, 255))
    rgb = sample.convert("RGB")
    resized = ImageOps.fit(rgb, (224, 224))
    if rgb.mode != "RGB" or resized.size != (224, 224):
        fail("tiny PIL image did not normalize to RGB and 224x224")
    marker = "<img>tiny.png</img>问：描述图像\n答："
    match = re.findall(r"<img>(.*?)</img>", marker)
    if match != ["tiny.png"]:
        fail("tiny image marker parser contract failed")
    stripped = marker.replace(match[-1], "")
    if "tiny.png" in stripped:
        fail("image reference was not removable from prompt text")
    print(f"PASS: image marker, local/URL parser evidence, and tiny PIL RGB resize under {root}")
    return 0


if __name__ == "__main__":
    main()
