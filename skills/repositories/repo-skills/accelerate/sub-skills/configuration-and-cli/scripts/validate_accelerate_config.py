#!/usr/bin/env python3
"""Validate an Accelerate YAML config without importing Accelerate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

CLUSTER_KEYS = {
    "compute_environment",
    "distributed_type",
    "mixed_precision",
    "use_cpu",
    "debug",
    "num_processes",
    "machine_rank",
    "num_machines",
    "gpu_ids",
    "main_process_ip",
    "main_process_port",
    "rdzv_backend",
    "same_network",
    "main_training_function",
    "enable_cpu_affinity",
    "fp8_config",
    "deepspeed_config",
    "fsdp_config",
    "parallelism_config",
    "megatron_lm_config",
    "mpirun_config",
    "downcast_bf16",
    "tpu_name",
    "tpu_zone",
    "tpu_use_cluster",
    "tpu_use_sudo",
    "command_file",
    "commands",
    "tpu_vm",
    "tpu_env",
    "dynamo_config",
}

SAGEMAKER_KEYS = {
    "compute_environment",
    "distributed_type",
    "mixed_precision",
    "use_cpu",
    "debug",
    "ec2_instance_type",
    "iam_role_name",
    "image_uri",
    "profile",
    "region",
    "num_machines",
    "gpu_ids",
    "base_job_name",
    "pytorch_version",
    "transformers_version",
    "py_version",
    "sagemaker_inputs_file",
    "sagemaker_metrics_file",
    "additional_args",
    "dynamo_config",
    "enable_cpu_affinity",
}

LOCAL_DISTRIBUTED_TYPES = {
    "NO",
    "MULTI_CPU",
    "MULTI_GPU",
    "MULTI_NPU",
    "MULTI_MLU",
    "MULTI_SDAA",
    "MULTI_MUSA",
    "MULTI_XPU",
    "MULTI_HPU",
    "MULTI_NEURON",
    "DEEPSPEED",
    "FSDP",
    "MEGATRON_LM",
    "XLA",
}

SAGEMAKER_DISTRIBUTED_TYPES = {"NO", "DATA_PARALLEL", "MODEL_PARALLEL"}
MIXED_PRECISION_VALUES = {"no", "fp16", "bf16", "fp8", None}
RENDEZVOUS_VALUES = {"static", "c10d", None}


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in ("", "null", "Null", "NULL", "~"):
        return None
    if value in ("{}",):
        return {}
    if value in ("[]",):
        return []
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml_mapping(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        without_comment = raw_line.split("#", 1)[0].rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        stripped = without_comment.strip()
        if ":" not in stripped or stripped.startswith("-"):
            raise ValueError(f"fallback parser only supports mapping entries, failed at line {line_number}")
        key, value = stripped.split(":", 1)
        key = key.strip().strip("'\"")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"invalid indentation near line {line_number}")
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [f"Config file not found: {path}"]
    except OSError as error:
        return None, [f"Could not read config: {error}"]
    try:
        if yaml is not None:
            data = yaml.safe_load(text)
        else:
            data = parse_simple_yaml_mapping(text)
    except Exception as error:
        return None, [f"Invalid YAML: {error}"]
    if data is None:
        return None, ["Config file is empty."]
    if not isinstance(data, dict):
        return None, ["Config root must be a mapping of top-level keys."]
    return data, []


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def validate_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    compute_environment = config.get("compute_environment", "LOCAL_MACHINE")
    if compute_environment == "AMAZON_SAGEMAKER":
        known_keys = SAGEMAKER_KEYS
        distributed_values = SAGEMAKER_DISTRIBUTED_TYPES
        for required in ("ec2_instance_type", "iam_role_name"):
            if required not in config:
                warnings.append(f"SageMaker config usually needs `{required}`.")
    elif compute_environment == "LOCAL_MACHINE":
        known_keys = CLUSTER_KEYS
        distributed_values = LOCAL_DISTRIBUTED_TYPES
    else:
        known_keys = CLUSTER_KEYS | SAGEMAKER_KEYS
        distributed_values = LOCAL_DISTRIBUTED_TYPES | SAGEMAKER_DISTRIBUTED_TYPES
        errors.append("`compute_environment` should be `LOCAL_MACHINE` or `AMAZON_SAGEMAKER`.")

    unknown = sorted(set(config) - known_keys)
    if unknown:
        errors.append(f"Unknown top-level keys: {', '.join(unknown)}")

    if "distributed_type" not in config:
        errors.append("Missing required key: `distributed_type`.")
        distributed_type = None
    else:
        distributed_type = config.get("distributed_type")
        if distributed_type not in distributed_values:
            errors.append(
                f"Unsupported `distributed_type` {distributed_type!r} for {compute_environment}; "
                f"expected one of {', '.join(sorted(distributed_values))}."
            )

    mixed_precision = config.get("mixed_precision", None)
    if mixed_precision not in MIXED_PRECISION_VALUES:
        errors.append("`mixed_precision` should be one of: no, fp16, bf16, fp8.")

    use_cpu = bool(config.get("use_cpu", False))
    if use_cpu and distributed_type not in (None, "NO", "MULTI_CPU"):
        errors.append("`use_cpu: true` conflicts with accelerator distributed types; use `distributed_type: 'NO'` for CPU debug.")

    num_processes = as_int(config.get("num_processes"))
    num_machines = as_int(config.get("num_machines", 1))
    machine_rank = as_int(config.get("machine_rank", 0))

    if "num_processes" in config and num_processes is None:
        errors.append("`num_processes` must be an integer.")
    if "num_machines" in config and num_machines is None:
        errors.append("`num_machines` must be an integer.")
    if "machine_rank" in config and machine_rank is None:
        errors.append("`machine_rank` must be an integer.")

    if distributed_type == "MULTI_GPU" and num_processes is not None and num_processes < 2:
        errors.append("`distributed_type: MULTI_GPU` requires `num_processes` of at least 2.")
    if distributed_type == "NO" and num_processes is not None and num_processes > 1:
        warnings.append("`distributed_type: 'NO'` with `num_processes > 1` is unusual; use a distributed type for multiprocessing.")
    if num_processes == -1:
        warnings.append("`num_processes: -1` requires passing `--num_processes` manually at launch time.")
    if num_machines is not None and num_machines < 1:
        errors.append("`num_machines` must be at least 1.")
    if machine_rank is not None and machine_rank < 0:
        errors.append("`machine_rank` cannot be negative.")
    if num_machines is not None and machine_rank is not None and machine_rank >= num_machines:
        errors.append("`machine_rank` must be smaller than `num_machines`.")

    if num_machines is not None and num_machines > 1:
        if not config.get("main_process_ip"):
            errors.append("Multi-node configs need `main_process_ip` for the rank-0 machine.")
        if config.get("main_process_port") in (None, ""):
            warnings.append("Multi-node configs should set `main_process_port` explicitly.")
    elif num_machines == 1 and machine_rank not in (None, 0):
        errors.append("Single-machine configs should use `machine_rank: 0`.")

    rdzv_backend = config.get("rdzv_backend", "static")
    if rdzv_backend not in RENDEZVOUS_VALUES:
        warnings.append("`rdzv_backend` is usually `static` or `c10d`; verify custom rendezvous support.")

    for mapping_key in (
        "deepspeed_config",
        "fsdp_config",
        "parallelism_config",
        "megatron_lm_config",
        "mpirun_config",
        "fp8_config",
        "dynamo_config",
    ):
        if mapping_key in config and config[mapping_key] is not None and not isinstance(config[mapping_key], dict):
            errors.append(f"`{mapping_key}` must be a mapping/dictionary when provided.")

    if distributed_type == "FSDP" and config.get("fsdp_config") in (None, {}):
        warnings.append("FSDP configs usually need an `fsdp_config` mapping; route backend details to the distributed backend guide.")
    if distributed_type == "DEEPSPEED" and config.get("deepspeed_config") in (None, {}):
        warnings.append("DeepSpeed configs usually need a `deepspeed_config` mapping or launch-time DeepSpeed flags.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Accelerate YAML config for schema and common launch conflicts.")
    parser.add_argument("config", type=Path, help="Path to an Accelerate YAML config file.")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Exit non-zero when warnings are present.")
    args = parser.parse_args()

    config, load_errors = load_yaml(args.config)
    if load_errors:
        for message in load_errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2

    errors, warnings = validate_config(config or {})
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)

    if errors or (warnings and args.warnings_as_errors):
        return 1
    print(f"OK: {args.config} looks like a valid Accelerate config.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
