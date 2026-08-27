#!/usr/bin/env python3
"""Inspect media, voice, TTS, and optional GPU backends used by GPT Academic."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MODULES = {"openai": "openai", "PIL/Pillow": "PIL", "edge_tts": "edge_tts", "pydub": "pydub", "requests": "requests", "webrtcvad optional": "webrtcvad", "scipy optional": "scipy", "Aliyun NLS SDK optional": "nls", "manim optional": "manim"}
COMMANDS = ["ffmpeg", "nvidia-smi", "manim"]


def setup_repo(repo_root: str | None):
    if not repo_root:
        return {}
    root = Path(repo_root).resolve()
    if (root / "toolbox.py").exists():
        sys.path.insert(0, str(root))
        os.chdir(root)
    try:
        from toolbox import get_conf
        names = ["ENABLE_AUDIO", "TTS_TYPE", "EDGE_TTS_VOICE", "GPT_SOVITS_URL", "LLM_MODEL"]
        values = get_conf(*names)
        return dict(zip(names, values))
    except Exception as exc:  # noqa: BLE001
        return {"config_error": f"{type(exc).__name__}: {exc}"}


def module_status(module_name: str) -> str:
    return "present" if importlib.util.find_spec(module_name) is not None else "missing"


def command_status(command: str):
    path = shutil.which(command)
    if not path:
        return {"status": "missing", "path": None}
    try:
        probe = [command, "-L"] if command == "nvidia-smi" else [command, "--version"]
        proc = subprocess.run(probe, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
    except Exception as exc:  # noqa: BLE001
        return {"status": "present", "path": path, "version_probe": f"{type(exc).__name__}: {exc}"}
    return {"status": "present", "path": path, "version_probe": proc.stdout.splitlines()[:4]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", help="optional GPT Academic checkout root for config checks")
    args = parser.parse_args()
    result = {"modules": {label: module_status(mod) for label, mod in MODULES.items()}, "commands": {cmd: command_status(cmd) for cmd in COMMANDS}, "config_snapshot": setup_repo(args.repo_root), "credentials_present": {"ALIYUN_APPKEY_env": bool(os.environ.get("ALIYUN_APPKEY")), "ALIYUN_TOKEN_env": bool(os.environ.get("ALIYUN_TOKEN")), "ALIYUN_ACCESSKEY_env": bool(os.environ.get("ALIYUN_ACCESSKEY")), "ALIYUN_SECRET_env": bool(os.environ.get("ALIYUN_SECRET")), "OPENAI_API_KEY_env": bool(os.environ.get("OPENAI_API_KEY"))}, "notes": ["Image generation still requires a GPT/OpenAI-compatible model selection and valid API key.", "Voice assistant requires browser microphone permission and usually HTTPS or localhost.", "Edge TTS also needs network access; pydub conversion needs ffmpeg.", "SoVITS and large local media/model services are external optional backends."]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
