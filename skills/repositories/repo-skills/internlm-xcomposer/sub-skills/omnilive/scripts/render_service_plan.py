#!/usr/bin/env python3
"""Render a non-executing OmniLive service deployment plan.

The script prints Markdown or JSON. It never starts Docker, uvicorn, npm,
Gradio, torch, Swift, or network listeners.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Sequence


@dataclass
class Plan:
    mode: str
    model_root: str
    lan_ip: str
    backend_ip: str
    srs_ip: str
    cuda_visible_devices: str
    audio_source: str
    video_source: str
    warnings: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    sections: List[dict] = field(default_factory=list)


def _is_bad_client_host(host: str) -> bool:
    return host in {"0.0.0.0", "::", ""}


def _is_loopback_or_unspecified(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_unspecified


def _default_backend_ip(lan_ip: str) -> str:
    return lan_ip


def _hostname_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


def add_common_checks(plan: Plan) -> None:
    model_root = Path(plan.model_root).expanduser()
    if model_root.exists():
        plan.checks.append(f"Model root path currently exists: {model_root}")
    else:
        plan.warnings.append(f"Model root path does not currently exist on this host: {model_root}")

    if _is_loopback_or_unspecified(plan.lan_ip):
        plan.warnings.append("SRS CANDIDATE/LAN IP should not be loopback or unspecified; use a LAN-reachable address.")
    if _is_bad_client_host(plan.backend_ip):
        plan.warnings.append("backend_ip is a bind address, not a client destination; use a LAN/routable host for frontends.")
    if _is_bad_client_host(plan.srs_ip):
        plan.warnings.append("srs_ip is a bind address, not a WebRTC client destination; use a LAN/routable host.")

    plan.checks.append(
        f"Validate all required components: python scripts/check_omnilive_layout.py {model_root} --workflow all --require-weights"
    )
    plan.checks.append("Confirm merge_lora/ was produced from base/ + adapter/ before starting memory/service backends.")
    plan.checks.append("Confirm CUDA devices, firewall rules, and browser camera/microphone permissions before execution.")


def srs_section(plan: Plan) -> dict:
    return {
        "title": "SRS + JavaScript frontend + FastAPI backend",
        "bullets": [
            "Use this path when real-time browser WebRTC streaming and interruption support matter.",
            "Keep SRS, frontend browser, and backend on the same LAN for the known-good path.",
            "Expose SRS TCP 1935/8080/1985 and UDP 8000; expose backend TCP 7862 to the frontend.",
            "Patch frontend chat and SRS URLs together; do not mix localhost with remote hosts.",
        ],
        "commands": [
            {
                "label": "Validate service layout",
                "body": f"python scripts/check_omnilive_layout.py {plan.model_root} --workflow service-srs --require-weights",
            },
            {
                "label": "SRS server plan",
                "body": "\n".join([
                    f"export CANDIDATE=\"{plan.lan_ip}\"  # LAN IP, not 127.0.0.1",
                    "docker run --rm --env CANDIDATE=\"$CANDIDATE\" \\",
                    "  -p 1935:1935 -p 8080:8080 -p 1985:1985 -p 8000:8000/udp \\",
                    "  registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5 \\",
                    "  objs/srs -c conf/rtc2rtmp.conf",
                ]),
            },
            {
                "label": "FastAPI backend plan",
                "body": "\n".join([
                    f"export ROOT_DIR=\"{plan.model_root}\"",
                    f"export CUDA_VISIBLE_DEVICES=\"{plan.cuda_visible_devices}\"",
                    "uvicorn main:app --host 0.0.0.0 --port 7862 --loop asyncio",
                ]),
            },
            {
                "label": "Frontend URL configuration",
                "body": "\n".join([
                    f"CHAT_SOCKET_URL = 'ws://{plan.backend_ip}:7862/chat'",
                    f"SRS_BASE_URL = 'webrtc://{plan.srs_ip}/live/livestream'",
                    f"Vite /rtc proxy target = 'http://{plan.srs_ip}:1985'",
                    "Node.js >= 18; run npm install, then npm start in the frontend app working copy.",
                ]),
            },
        ],
    }


def gradio_section(plan: Plan) -> dict:
    return {
        "title": "Gradio frontend + FastAPI backend trio",
        "bullets": [
            "Use this path when avoiding SRS is more important than real-time interruption support.",
            "The backend trio is video-memory on 8002, MLLM on 8001, ASR/TTS on 8000.",
            "audio_source=local uses PyAudio and needs echo cancellation/device-index work; audio_source=gradio is safer first.",
            "video_source=local uses OpenCV camera snapshots; video_source=gradio uses a Gradio webcam component.",
        ],
        "commands": [
            {
                "label": "Validate service layout",
                "body": f"python scripts/check_omnilive_layout.py {plan.model_root} --workflow service-gradio --require-weights",
            },
            {
                "label": "Backend trio plan",
                "body": "\n".join([
                    f"export MODEL_ROOT=\"{plan.model_root}\"  # patch scripts or symlink this as internlm-xcomposer2d5-ol-7b",
                    f"export CUDA_VISIBLE_DEVICES=\"{plan.cuda_visible_devices}\"",
                    "python backend_vs.py  # binds video-memory service, default port 8002",
                    "python backend_llm.py # binds MLLM service, default port 8001",
                    "python backend.py     # binds ASR/TTS service, default port 8000",
                ]),
            },
            {
                "label": "Frontend plan",
                "body": "\n".join([
                    f"python frontend.py --backend_ip {plan.backend_ip} --audio_source {plan.audio_source} --video_source {plan.video_source}",
                    "Click Push Video first; wait for a video snapshot; then Record Audio.",
                ]),
            },
        ],
    }


def build_plan(args: argparse.Namespace) -> Plan:
    lan_ip = _hostname_ip() if args.lan_ip == "auto" else args.lan_ip
    backend_ip = args.backend_ip or _default_backend_ip(lan_ip)
    srs_ip = args.srs_ip or lan_ip
    plan = Plan(
        mode=args.mode,
        model_root=str(Path(args.model_root).expanduser()),
        lan_ip=lan_ip,
        backend_ip=backend_ip,
        srs_ip=srs_ip,
        cuda_visible_devices=args.cuda_visible_devices,
        audio_source=args.audio_source,
        video_source=args.video_source,
    )
    add_common_checks(plan)
    if args.mode in {"srs", "both"}:
        plan.sections.append(srs_section(plan))
    if args.mode in {"gradio", "both"}:
        plan.sections.append(gradio_section(plan))
    return plan


def render_markdown(plan: Plan) -> str:
    lines: List[str] = []
    lines.append("# OmniLive service deployment plan")
    lines.append("")
    lines.append("This is a non-executing plan. Review and edit every path, host, port, and environment before running commands in a prepared runtime.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- mode: `{plan.mode}`")
    lines.append(f"- model root: `{plan.model_root}`")
    lines.append(f"- LAN/SRS candidate IP: `{plan.lan_ip}`")
    lines.append(f"- backend client IP/host: `{plan.backend_ip}`")
    lines.append(f"- SRS client IP/host: `{plan.srs_ip}`")
    lines.append(f"- CUDA_VISIBLE_DEVICES: `{plan.cuda_visible_devices}`")
    lines.append(f"- Gradio audio source: `{plan.audio_source}`")
    lines.append(f"- Gradio video source: `{plan.video_source}`")
    lines.append("")

    if plan.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in plan.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Pre-flight checks")
    lines.append("")
    for check in plan.checks:
        lines.append(f"- {check}")
    lines.append("")

    for section in plan.sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        for bullet in section["bullets"]:
            lines.append(f"- {bullet}")
        lines.append("")
        for command in section["commands"]:
            lines.append(f"### {command['label']}")
            lines.append("")
            lines.append("```bash")
            lines.append(command["body"])
            lines.append("```")
            lines.append("")

    lines.append("## Remote backend reminders")
    lines.append("")
    lines.append("- Use routable client hosts in frontend config; `0.0.0.0` is only a bind address.")
    lines.append("- Add local/backend IPs to `no_proxy` if HTTP requests between backend processes are intercepted by a proxy.")
    lines.append("- Confirm firewall access for every frontend-to-backend and frontend-to-SRS port.")
    lines.append("- Keep SRS WebRTC, chat WebSocket, and API proxy hosts consistent.")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a safe OmniLive service deployment plan.")
    parser.add_argument("--mode", choices=["srs", "gradio", "both"], default="both")
    parser.add_argument("--model-root", required=True, help="Path to the local OmniLive model root.")
    parser.add_argument(
        "--lan-ip",
        default="192.168.3.10",
        help="LAN IP to use as SRS CANDIDATE. Use 'auto' to use socket.gethostbyname(hostname).",
    )
    parser.add_argument("--backend-ip", default=None, help="Frontend-visible backend host/IP. Defaults to --lan-ip.")
    parser.add_argument("--srs-ip", default=None, help="Frontend-visible SRS host/IP. Defaults to --lan-ip.")
    parser.add_argument("--cuda-visible-devices", default="0")
    parser.add_argument("--audio-source", choices=["gradio", "local"], default="gradio")
    parser.add_argument("--video-source", choices=["local", "gradio"], default="local")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    plan = build_plan(args)
    if args.format == "json":
        print(json.dumps(asdict(plan), indent=2, sort_keys=True))
    else:
        print(render_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
