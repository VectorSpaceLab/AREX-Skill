#!/usr/bin/env python3
"""Client helper for the Hunyuan3D-2 FastAPI service.

Supports dry-run payload inspection without contacting a server.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def b64_file(path: Optional[str], label: str) -> Optional[str]:
    if path is None:
        return None
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {path}")
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or send Hunyuan3D-2 API server requests.")
    parser.add_argument("--server", default="http://localhost:8080", help="Base server URL.")
    parser.add_argument("--mode", choices=["generate", "send", "status"], default="generate", help="Endpoint mode.")
    parser.add_argument("--uid", help="Job id for --mode status.")
    parser.add_argument("--image", help="Image file for image-to-3D or texture conditioning.")
    parser.add_argument("--text", help="Text prompt. Server text-to-image support may be disabled in api_server.py defaults.")
    parser.add_argument("--mesh", help="Existing mesh file to texture via base64 GLB payload.")
    parser.add_argument("--texture", action="store_true", help="Request texture generation.")
    parser.add_argument("--seed", type=int, default=1234, help="Generation seed.")
    parser.add_argument("--octree-resolution", type=int, default=128, help="Server generation octree_resolution payload.")
    parser.add_argument("--num-inference-steps", type=int, default=5, help="Server generation step payload.")
    parser.add_argument("--guidance-scale", type=float, default=5.0, help="Server guidance scale payload.")
    parser.add_argument("--face-count", type=int, default=40000, help="Texture cleanup face count.")
    parser.add_argument("--type", default="glb", help="Output file type requested from server.")
    parser.add_argument("--output", default="result.glb", help="Output file for binary /generate response or completed status model.")
    parser.add_argument("--timeout", type=float, default=600.0, help="HTTP timeout seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print endpoint and payload summary without sending a request.")
    return parser


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.mode == "status":
        if not args.uid:
            raise SystemExit("--uid is required for --mode status")
        return {}
    image = b64_file(args.image, "--image")
    mesh = b64_file(args.mesh, "--mesh")
    if image is None and args.text is None:
        raise SystemExit("Provide --image or --text for generate/send requests.")
    payload: Dict[str, Any] = {
        "seed": args.seed,
        "octree_resolution": args.octree_resolution,
        "num_inference_steps": args.num_inference_steps,
        "guidance_scale": args.guidance_scale,
        "texture": bool(args.texture),
        "face_count": args.face_count,
        "type": args.type,
    }
    if image is not None:
        payload["image"] = image
    if args.text is not None:
        payload["text"] = args.text
    if mesh is not None:
        payload["mesh"] = mesh
    return payload


def payload_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict(payload)
    for key in ("image", "mesh"):
        if key in summary:
            summary[key] = f"<base64 {len(payload[key])} chars>"
    return summary


def request_json(url: str, payload: Dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as response:
        ctype = response.headers.get("Content-Type", "")
        data = response.read()
    if "application/json" in ctype:
        return json.loads(data.decode("utf-8"))
    return data


def main() -> None:
    args = build_parser().parse_args()
    server = args.server.rstrip("/")
    payload = build_payload(args)
    if args.mode == "status":
        url = f"{server}/status/{args.uid}"
    else:
        url = f"{server}/{args.mode}"

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "url": url, "payload": payload_summary(payload)}, indent=2, sort_keys=True))
        return

    try:
        if args.mode == "status":
            with urlopen(url, timeout=args.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            if result.get("status") == "completed" and "model_base64" in result:
                Path(args.output).write_bytes(base64.b64decode(result["model_base64"]))
                print(f"wrote {args.output}")
            else:
                print(json.dumps(result, indent=2, sort_keys=True))
        elif args.mode == "generate":
            result = request_json(url, payload, args.timeout)
            if isinstance(result, bytes):
                Path(args.output).write_bytes(result)
                print(f"wrote {args.output}")
            else:
                print(json.dumps(result, indent=2, sort_keys=True))
        else:
            result = request_json(url, payload, args.timeout)
            print(json.dumps(result, indent=2, sort_keys=True))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"Could not reach server {server}: {exc}") from exc


if __name__ == "__main__":
    main()
