#!/usr/bin/env python3
"""Configurable client for the Janus FastAPI demo skeleton.

Safe default: parser help works without requests. Use a subcommand to make
network calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IEND = b"IEND"


def _split_png_stream(blob: bytes) -> list[bytes]:
    images: list[bytes] = []
    offset = 0
    while True:
        start = blob.find(PNG_SIGNATURE, offset)
        if start < 0:
            break
        end = blob.find(PNG_IEND, start)
        if end < 0:
            images.append(blob[start:])
            break
        # Include the IEND chunk plus CRC.
        chunk_end = end + 8
        images.append(blob[start:chunk_end])
        offset = chunk_end
    return images


def understand(args: argparse.Namespace) -> int:
    import requests

    url = f"{args.base_url.rstrip('/')}/understand_image_and_question/"
    with open(args.image, "rb") as fh:
        response = requests.post(
            url,
            files={"file": fh},
            data={
                "question": args.question,
                "seed": args.seed,
                "top_p": args.top_p,
                "temperature": args.temperature,
            },
            timeout=args.timeout,
        )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2, sort_keys=True))
    return 0


def generate(args: argparse.Namespace) -> int:
    import requests

    url = f"{args.base_url.rstrip('/')}/generate_images/"
    data = {"prompt": args.prompt, "guidance": args.guidance}
    if args.seed is not None:
        data["seed"] = args.seed
    response = requests.post(
        url,
        data=data,
        stream=True,
        timeout=args.timeout,
    )
    response.raise_for_status()
    blob = b"".join(response.iter_content(chunk_size=8192))
    images = _split_png_stream(blob)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for idx, data in enumerate(images):
        path = args.output_dir / f"generated_{idx:02d}.png"
        path.write_bytes(data)
        print(path)
    if not images:
        raise SystemExit("No PNG images were detected in the response stream.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client for the Janus FastAPI demo skeleton.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for the service.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    und = subparsers.add_parser("understand", help="Call the understanding endpoint.")
    und.add_argument("--image", required=True, help="Path to the image to upload.")
    und.add_argument("--question", required=True, help="Question to ask about the image.")
    und.add_argument("--seed", type=int, default=42, help="Seed sent to the server.")
    und.add_argument("--top-p", type=float, default=0.95, help="Top-p sent to the server.")
    und.add_argument("--temperature", type=float, default=0.1, help="Temperature sent to the server.")
    und.set_defaults(func=understand)

    gen = subparsers.add_parser("generate", help="Call the text-to-image endpoint.")
    gen.add_argument("--prompt", required=True, help="Prompt to send to the server.")
    gen.add_argument("--seed", type=int, default=None, help="Optional seed sent to the server.")
    gen.add_argument("--guidance", type=float, default=5.0, help="Guidance value sent to the server.")
    gen.add_argument("--output-dir", type=Path, default=Path("generated_images"), help="Directory to store the parsed PNG files.")
    gen.set_defaults(func=generate)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
