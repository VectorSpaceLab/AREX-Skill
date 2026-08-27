#!/usr/bin/env python3
"""Safely inspect an OpenFold environment.

The checker imports modules, verifies optional backend availability, checks common
external binaries, and optionally runs CLI ``--help`` commands for explicit user
script paths. It never runs inference, training, downloads, builds, or repository
mutations.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

CORE_IMPORTS = [
    "openfold",
    "openfold.config",
    "openfold.data.parsers",
    "openfold.data.mmcif_parsing",
    "openfold.np.protein",
]

MODEL_IMPORTS = [
    "attn_core_inplace_cuda",
    "openfold.model.model",
    "openfold.model.primitives",
    "openfold.utils.script_utils",
]

RELAX_IMPORTS = [
    "openfold.np.relax.relax",
]

OPTIONAL_IMPORTS = {
    "openmm": "Structure relaxation runtime.",
    "pdbfixer": "Structure relaxation repair utility.",
    "deepspeed": "DeepSpeed inference/training acceleration.",
    "deepspeed.ops.deepspeed4science": "DeepSpeed4Science Evoformer attention kernels.",
    "dllogger": "Training/logging dependency used by NVIDIA-style workflows.",
    "flash_attn": "Optional FlashAttention acceleration.",
    "tensorrt": "Optional TensorRT engine acceleration.",
    "cuda.cudart": "CUDA Python runtime module often required by TensorRT utilities.",
    "polygraphy": "TensorRT helper package used for engine workflows.",
    "cuequivariance_torch": "Optional cuEquivariance kernels for CUDA Linux.",
    "cuequivariance_ops_torch": "Optional cuEquivariance operation bindings.",
}

BINARIES = [
    "nvcc",
    "nvidia-smi",
    "jackhmmer",
    "hmmsearch",
    "hmmbuild",
    "hhblits",
    "hhsearch",
    "kalign",
    "aria2c",
    "aws",
    "git",
]


def import_status(module: str, include_paths: bool = False) -> dict[str, Any]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - report all import-time failures.
        status = {
            "ok": False,
            "module": module,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if stdout_buffer.getvalue():
            status["import_stdout_tail"] = stdout_buffer.getvalue()[-500:]
        if stderr_buffer.getvalue():
            status["import_stderr_tail"] = stderr_buffer.getvalue()[-500:]
        return status

    status: dict[str, Any] = {
        "ok": True,
        "module": module,
        "version": getattr(imported, "__version__", None),
    }
    if stdout_buffer.getvalue():
        status["import_stdout_tail"] = stdout_buffer.getvalue()[-500:]
    if stderr_buffer.getvalue():
        status["import_stderr_tail"] = stderr_buffer.getvalue()[-500:]
    if include_paths:
        status["file"] = getattr(imported, "__file__", None)
    return status


def package_version(distribution: str) -> dict[str, Any]:
    try:
        version = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return {"ok": False, "distribution": distribution, "error": "not installed"}
    except Exception as exc:  # noqa: BLE001 - report metadata issues.
        return {"ok": False, "distribution": distribution, "error_type": type(exc).__name__, "error": str(exc)}
    return {"ok": True, "distribution": distribution, "version": version}


def binary_status(binary: str, include_paths: bool) -> dict[str, Any]:
    path = shutil.which(binary)
    status: dict[str, Any] = {"ok": path is not None, "binary": binary}
    if include_paths:
        status["path"] = path
    return status


def run_help(script: Path, timeout: int) -> dict[str, Any]:
    expanded = script.expanduser()
    if not expanded.exists():
        return {"ok": False, "script": str(script), "error": "script not found"}
    if not expanded.is_file():
        return {"ok": False, "script": str(script), "error": "not a file"}

    try:
        completed = subprocess.run(
            [sys.executable, str(expanded), "--help"],
            cwd=str(expanded.parent),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "script": expanded.name, "error": f"timed out after {timeout}s"}
    except Exception as exc:  # noqa: BLE001 - report all launcher failures.
        return {"ok": False, "script": expanded.name, "error_type": type(exc).__name__, "error": str(exc)}

    output = (completed.stdout or "") + (completed.stderr or "")
    return {
        "ok": completed.returncode == 0,
        "script": expanded.name,
        "returncode": completed.returncode,
        "mentions_usage": "usage" in output.lower(),
        "stdout_tail": (completed.stdout or "")[-500:],
        "stderr_tail": (completed.stderr or "")[-500:],
    }


def check_torch() -> dict[str, Any]:
    status = import_status("torch")
    if not status["ok"]:
        return status

    import torch  # type: ignore[import-not-found]

    status.update(
        {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
        }
    )
    return status


def check_cuda_toolkit() -> dict[str, Any]:
    nvcc = shutil.which("nvcc")
    status: dict[str, Any] = {"nvcc_found": nvcc is not None}
    if nvcc:
        try:
            completed = subprocess.run(
                [nvcc, "--version"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001 - report all probe failures.
            status.update({"nvcc_ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        else:
            status.update(
                {
                    "nvcc_ok": completed.returncode == 0,
                    "returncode": completed.returncode,
                    "version_tail": ((completed.stdout or "") + (completed.stderr or ""))[-500:],
                }
            )
    return status


def summarize(results: dict[str, Any], require_core: bool, require_model: bool, require_cli: bool) -> tuple[str, list[str]]:
    failures: list[str] = []

    if require_core:
        for group in ["core_imports", "relax_imports"]:
            for item in results[group]:
                if not item["ok"]:
                    failures.append(f"{group} failed: {item['module']} ({item.get('error_type', 'error')}: {item.get('error', '')})")

    if require_model:
        for item in results["model_imports"]:
            if not item["ok"]:
                failures.append(f"model import failed: {item['module']} ({item.get('error_type', 'error')}: {item.get('error', '')})")

    torch_status = results["torch"]
    if require_core and not torch_status["ok"]:
        failures.append(f"torch import failed: {torch_status.get('error_type', 'error')}: {torch_status.get('error', '')}")

    if require_cli:
        for item in results["cli_help"]:
            if not item["ok"]:
                failures.append(f"CLI help failed: {item['script']} ({item.get('error', 'nonzero exit')})")

    if failures:
        return "fail", failures
    return "pass", []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely validate OpenFold imports, optional backends, extension availability, binaries, and opt-in CLI help.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a text summary.")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds to allow each CLI --help command before marking it failed.")
    parser.add_argument("--no-require-core", action="store_true", help="Do not fail the process for missing core/relax imports; still report them.")
    parser.add_argument("--no-require-model", action="store_true", help="Do not fail the process for missing model imports or attn_core_inplace_cuda; still report them.")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional backend import probes.")
    parser.add_argument("--skip-binaries", action="store_true", help="Skip external binary discovery checks.")
    parser.add_argument("--include-binary-paths", action="store_true", help="Include resolved external-binary paths in output. Omit this when sharing logs publicly.")
    parser.add_argument("--include-import-paths", action="store_true", help="Include imported module file paths in output. Omit this when sharing logs publicly.")
    parser.add_argument("--check-cli", action="store_true", help="Run --help for explicit script paths supplied with --run-pretrained, --train-openfold, or --thread-sequence.")
    parser.add_argument("--run-pretrained", type=Path, help="Path to a run_pretrained_openfold.py script for optional --help checking.")
    parser.add_argument("--train-openfold", type=Path, help="Path to a train_openfold.py script for optional --help checking.")
    parser.add_argument("--thread-sequence", type=Path, help="Path to a thread_sequence.py script for optional --help checking.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cli_scripts = [path for path in [args.run_pretrained, args.train_openfold, args.thread_sequence] if path is not None]
    if args.check_cli and not cli_scripts:
        raise SystemExit("--check-cli requires at least one explicit script path")

    results: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "metadata": {"openfold": package_version("openfold")},
        "torch": check_torch(),
        "cuda_toolkit": check_cuda_toolkit(),
        "core_imports": [import_status(module, args.include_import_paths) for module in CORE_IMPORTS],
        "model_imports": [import_status(module, args.include_import_paths) for module in MODEL_IMPORTS],
        "relax_imports": [import_status(module, args.include_import_paths) for module in RELAX_IMPORTS],
        "optional_imports": {},
        "binaries": [],
        "cli_help": [],
        "notes": [
            "This checker does not download assets, build extensions, run unit tests, run inference, or run training.",
            "Missing optional imports are informational unless the selected workflow enables that backend.",
        ],
    }

    if not args.skip_optional:
        results["optional_imports"] = {
            module: {**import_status(module, args.include_import_paths), "purpose": purpose}
            for module, purpose in OPTIONAL_IMPORTS.items()
        }

    if not args.skip_binaries:
        results["binaries"] = [binary_status(binary, args.include_binary_paths) for binary in BINARIES]

    if args.check_cli:
        results["cli_help"] = [run_help(script, args.timeout) for script in cli_scripts]

    verdict, failures = summarize(
        results,
        require_core=not args.no_require_core,
        require_model=not args.no_require_model,
        require_cli=args.check_cli,
    )
    results["verdict"] = verdict
    results["failures"] = failures

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(f"OpenFold environment check: {verdict}")
        print(f"Python: {results['python']} ({results['platform']})")
        metadata = results["metadata"]["openfold"]
        if metadata["ok"]:
            print(f"OpenFold metadata: {metadata['version']}")
        else:
            print(f"OpenFold metadata: {metadata.get('error')}")
        torch_status = results["torch"]
        if torch_status["ok"]:
            print(f"PyTorch: {torch_status.get('torch_version')} CUDA={torch_status.get('cuda_version')} cuda_available={torch_status.get('cuda_available')}")
        else:
            print(f"PyTorch: FAILED {torch_status.get('error_type')}: {torch_status.get('error')}")
        for failure in failures:
            print(f"ERROR: {failure}")
        missing_optional = [name for name, item in results["optional_imports"].items() if not item["ok"]]
        if missing_optional:
            print("Missing optional imports: " + ", ".join(missing_optional))
        missing_bins = [item["binary"] for item in results["binaries"] if not item["ok"]]
        if missing_bins:
            print("Missing external binaries: " + ", ".join(missing_bins))

    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
