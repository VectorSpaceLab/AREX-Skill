#!/usr/bin/env python3
"""Inspect ESPnet inference entrypoint classes and optional CLI help safely."""
from __future__ import annotations
import argparse
import contextlib
import importlib
import inspect
import io
import json
import subprocess
import sys

TASKS = {
    "asr": ("espnet2.bin.asr_inference", "Speech2Text"),
    "asr-streaming": ("espnet2.bin.asr_inference_streaming", "Speech2TextStreaming"),
    "tts": ("espnet2.bin.tts_inference", "Text2Speech"),
    "tts2": ("espnet2.bin.tts2_inference", "Text2Speech"),
    "enh": ("espnet2.bin.enh_inference", "SeparateSpeech"),
    "st": ("espnet2.bin.st_inference", "Speech2Text"),
    "s2t": ("espnet2.bin.s2t_inference", "Speech2Text"),
    "s2st": ("espnet2.bin.s2st_inference", "Speech2Speech"),
    "slu": ("espnet2.bin.slu_inference", "Speech2Understand"),
    "spk": ("espnet2.bin.spk_inference", "Speech2Embedding"),
    "diar": ("espnet2.bin.diar_inference", "DiarizeSpeech"),
    "svs": ("espnet2.bin.svs_inference", "SingingGenerate"),
}


def inspect_task(task: str) -> dict[str, object]:
    module_name, class_name = TASKS[task]
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        init_signature = str(inspect.signature(cls.__init__))
        pretrained_signature = str(inspect.signature(cls.from_pretrained)) if hasattr(cls, "from_pretrained") else None
    data: dict[str, object] = {
        "ok": True,
        "task": task,
        "module": module_name,
        "class": class_name,
        "init_signature": init_signature,
    }
    if pretrained_signature is not None:
        data["from_pretrained_signature"] = pretrained_signature
    messages = (captured_out.getvalue() + captured_err.getvalue()).strip()
    if messages:
        data["messages"] = messages
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect ESPnet inference classes without downloading models.")
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help-cli", action="store_true")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    try:
        data = inspect_task(args.task)
        rc = 0
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report import/signature failures.
        data = {"ok": False, "task": args.task, "error": f"{type(exc).__name__}: {exc}"}
        rc = 1
    if args.help_cli and data.get("ok"):
        completed = subprocess.run([sys.executable, "-m", str(data["module"]), "--help"], text=True, capture_output=True, timeout=args.timeout)
        data["help_returncode"] = completed.returncode
        data["help_excerpt"] = (completed.stdout or completed.stderr)[:2000]
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
