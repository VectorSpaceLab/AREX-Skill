#!/usr/bin/env python3
"""Inspect a PaddleSpeech server YAML without starting the server."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize and sanity-check PaddleSpeech server config")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = yaml.safe_load(args.config.read_text())
    problems = []
    protocol = data.get("protocol")
    engines = data.get("engine_list", []) or []
    if protocol not in {"http", "websocket"}:
        problems.append(f"protocol {protocol!r} is not http or websocket")
    if not isinstance(engines, list) or not engines:
        problems.append("engine_list is empty or not a list")
    sections = {k for k, v in data.items() if isinstance(v, dict)}
    missing = [engine for engine in engines if engine not in sections]
    if missing:
        problems.append(f"missing config sections for engines: {', '.join(missing)}")
    if protocol == "http" and any(engine.startswith("asr_online") for engine in engines):
        problems.append("streaming ASR online engines require websocket protocol")
    if protocol == "websocket" and not any(engine.startswith(("asr_online", "tts_online")) for engine in engines):
        problems.append("websocket protocol usually needs online ASR/TTS engines")

    summary = {
        "host": data.get("host"),
        "port": data.get("port"),
        "protocol": protocol,
        "engine_list": engines,
        "sections": sorted(sections),
        "devices": {},
        "problems": problems,
    }
    for engine in engines:
        section = data.get(engine)
        if isinstance(section, dict):
            device = section.get("device")
            for key in ("predictor_conf", "am_predictor_conf", "voc_predictor_conf", "am_sess_conf", "voc_sess_conf"):
                if isinstance(section.get(key), dict) and section[key].get("device"):
                    device = section[key].get("device")
            summary["devices"][engine] = device

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"host={summary['host']} port={summary['port']} protocol={summary['protocol']}")
        print("engines=" + ", ".join(engines))
        for engine, device in summary["devices"].items():
            print(f"device[{engine}]={device}")
        if problems:
            print("problems:")
            for problem in problems:
                print(f"- {problem}")
        else:
            print("no structural problems found")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
