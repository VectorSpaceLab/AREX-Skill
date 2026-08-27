#!/usr/bin/env python3
"""Safe Coqui TTS environment smoke checker.

This helper confirms that the installed Coqui TTS package is importable, the
registry is readable, the package metadata is present, and the installed CLI
modules expose their help text without starting downloads or long-running
services. Optional CUDA checks are available behind an explicit flag.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from importlib.metadata import PackageNotFoundError, metadata, version
from typing import Any, Dict, List, Optional

DEFAULT_QUERY_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"


@dataclass
class CommandResult:
    name: str
    command: List[str]
    returncode: int
    ok: bool
    stdout: str
    stderr: str


def excerpt(text: str, limit: int = 1200) -> str:
    text = text.replace("\r\n", "\n")
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def run_cmd(name: str, command: List[str], timeout: float) -> CommandResult:
    proc = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout, check=False)
    return CommandResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        ok=proc.returncode == 0,
        stdout=excerpt(proc.stdout),
        stderr=excerpt(proc.stderr),
    )


def pip_check(timeout: float) -> CommandResult:
    return run_cmd("pip-check", [sys.executable, "-m", "pip", "check"], timeout)


def cli_help(timeout: float) -> List[CommandResult]:
    return [
        run_cmd("tts-help", [sys.executable, "-m", "TTS.bin.synthesize", "--help"], timeout),
        run_cmd("tts-server-help", [sys.executable, "-m", "TTS.server.server", "--help"], timeout),
    ]


def query_model(name: str) -> Dict[str, Any]:
    from TTS.utils.manage import ModelManager

    manager = ModelManager(progress_bar=False, verbose=False)
    info: Dict[str, Any] = {"name": name}
    try:
        model = manager.models_dict
        parts = name.split("/")
        if len(parts) == 4 and parts[0] in model and parts[1] in model[parts[0]] and parts[2] in model[parts[0]][parts[1]]:
            entry = model[parts[0]][parts[1]][parts[2]].get(parts[3])
            if entry is not None:
                info.update({
                    "description": entry.get("description"),
                    "default_vocoder": entry.get("default_vocoder"),
                    "license": entry.get("license"),
                    "tos_required": bool(entry.get("tos_required", False)),
                })
        else:
            info["note"] = "model not found in static registry; may be dynamic or shorthand"
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def import_smoke() -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    try:
        import TTS
        from TTS.api import TTS as TTSApi
        from TTS.utils.manage import ModelManager
        from TTS.utils.synthesizer import Synthesizer
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        mgr = ModelManager(progress_bar=False, verbose=False)
        models = mgr.list_models()
        report.update(
            {
                "ok": True,
                "version": getattr(TTS, "__version__", None),
                "api_class": TTSApi.__name__,
                "synthesizer_class": Synthesizer.__name__,
                "registry_count": len(models),
                "first_model": models[0] if models else None,
            }
        )
    except Exception as exc:  # noqa: BLE001
        report.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return report


def cuda_smoke(timeout: float) -> Dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report: Dict[str, Any] = {
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if not torch.cuda.is_available():
        report["ok"] = False
        return report
    try:
        report["device_name"] = torch.cuda.get_device_name(0)
        report["device_capability"] = torch.cuda.get_device_capability(0)
        tensor = torch.empty((1,), device="cuda")
        report["alloc_ok"] = int(tensor.numel()) == 1
        report["ok"] = True
    except Exception as exc:  # noqa: BLE001
        report.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-model", default=DEFAULT_QUERY_MODEL, help="Model name to inspect in the installed registry.")
    parser.add_argument("--skip-query", action="store_true", help="Skip the model metadata query step.")
    parser.add_argument("--skip-pip-check", action="store_true", help="Skip `python -m pip check`.")
    parser.add_argument("--skip-cli-help", action="store_true", help="Skip `TTS.bin.synthesize` and `TTS.server.server` help checks.")
    parser.add_argument("--check-cuda", action="store_true", help="Run a tiny CUDA allocation smoke if torch reports CUDA available.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for subprocess checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {
        "package": {},
        "imports": import_smoke(),
        "commands": [],
        "model_query": None,
        "cuda": None,
        "ok": True,
    }

    try:
        report["package"] = {
            "name": metadata("TTS")["Name"],
            "version": version("TTS"),
            "summary": metadata("TTS").get("Summary"),
        }
    except PackageNotFoundError as exc:
        report["package"] = {"error": f"PackageNotFoundError: {exc}"}
        report["ok"] = False
    except Exception as exc:  # noqa: BLE001
        report["package"] = {"error": f"{type(exc).__name__}: {exc}"}
        report["ok"] = False

    if not report["imports"].get("ok"):
        report["ok"] = False

    if not args.skip_pip_check:
        pip_result = pip_check(args.timeout)
        report["commands"].append(asdict(pip_result))
        if not pip_result.ok:
            report["ok"] = False

    if not args.skip_cli_help:
        for result in cli_help(args.timeout):
            report["commands"].append(asdict(result))
            if not result.ok:
                report["ok"] = False

    if not args.skip_query:
        report["model_query"] = query_model(args.query_model)

    if args.check_cuda:
        report["cuda"] = cuda_smoke(args.timeout)
        if not report["cuda"].get("ok"):
            report["ok"] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Coqui TTS environment smoke")
        print(f"package: {report['package'].get('name')} {report['package'].get('version')}")
        if report["imports"].get("ok"):
            print(f"imports: ok ({report['imports'].get('registry_count')} models; first={report['imports'].get('first_model')})")
        else:
            print(f"imports: FAIL {report['imports'].get('error')}")
        if report["model_query"]:
            mq = report["model_query"]
            print(f"model query: {mq.get('name')} -> {mq.get('description')}")
        if report["cuda"] is not None:
            print(f"cuda: {report['cuda']}")
        for cmd in report["commands"]:
            print(f"[{ 'ok' if cmd['ok'] else 'FAIL' }] {cmd['name']}: {cmd['returncode']}")
        print(f"overall: {'OK' if report['ok'] else 'FAILED'}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
