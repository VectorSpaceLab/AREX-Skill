#!/usr/bin/env python3
"""Quick FunASR package/environment smoke checks.

This helper is intentionally safe: it inspects package metadata, importability,
console-script entry points, and optional backend availability without downloading
models or starting long-running services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

EXPECTED_CONSOLE_SCRIPTS = [
    "funasr",
    "funasr-hydra",
    "funasr-server",
    "funasr-realtime-server",
    "funasr-train",
    "funasr-train-ds",
    "funasr-export",
    "scp2jsonl",
    "jsonl2scp",
    "sensevoice2jsonl",
]

CLI_HELP_MODULES = [
    "funasr.cli",
    "funasr.bin.server",
    "funasr.bin.realtime_ws",
    "funasr.bin.export",
    "funasr.datasets.audio_datasets.scp2jsonl",
    "funasr.datasets.audio_datasets.jsonl2scp",
    "funasr.datasets.audio_datasets.sensevoice2jsonl",
]

OPTIONAL_MODULES = [
    "torch",
    "fastapi",
    "uvicorn",
    "python_multipart",
    "vllm",
    "pypinyin",
    "rapidfuzz",
    "soundfile",
    "librosa",
    "modelscope",
    "huggingface_hub",
    "transformers",
]


def module_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def safe_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - defensive helper
        return None, f"{exc.__class__.__name__}: {exc}"


def run_help(module_name: str) -> dict:
    command = [sys.executable, "-m", module_name, "--help"]
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
        check=False,
    )
    output = proc.stdout.strip() or proc.stderr.strip()
    return {
        "module": module_name,
        "command": " ".join(command),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "output": output[:2000],
    }


def console_script_names() -> set[str]:
    try:
        dist = metadata.distribution("funasr")
    except metadata.PackageNotFoundError:
        return set()
    except Exception:
        return set()
    return {
        entry.name
        for entry in dist.entry_points
        if entry.group == "console_scripts"
    }


def torch_smoke() -> dict:
    module, error = safe_import("torch")
    if error:
        return {"available": False, "error": error}

    info = {
        "available": True,
        "version": getattr(module, "__version__", None),
        "cuda_version": getattr(getattr(module, "version", None), "cuda", None),
        "cuda_available": bool(module.cuda.is_available()),
    }
    if info["cuda_available"]:
        try:
            info["device_count"] = module.cuda.device_count()
            info["device_name"] = module.cuda.get_device_name(0)
            info["device_capability"] = list(module.cuda.get_device_capability(0))
            module.empty((1,), device="cuda")
            info["tiny_allocation"] = True
        except Exception as exc:  # pragma: no cover - defensive helper
            info["tiny_allocation"] = False
            info["error"] = f"{exc.__class__.__name__}: {exc}"
    return info


def vllm_smoke() -> dict:
    result = {
        "available": False,
        "applicable_fun_asr_nano": None,
        "paraformer_rejected": None,
        "qwen3_rejected": None,
    }
    module, error = safe_import("funasr.auto.auto_model_vllm")
    if error:
        result["error"] = error
        return result

    result["available"] = True
    try:
        result["applicable_fun_asr_nano"] = bool(module.check_vllm_applicable("FunASRNano"))
    except Exception as exc:  # pragma: no cover - defensive helper
        result["applicable_fun_asr_nano_error"] = f"{exc.__class__.__name__}: {exc}"

    for family in ("Paraformer", "Qwen3ASR"):
        try:
            module.check_vllm_applicable(family)
        except Exception as exc:
            result[f"{family.lower()}_rejected"] = f"{exc.__class__.__name__}: {exc}"
        else:
            result[f"{family.lower()}_rejected"] = None
    result["vllm_installed"] = module_version("vllm") is not None
    return result


def funasr_smoke() -> dict:
    report: dict = {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "platform": platform.platform(),
        },
        "distribution": {
            "name": "funasr",
            "version": module_version("funasr"),
            "console_scripts": sorted(console_script_names()),
            "expected_console_scripts": EXPECTED_CONSOLE_SCRIPTS,
        },
        "imports": {},
        "optional_modules": {},
    }

    funasr, error = safe_import("funasr")
    if error:
        report["imports"]["funasr"] = {"available": False, "error": error}
        return report

    report["imports"]["funasr"] = {
        "available": True,
        "version": getattr(funasr, "__version__", None),
        "import_errors_count": len(getattr(funasr, "get_import_errors", lambda: {})()),
    }
    report["imports"]["AutoModel"] = {
        "available": hasattr(funasr, "AutoModel"),
    }
    try:
        from funasr import AutoModel

        report["imports"]["AutoModel"]["importable"] = True
        report["imports"]["AutoModel"]["signature"] = "available"
    except Exception as exc:
        report["imports"]["AutoModel"]["importable"] = False
        report["imports"]["AutoModel"]["error"] = f"{exc.__class__.__name__}: {exc}"

    try:
        from funasr.auto.auto_model_vllm import check_vllm_applicable

        report["imports"]["check_vllm_applicable"] = {
            "available": True,
            "FunASRNano": bool(check_vllm_applicable("FunASRNano")),
        }
    except Exception as exc:
        report["imports"]["check_vllm_applicable"] = {
            "available": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }

    for name in OPTIONAL_MODULES:
        import_name = "multipart" if name == "python_multipart" else name
        dist_name = "python-multipart" if name == "python_multipart" else name
        module, err = safe_import(import_name)
        report["optional_modules"][name] = {
            "available": err is None,
            "version": module_version(dist_name),
        }
        if err:
            report["optional_modules"][name]["error"] = err

    return report


def check_cli_help() -> list[dict]:
    return [run_help(module_name) for module_name in CLI_HELP_MODULES]


def collect_required_failures(report: dict, cli_results: list[dict] | None, check_torch: bool, check_vllm: bool) -> list[str]:
    failures: list[str] = []
    if not report["imports"]["funasr"]["available"]:
        failures.append("funasr import failed")
        return failures
    if not report["imports"]["AutoModel"]["importable"]:
        failures.append("AutoModel import failed")
    if not report["distribution"]["version"]:
        failures.append("funasr distribution metadata missing")
    expected = set(EXPECTED_CONSOLE_SCRIPTS)
    actual = set(report["distribution"]["console_scripts"])
    missing = sorted(expected - actual)
    if missing:
        failures.append(f"missing console scripts: {', '.join(missing)}")
    if cli_results is not None:
        bad = [item["module"] for item in cli_results if not item["ok"]]
        if bad:
            failures.append(f"CLI help failed: {', '.join(bad)}")
    if check_torch and not report.get("torch", {}).get("available", False):
        failures.append("torch smoke failed")
    # vLLM is optional in the confirmed FunASR scope, so its absence is a
    # warning rather than a hard failure unless a caller adds a stricter gate
    # later.
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the FunASR package and safe helper commands.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe --help checks for bundled CLI modules.")
    parser.add_argument("--check-torch", action="store_true", help="Probe torch importability and a tiny CUDA allocation when available.")
    parser.add_argument("--check-vllm", action="store_true", help="Inspect AutoModelVLLM applicability and vLLM availability.")
    parser.add_argument("--check-all", action="store_true", help="Enable the CLI, torch, and vLLM checks together.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any requested check fails.")
    args = parser.parse_args()

    if args.check_all:
        args.check_cli = True
        args.check_torch = True
        args.check_vllm = True

    report = funasr_smoke()

    if args.check_torch:
        report["torch"] = torch_smoke()
    if args.check_vllm:
        report["vllm"] = vllm_smoke()
    cli_results = check_cli_help() if args.check_cli else None
    if cli_results is not None:
        report["cli_help"] = cli_results

    report["warnings"] = []
    if report["imports"]["funasr"].get("import_errors_count", 0):
        report["warnings"].append("funasr imported with optional submodule import errors; inspect funasr.get_import_errors() if a missing helper matters.")
    if not report["optional_modules"].get("pypinyin", {}).get("available", False):
        report["warnings"].append("pypinyin is absent; fuzzy hotword matching stays optional.")
    if not report["optional_modules"].get("vllm", {}).get("available", False):
        report["warnings"].append("vllm is absent; accelerated Fun-ASR-Nano / GLM-ASR runtime remains optional.")

    failures = collect_required_failures(report, cli_results, args.check_torch, args.check_vllm)
    report["failures"] = failures
    report["status"] = "ok" if not failures else "failed"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"FunASR version: {report['distribution']['version']}")
        print(f"Console scripts: {', '.join(report['distribution']['console_scripts'])}")
        print(f"AutoModel importable: {report['imports']['AutoModel']['importable']}")
        if args.check_torch:
            print(f"Torch: {report.get('torch', {}).get('available', False)}")
        if args.check_vllm:
            print(f"vLLM helper available: {report.get('vllm', {}).get('available', False)}")
        if cli_results is not None:
            for item in cli_results:
                print(f"{item['module']}: {'ok' if item['ok'] else 'fail'}")
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"- {warning}")
        if report["failures"]:
            print("Failures:")
            for failure in report["failures"]:
                print(f"- {failure}")

    return 0 if (not args.strict or not report["failures"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
