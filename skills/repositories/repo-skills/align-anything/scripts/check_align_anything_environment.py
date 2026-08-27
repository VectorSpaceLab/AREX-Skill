#!/usr/bin/env python3
"""Check whether the active Python environment can operate Align-Anything.

The checker imports the installed package and selected modules, reports package
versions, checks CUDA visibility through PyTorch, and optionally runs `pip check`.
It intentionally omits local executable, virtualenv, and installation paths from
its default output so reports can be shared without leaking private paths.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


CORE_IMPORTS = [
    "align_anything",
    "align_anything.models.pretrained_model",
    "align_anything.models.model_registry",
    "align_anything.serve.text_modal_cli",
    "align_anything.serve.multi_modal_cli",
    "align_anything.serve.omni_modal_cli",
    "align_anything.models.remote_rm.run_reward_server",
    "align_anything.models.remote_rm.reward_server",
    "align_anything.models.remote_rm.remote_rm_client",
]

TRAINER_IMPORTS = [
    "align_anything.trainers.text_to_text.sft",
    "align_anything.trainers.text_to_text.dpo",
    "align_anything.trainers.text_to_text.ppo",
    "align_anything.trainers.text_to_text.ppo_remote_rm",
    "align_anything.trainers.text_image_to_text.sft",
    "align_anything.trainers.text_audio_to_text.ppo",
    "align_anything.trainers.any_to_any.sft",
]

OPTIONAL_IMPORTS = [
    "vllm",
    "janus",
    "av",
    "moviepy",
    "gradio",
    "deepspeed",
    "math_verify",
    "latex2sympy2_extended",
]

VERSION_IMPORTS = [
    "torch",
    "transformers",
    "datasets",
    "accelerate",
    "deepspeed",
    "gradio",
]


@dataclass
class ImportResult:
    name: str
    ok: bool
    error_type: str | None = None
    error: str | None = None


@dataclass
class CheckReport:
    python_version: str
    versions: dict[str, str] = field(default_factory=dict)
    cuda: dict[str, Any] = field(default_factory=dict)
    core_imports: list[ImportResult] = field(default_factory=list)
    trainer_imports: list[ImportResult] = field(default_factory=list)
    optional_imports: list[ImportResult] = field(default_factory=list)
    pip_check: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)


def import_quiet(name: str):
    """Import a module while keeping noisy optional-backend warnings out of JSON output."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return importlib.import_module(name)


def try_import(name: str) -> ImportResult:
    try:
        import_quiet(name)
        return ImportResult(name=name, ok=True)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return ImportResult(name=name, ok=False, error_type=type(exc).__name__, error=str(exc))


def module_version(name: str) -> str:
    try:
        module = import_quiet(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"IMPORT_ERROR:{type(exc).__name__}: {exc}"
    return str(getattr(module, "__version__", "unknown"))


def cuda_report() -> dict[str, Any]:
    try:
        torch = import_quiet("torch")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"torch_import_ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report: dict[str, Any] = {
        "torch_import_ok": True,
        "torch_version": getattr(torch, "__version__", "unknown"),
        "torch_cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            report["first_device_name"] = torch.cuda.get_device_name(0)
            report["first_device_capability"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["device_query_error"] = f"{type(exc).__name__}: {exc}"
    return report


def run_pip_check() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def build_report(args: argparse.Namespace) -> CheckReport:
    report = CheckReport(python_version=".".join(map(str, sys.version_info[:3])))
    for name in VERSION_IMPORTS:
        report.versions[name] = module_version(name)
    report.cuda = cuda_report()
    report.core_imports = [try_import(name) for name in CORE_IMPORTS]
    report.trainer_imports = [try_import(name) for name in TRAINER_IMPORTS]
    if args.optional:
        report.optional_imports = [try_import(name) for name in OPTIONAL_IMPORTS]
    if args.pip_check:
        report.pip_check = run_pip_check()

    if not report.cuda.get("cuda_available"):
        report.notes.append("CUDA is not available; CPU/import checks do not prove training or generation readiness.")
    if any((not item.ok and "janus" in item.name) for item in report.optional_imports):
        report.notes.append("Janus is optional and must be prepared separately before Janus workflows are executable.")
    if any((not item.ok and "vllm" in item.name) for item in report.optional_imports):
        report.notes.append("vLLM/Eval-Anything workflows require a separate heavy runtime if vLLM is missing.")
    return report


def print_text(report: CheckReport) -> None:
    data = asdict(report)
    print(f"Python: {data['python_version']}")
    print("Versions:")
    for name, version in data["versions"].items():
        print(f"  {name}: {version}")
    print("CUDA:")
    for key, value in data["cuda"].items():
        print(f"  {key}: {value}")
    for label in ("core_imports", "trainer_imports", "optional_imports"):
        items = data[label]
        if not items:
            continue
        print(label.replace("_", " ").title() + ":")
        for item in items:
            status = "OK" if item["ok"] else f"FAIL {item['error_type']}: {item['error']}"
            print(f"  {item['name']}: {status}")
    if data["pip_check"] is not None:
        print("Pip check:")
        print(json.dumps(data["pip_check"], indent=2, ensure_ascii=False))
    if data["notes"]:
        print("Notes:")
        for note in data["notes"]:
            print(f"  - {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Align-Anything environment readiness")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--optional", action="store_true", help="Probe optional runtime packages such as vLLM and Janus")
    parser.add_argument("--pip-check", action="store_true", help="Run `python -m pip check` with a timeout")
    args = parser.parse_args()

    report = build_report(args)
    data = asdict(report)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_text(report)

    failures = [item for item in report.core_imports + report.trainer_imports if not item.ok]
    if report.pip_check and not report.pip_check["ok"]:
        failures.append(ImportResult(name="pip check", ok=False, error="broken requirements"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
