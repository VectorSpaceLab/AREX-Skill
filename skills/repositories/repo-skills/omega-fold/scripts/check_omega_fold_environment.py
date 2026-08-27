#!/usr/bin/env python3
"""No-download OmegaFold environment and API smoke report."""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import shutil
import subprocess
import sys
from typing import Any

EXPECTED_CLI_FLAGS = [
    "--num_cycle",
    "--subbatch_size",
    "--device",
    "--weights_file",
    "--weights",
    "--model",
    "--pseudo_msa_mask_rate",
    "--num_pseudo_msa",
    "--allow_tf32",
]


def dist_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {exc}>"


def run_help(command: list[str], timeout: float) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "error": str(exc), "command": command}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout} seconds", "command": command}

    output = completed.stdout or ""
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "command": command,
        "missing_expected_flags": [flag for flag in EXPECTED_CLI_FLAGS if flag not in output],
        "first_lines": output.splitlines()[:12],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check OmegaFold installation, import, API signatures, Torch backend, "
            "and CLI help without loading model weights or downloading checkpoints."
        )
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="Timeout for CLI help checks.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON only.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "distribution_version": dist_version("OmegaFold") or dist_version("omegafold"),
        "omegafold_import": None,
        "torch": None,
        "cli": None,
        "module_cli": None,
        "warnings": [],
    }

    try:
        import torch

        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "mps_available": bool(getattr(getattr(torch.backends, "mps", None), "is_available", lambda: False)()),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic report
        report["torch"] = {"error_type": type(exc).__name__, "error": str(exc)}

    try:
        import omegafold
        from omegafold import confidence, pipeline

        report["omegafold_import"] = {
            "ok": True,
            "exports": [name for name in ("OmegaFold", "make_config", "pipeline", "confidence") if hasattr(omegafold, name)],
            "signatures": {
                "omegafold.make_config": signature(omegafold.make_config),
                "omegafold.OmegaFold": signature(omegafold.OmegaFold),
                "omegafold.OmegaFold.forward": signature(omegafold.OmegaFold.forward),
                "pipeline.fasta2inputs": signature(pipeline.fasta2inputs),
                "pipeline.save_pdb": signature(pipeline.save_pdb),
                "confidence.get_all_confidence": signature(confidence.get_all_confidence),
            },
            "configs": {},
        }
        for model_idx in (1, 2):
            cfg = omegafold.make_config(model_idx)
            report["omegafold_import"]["configs"][str(model_idx)] = {
                "struct_embedder": getattr(cfg, "struct_embedder", None),
                "node_dim": getattr(cfg, "node_dim", None),
                "edge_dim": getattr(cfg, "edge_dim", None),
                "plm_edge": getattr(getattr(cfg, "plm", None), "edge", None),
            }
        try:
            omegafold.make_config(3)
        except Exception as exc:  # noqa: BLE001 - expected diagnostic
            report["omegafold_import"]["invalid_model_check"] = {
                "raised": type(exc).__name__,
                "message": str(exc),
            }
    except Exception as exc:  # noqa: BLE001 - diagnostic report
        report["omegafold_import"] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        if "numpy" in str(exc).lower() or "_array_api" in str(exc).lower():
            report["warnings"].append("Torch 1.12 with NumPy 2.x can fail; try `python -m pip install 'numpy<2'`.")

    executable = shutil.which("omegafold")
    report["cli"] = {"executable": executable, "help": None}
    if executable:
        report["cli"]["help"] = run_help([executable, "--help"], args.timeout)
    else:
        report["warnings"].append("`omegafold` is not on PATH; try `python -m omegafold --help` if import works.")

    report["module_cli"] = run_help([sys.executable, "-m", "omegafold", "--help"], args.timeout)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["omegafold_import"].get("ok") and (
            (report["cli"].get("help") or {}).get("ok") or report["module_cli"].get("ok")
        ):
            print("\nOmegaFold environment check: OK for no-download inspection.")
        else:
            print("\nOmegaFold environment check: NOT READY; inspect warnings/errors above.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
