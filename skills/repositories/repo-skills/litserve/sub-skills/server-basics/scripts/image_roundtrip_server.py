#!/usr/bin/env python3
"""LitServe base64 image round-trip example.

Run:
    python image_roundtrip_server.py --host 127.0.0.1 --port 8000 --transform invert

Create a tiny JSON payload:
    python image_roundtrip_server.py --print-sample-json > payload.json

Call:
    curl -X POST http://127.0.0.1:8000/predict \
      -H 'Content-Type: application/json' \
      --data-binary @payload.json > response.json

The response JSON contains an "image" field with a PNG image encoded as base64.
"""

from __future__ import annotations

import argparse
import base64
import io
import json

from PIL import Image, ImageOps

import litserve as ls
from litserve.schema.image import ImageInput, ImageOutput


class ImageRoundTripAPI(ls.LitAPI):
    """Decode a base64 image, apply a small PIL transform, and return base64 PNG."""

    def __init__(self, api_path: str, transform: str) -> None:
        super().__init__(api_path=api_path)
        self.transform = transform

    def setup(self, device):
        self.device = str(device)

    def decode_request(self, request: ImageInput):
        return request.get_image().convert("RGB")

    def predict(self, image: Image.Image):
        if self.transform == "identity":
            return image
        if self.transform == "invert":
            return ImageOps.invert(image)
        if self.transform == "grayscale":
            return ImageOps.grayscale(image)
        if self.transform == "thumbnail":
            result = image.copy()
            result.thumbnail((64, 64))
            return result.convert("RGB")
        raise ValueError(f"Unknown transform: {self.transform}")

    def encode_response(self, image: Image.Image) -> ImageOutput:
        return ImageOutput(image=image)


def sample_payload() -> dict[str, str]:
    image = Image.new("RGB", (16, 16), color=(255, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {"image_data": base64.b64encode(buf.getvalue()).decode("utf-8")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a LitServe base64 image round-trip server.")
    parser.add_argument(
        "--print-sample-json",
        action="store_true",
        help="Print a tiny request payload and exit instead of starting a server.",
    )
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "0.0.0.0", "::"])
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--api-path", default="/predict", help="POST endpoint path; must start with '/'.")
    parser.add_argument("--workers-per-device", default=1, type=int)
    parser.add_argument("--timeout", default=30.0, type=float)
    parser.add_argument(
        "--transform",
        default="identity",
        choices=["identity", "invert", "grayscale", "thumbnail"],
        help="Small deterministic PIL transform applied in predict().",
    )
    parser.add_argument(
        "--generate-client",
        action="store_true",
        help="Write client.py in the current working directory if it does not already exist.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.print_sample_json:
        print(json.dumps(sample_payload()))
        return

    server = ls.LitServer(
        ImageRoundTripAPI(api_path=args.api_path, transform=args.transform),
        accelerator="cpu",
        devices=1,
        workers_per_device=args.workers_per_device,
        timeout=args.timeout,
        model_metadata={"name": "image-roundtrip-example", "kind": "image-demo"},
    )
    server.run(
        host=args.host,
        port=args.port,
        generate_client_file=args.generate_client,
    )


if __name__ == "__main__":
    main()
