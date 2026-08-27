#!/usr/bin/env python3
"""SUPIR demo launch preflight.

Builds source-style launch commands for SUPIR's standard, tiled, and face demo
modes. By default it does not import Gradio and does not start a server.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import socket
from pathlib import Path
from typing import Dict, List

MODE_SCRIPT = {
    "main": "gradio_demo.py",
    "tiled": "gradio_demo_tiled.py",
    "face": "gradio_demo_face.py",
}


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command(args: argparse.Namespace) -> List[str]:
    script = MODE_SCRIPT[args.mode]
    cmd = ["python", script, "--ip", args.ip, "--port", str(args.port)]
    if args.mode == "main" and args.opt:
        cmd.extend(["--opt", args.opt])
    if args.no_llava:
        cmd.append("--no_llava")
    if args.use_image_slider:
        cmd.append("--use_image_slider")
    if args.log_history:
        cmd.append("--log_history")
    if args.loading_half_params:
        cmd.append("--loading_half_params")
    if args.use_tile_vae:
        cmd.append("--use_tile_vae")
    if args.mode in {"main", "tiled"}:
        cmd.extend(["--encoder_tile_size", str(args.encoder_tile_size), "--decoder_tile_size", str(args.decoder_tile_size)])
    if args.load_8bit_llava:
        cmd.append("--load_8bit_llava")
    if args.mode in {"tiled", "face"} and args.local_prompt:
        cmd.append("--local_prompt")
    return cmd


def _checks(args: argparse.Namespace) -> Dict[str, object]:
    optional = {
        "gradio": _module_available("gradio"),
        "gradio_imageslider": _module_available("gradio_imageslider"),
        "torch": _module_available("torch"),
        "SUPIR": _module_available("SUPIR"),
        "llava": _module_available("llava"),
    }
    if args.mode == "face":
        optional["facexlib"] = _module_available("facexlib")
    cfg = Path(args.opt) if args.opt else None
    result: Dict[str, object] = {
        "mode": args.mode,
        "script": MODE_SCRIPT[args.mode],
        "ip": args.ip,
        "port": args.port,
        "port_free": _port_free("127.0.0.1" if args.ip == "0.0.0.0" else args.ip, args.port),
        "optional_imports": optional,
        "config": str(cfg) if cfg else None,
        "config_exists": cfg.exists() if cfg else None,
        "history_logging": args.log_history,
        "binds_public_interface": args.ip == "0.0.0.0",
    }
    if args.mode == "tiled":
        result["tiled_notes"] = {
            "local_prompt": args.local_prompt,
            "use_tile_vae": args.use_tile_vae,
            "encoder_tile_size": args.encoder_tile_size,
            "decoder_tile_size": args.decoder_tile_size,
        }
    if args.mode == "face":
        result["face_notes"] = {
            "local_prompt": args.local_prompt,
            "face_resolution": args.face_resolution,
            "requires_facexlib_assets": True,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight SUPIR Gradio demo launch commands without starting a server.")
    parser.add_argument("--mode", choices=sorted(MODE_SCRIPT), default="main")
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6688)
    parser.add_argument("--opt", help="Config path for main mode, e.g. a Juggernaut/Lightning YAML.")
    parser.add_argument("--no_llava", action="store_true")
    parser.add_argument("--use_image_slider", action="store_true")
    parser.add_argument("--log_history", action="store_true")
    parser.add_argument("--loading_half_params", action="store_true")
    parser.add_argument("--use_tile_vae", action="store_true")
    parser.add_argument("--encoder_tile_size", type=int, default=512)
    parser.add_argument("--decoder_tile_size", type=int, default=64)
    parser.add_argument("--load_8bit_llava", action="store_true")
    parser.add_argument("--local-prompt", dest="local_prompt", action="store_true", help="Enable local prompt flag for tiled/face modes.")
    parser.add_argument("--face-resolution", type=int, default=1024, help="Planning value for face mode UI; not passed as a source CLI arg.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = _checks(args)
    cmd = _command(args)
    quoted = " ".join(shlex.quote(x) for x in cmd)
    payload = {"checks": checks, "command": cmd, "command_string": quoted}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("# SUPIR demo preflight")
        print(f"mode: {args.mode}")
        print(f"command: {quoted}")
        print(f"port_free: {checks['port_free']}")
        if checks["binds_public_interface"]:
            print("warning: --ip 0.0.0.0 exposes the server beyond loopback; require user approval")
        if checks["history_logging"]:
            print("warning: --log_history writes prompt/output metadata under a relative history/ directory")
        print("optional imports:")
        for name, ok in checks["optional_imports"].items():
            print(f"  {name}: {'ok' if ok else 'missing'}")
        if checks.get("config"):
            print(f"config_exists: {checks['config_exists']} ({checks['config']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
