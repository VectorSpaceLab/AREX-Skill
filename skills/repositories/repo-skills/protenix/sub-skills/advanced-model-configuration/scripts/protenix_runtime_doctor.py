#!/usr/bin/env python3
"""Read-only Protenix runtime doctor for advanced configuration triage."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any

CURRENT_WORKING_DIRECTORY = os.getcwd()
if CURRENT_WORKING_DIRECTORY not in sys.path:
    sys.path.insert(0, CURRENT_WORKING_DIRECTORY)

OPTIONAL_MODULES = [
    "torch",
    "triton",
    "deepspeed",
    "cuequivariance_torch",
    "cuequivariance_ops_torch",
    "ninja",
    "ml_collections",
    "yaml",
]

CORE_PROTENIX_MODULES = [
    "protenix",
    "protenix.config.config",
    "configs.configs_base",
    "configs.configs_inference",
    "configs.configs_model_type",
    "runner.batch_inference",
    "protenix.tfg.config",
    "protenix.tfg.potentials",
    "protenix.metrics.rmsd",
    "protenix.metrics.lddt_metrics",
    "protenix.model.sample_confidence",
]

MODEL_PROBE_MODULES = [
    "protenix.model.protenix",
    "protenix.model.modules.pairformer",
    "protenix.model.modules.confidence",
    "protenix.model.tri_attention",
    "protenix.model.triangular.triangular",
]

ENV_KEYS = [
    "LAYERNORM_TYPE",
    "CUTLASS_PATH",
    "CUDA_HOME",
    "CUDA_PATH",
    "TORCH_CUDA_ARCH_LIST",
    "MAX_JOBS",
    "PROTENIX_ROOT_DIR",
    "TRIANGLE_ATTENTION",
    "TRIANGLE_MULTIPLICATIVE",
    "CUEQ_TRITON_TUNING",
    "CUEQ_TRITON_IGNORE_EXISTING_CACHE",
    "CUEQ_TRITON_CACHE_DIR",
]

EXECUTABLES = [
    "python",
    "python3",
    "protenix",
    "nvcc",
    "ninja",
    "kalign",
    "hmmsearch",
    "hmmbuild",
    "hmmalign",
    "nhmmer",
]

DISTRIBUTIONS = [
    "protenix",
    "torch",
    "triton",
    "deepspeed",
    "cuequivariance-torch",
    "cuequivariance-ops-torch-cu12",
    "cuequivariance-ops-torch",
    "ml-collections",
    "PyYAML",
]

CLI_ALIASES = ["pred", "json", "msa", "mt", "prep"]


def safe_version(distribution_name: str) -> str | None:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool reports failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    version = getattr(module, "__version__", None)
    if version is None:
        package_name = module_name.split(".", 1)[0]
        version = safe_version(package_name)
    return {"ok": True, "version": version}


def distribution_status() -> dict[str, Any]:
    found: dict[str, str] = {}
    missing: list[str] = []
    for name in DISTRIBUTIONS:
        version = safe_version(name)
        if version is None:
            missing.append(name)
        else:
            found[name] = version
    return {"found": found, "missing": missing}


def torch_status() -> dict[str, Any]:
    status = import_status("torch")
    if not status.get("ok"):
        return status

    import torch

    cuda: dict[str, Any] = {
        "available": bool(torch.cuda.is_available()),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cudnn_available": bool(torch.backends.cudnn.is_available()),
        "cudnn_version": torch.backends.cudnn.version()
        if torch.backends.cudnn.is_available()
        else None,
    }
    if cuda["available"]:
        try:
            device_count = torch.cuda.device_count()
            cuda["device_count"] = device_count
            cuda["devices"] = [
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "capability": list(torch.cuda.get_device_capability(index)),
                }
                for index in range(device_count)
            ]
            cuda["current_device"] = int(torch.cuda.current_device())
        except Exception as exc:  # noqa: BLE001 - keep diagnostics non-fatal.
            cuda["device_error"] = f"{type(exc).__name__}: {exc}"

    status["cuda"] = cuda
    status["tf32_matmul_allowed"] = bool(torch.backends.cuda.matmul.allow_tf32)
    status["deterministic_algorithms"] = bool(torch.are_deterministic_algorithms_enabled())
    return status


def executable_status() -> dict[str, dict[str, Any]]:
    return {
        name: {"available": shutil.which(name) is not None, "basename": os.path.basename(shutil.which(name) or "") or None}
        for name in EXECUTABLES
    }


def env_status() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in ENV_KEYS:
        value = os.environ.get(key)
        out[key] = {"set": bool(value), "value_preview": "<set>" if value else None}
    return out


def cli_status() -> dict[str, Any]:
    exe = shutil.which("protenix")
    status: dict[str, Any] = {"available": exe is not None, "aliases": {}}
    if exe is None:
        return status

    for alias in CLI_ALIASES:
        try:
            completed = subprocess.run(
                [exe, alias, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=15,
            )
            status["aliases"][alias] = {"returncode": completed.returncode}
        except Exception as exc:  # noqa: BLE001 - report non-fatal CLI probe errors.
            status["aliases"][alias] = {"error": f"{type(exc).__name__}: {exc}"}
    return status


def default_config_probe() -> dict[str, Any]:
    try:
        from configs.configs_base import configs_base
        from configs.configs_inference import inference_configs
        from configs.configs_model_type import model_configs
    except Exception as exc:  # noqa: BLE001 - report all failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "ok": True,
        "base": {
            "model_name": configs_base.get("model_name"),
            "triangle_multiplicative": configs_base.get("triangle_multiplicative"),
            "triangle_attention": configs_base.get("triangle_attention"),
            "enable_tf32": configs_base.get("enable_tf32"),
            "enable_efficient_fusion": configs_base.get("enable_efficient_fusion"),
            "enable_diffusion_shared_vars_cache": configs_base.get("enable_diffusion_shared_vars_cache"),
            "dtype": configs_base.get("dtype"),
        },
        "inference": {
            "model_name": inference_configs.get("model_name"),
            "enable_tf32": inference_configs.get("enable_tf32"),
            "enable_efficient_fusion": inference_configs.get("enable_efficient_fusion"),
            "enable_diffusion_shared_vars_cache": inference_configs.get("enable_diffusion_shared_vars_cache"),
            "use_template": inference_configs.get("use_template"),
            "use_rna_msa": inference_configs.get("use_rna_msa"),
        },
        "model_names": sorted(model_configs.keys()),
    }


def backend_notes(report: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    env = report.get("environment", {})
    optional = report.get("optional_imports", {})
    torch = report.get("torch", {})

    if not env.get("LAYERNORM_TYPE", {}).get("set"):
        notes.append(
            "LAYERNORM_TYPE is unset; model imports may use fast_layernorm and may build or load the fused CUDA extension."
        )
    elif os.environ.get("LAYERNORM_TYPE") != "torch":
        notes.append("LAYERNORM_TYPE is set but not to 'torch'; confirm this is intentional for backend triage.")

    if not torch.get("cuda", {}).get("available", False):
        notes.append("torch.cuda.is_available() is false; GPU-only kernels cannot be validated in this process.")

    if not optional.get("cuequivariance_torch", {}).get("ok"):
        notes.append("cuequivariance_torch is not importable; prefer torch triangle kernels or repair cuEquivariance.")
    if not optional.get("cuequivariance_ops_torch", {}).get("ok"):
        notes.append("cuequivariance_ops_torch is not importable; cuEquivariance ops may be unavailable.")
    if not optional.get("triton", {}).get("ok"):
        notes.append("triton is not importable; Triton-backed kernels may be unavailable.")
    if not optional.get("deepspeed", {}).get("ok"):
        notes.append("deepspeed is not importable; triangle_attention='deepspeed' is unavailable.")
    if not env.get("CUTLASS_PATH", {}).get("set"):
        notes.append("CUTLASS_PATH is unset; this matters only for DeepSpeed DS4Sci triangle attention.")

    return notes


def build_report(include_model_imports: bool, include_cli_probe: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "executable_basename": os.path.basename(sys.executable),
            "platform": platform.platform(),
        },
        "distributions": distribution_status(),
        "executables_on_path": executable_status(),
        "environment": env_status(),
        "torch": torch_status(),
        "optional_imports": {name: import_status(name) for name in OPTIONAL_MODULES if name != "torch"},
        "core_protenix_imports": {name: import_status(name) for name in CORE_PROTENIX_MODULES},
        "default_config_probe": default_config_probe(),
    }
    if include_cli_probe:
        report["protenix_cli"] = cli_status()
    else:
        report["protenix_cli"] = "skipped; pass --include-cli-probe to run help probes"

    if include_model_imports:
        report["model_probe_imports"] = {name: import_status(name) for name in MODEL_PROBE_MODULES}
    else:
        report["model_probe_imports"] = (
            "skipped; pass --include-model-imports to probe modules that may trigger fast layer norm behavior"
        )
    report["notes"] = backend_notes(report)
    return report


def format_status(status: dict[str, Any]) -> str:
    if status.get("ok"):
        return str(status.get("version") or "ok")
    return str(status.get("error") or status)


def print_text(report: dict[str, Any]) -> None:
    print("Protenix runtime doctor")
    print(f"Python: {report['python']['version']} on {report['python']['platform']}")

    dist = report["distributions"]
    if dist["found"]:
        print("Distributions:")
        for name, version in sorted(dist["found"].items()):
            print(f"  {name}: {version}")
    if dist["missing"]:
        print("Missing distributions:")
        for name in dist["missing"]:
            print(f"  {name}")

    torch = report["torch"]
    if torch.get("ok"):
        cuda = torch.get("cuda", {})
        print(
            "Torch: "
            f"{torch.get('version')} CUDA available={cuda.get('available')} "
            f"torch CUDA={cuda.get('torch_cuda_version')} TF32={torch.get('tf32_matmul_allowed')}"
        )
        for device in cuda.get("devices", []) or []:
            print(f"  CUDA device {device['index']}: {device['name']} capability={device['capability']}")
    else:
        print(f"Torch: {torch.get('error')}")

    print("Environment:")
    for key, value in report["environment"].items():
        print(f"  {key}: {'set' if value.get('set') else 'unset'}")

    print("Executables on PATH:")
    for key, value in report["executables_on_path"].items():
        print(f"  {key}: {value['available']}")

    print("Optional imports:")
    for name, status in report["optional_imports"].items():
        print(f"  {name}: {format_status(status)}")

    print("Core Protenix imports:")
    for name, status in report["core_protenix_imports"].items():
        print(f"  {name}: {format_status(status)}")

    config_probe = report["default_config_probe"]
    print("Default config probe:")
    if config_probe.get("ok"):
        base = config_probe["base"]
        inference = config_probe["inference"]
        print(
            "  base: "
            f"model={base.get('model_name')} tri_mul={base.get('triangle_multiplicative')} "
            f"tri_att={base.get('triangle_attention')} tf32={base.get('enable_tf32')} dtype={base.get('dtype')}"
        )
        print(
            "  inference: "
            f"model={inference.get('model_name')} tf32={inference.get('enable_tf32')} "
            f"cache={inference.get('enable_diffusion_shared_vars_cache')} fusion={inference.get('enable_efficient_fusion')}"
        )
        print("  model names: " + ", ".join(config_probe.get("model_names", [])))
    else:
        print(f"  {config_probe.get('error')}")

    print("Protenix CLI:")
    cli = report["protenix_cli"]
    if isinstance(cli, str):
        print(f"  {cli}")
    else:
        print(f"  available: {cli.get('available')}")
        for alias, status in cli.get("aliases", {}).items():
            print(f"  {alias}: {status}")

    print("Model probe imports:")
    model_probe = report["model_probe_imports"]
    if isinstance(model_probe, str):
        print(f"  {model_probe}")
    else:
        for name, status in model_probe.items():
            print(f"  {name}: {format_status(status)}")

    if report["notes"]:
        print("Notes:")
        for note in report["notes"]:
            print(f"  - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Protenix runtime doctor for configs, optional backends, CLI presence, and safe imports."
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument(
        "--include-model-imports",
        action="store_true",
        help="also import model modules that may trigger fast layer norm behavior unless LAYERNORM_TYPE=torch is set",
    )
    parser.add_argument(
        "--include-cli-probe",
        action="store_true",
        help="run 'protenix <alias> --help' probes for installed CLI aliases",
    )
    args = parser.parse_args(argv)

    report = build_report(
        include_model_imports=args.include_model_imports,
        include_cli_probe=args.include_cli_probe,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
