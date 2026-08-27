#!/usr/bin/env python3
"""Generate or validate a tiny PixelRAG local-source config.

This helper does not render, download models, embed, or build an index. It only
prints/writes a safe starter pixelrag.yaml for a local directory and optionally
validates that the source contains supported file types.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SUPPORTED = {".pdf", ".html", ".htm", ".png", ".jpg", ".jpeg", ".md", ".txt"}


def config_text(source: Path, output: Path, device: str, backend: str) -> str:
    return f"""source:
  type: local
  path: {source}

ingest:
  backend: cdp
  quality: 85
  tile_height: 8192

embed:
  model: Qwen/Qwen3-VL-Embedding-2B
  device: {device}

index:
  backend: {backend}

output: {output}
"""


def validate_source(source: Path) -> list[Path]:
    if not source.exists():
        raise SystemExit(f"source does not exist: {source}")
    if not source.is_dir():
        raise SystemExit(f"source is not a directory: {source}")
    return sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local source directory")
    parser.add_argument("--output", type=Path, default=Path("./pixelrag_index"), help="index output directory")
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--backend", choices=["faiss", "qdrant"], default="faiss")
    parser.add_argument("--config", type=Path, default=Path("pixelrag.yaml"), help="config path for --write")
    parser.add_argument("--write", action="store_true", help="write the config file instead of printing")
    parser.add_argument("--validate", action="store_true", help="list supported files found under source")
    args = parser.parse_args()

    if args.validate:
        files = validate_source(args.source)
        print(f"found {len(files)} supported file(s)")
        for p in files[:20]:
            print(p)
        if len(files) > 20:
            print(f"... {len(files) - 20} more")

    text = config_text(args.source, args.output, args.device, args.backend)
    if args.write:
        args.config.write_text(text, encoding="utf-8")
        print(f"wrote {args.config}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
