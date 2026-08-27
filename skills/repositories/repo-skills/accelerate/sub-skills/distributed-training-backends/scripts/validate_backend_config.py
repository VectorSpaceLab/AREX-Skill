#!/usr/bin/env python3
"""Static validator for Accelerate backend config snippets.

This helper checks JSON/YAML shape for DeepSpeed, FSDP/FSDP2, native
parallelism, FP8, quantization, compile, and related backend keys. It never
launches distributed jobs and does not import Accelerate or backend runtimes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


VALID_DISTRIBUTED_TYPES = {
    "NO",
    "MULTI_CPU",
    "MULTI_GPU",
    "MULTI_XPU",
    "MULTI_MLU",
    "MULTI_MUSA",
    "MULTI_NPU",
    "MULTI_HPU",
    "DEEPSPEED",
    "FSDP",
    "MEGATRON_LM",
    "XLA",
}
VALID_MIXED_PRECISION = {"no", "fp16", "bf16", "fp8"}
VALID_ZERO_STAGES = {0, 1, 2, 3}
VALID_OFFLOAD_DEVICES = {"none", "cpu", "nvme"}
VALID_FSDP_STATE_DICT = {"FULL_STATE_DICT", "LOCAL_STATE_DICT", "SHARDED_STATE_DICT"}
VALID_FSDP_WRAP = {"TRANSFORMER_BASED_WRAP", "SIZE_BASED_WRAP", "NO_WRAP"}
VALID_FP8_BACKENDS = {"te", "transformer_engine", "ao", "torchao", "msamp"}
VALID_FP8_FORMATS = {"HYBRID", "E4M3", "E5M2"}
VALID_AMAX_ALGOS = {"max", "most_recent"}
VALID_MSAMP_LEVELS = {"O1", "O2"}
VALID_CP_STRATEGIES = {"allgather", "alltoall"}
VALID_SP_ATTN = {"flash_attention_2", "flash_attention_3", "sdpa"}
UNSUPPORTED_SP_ATTN = {"eager", "flex_attention"}

OPTIONAL_IMPORTS = {
    "deepspeed": "deepspeed",
    "torch_xla": "torch_xla",
    "transformer-engine": "transformer_engine",
    "torchao": "torchao",
    "bitsandbytes": "bitsandbytes",
    "ms-amp": "msamp",
    "habana-frameworks": "habana_frameworks",
}


class Finding:
    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.message}"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "none", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue
        indent = len(line_without_comment) - len(line_without_comment.lstrip(" "))
        stripped = line_without_comment.strip()
        if stripped.startswith("-"):
            raise ValueError("fallback YAML parser does not support list items; install PyYAML or use JSON")
        if ":" not in stripped:
            raise ValueError(f"cannot parse YAML line: {raw_line}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        return parse_simple_yaml(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"could not parse YAML: {exc}") from exc


def as_dict(value: Any, context: str, findings: list[Finding]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    findings.append(Finding("error", f"{context} must be a mapping/object"))
    return {}


def normalize_str(value: Any) -> str:
    return str(value).strip()


def add_enum_check(findings: list[Finding], value: Any, valid: set[Any], label: str) -> None:
    if value is not None and value not in valid:
        findings.append(Finding("error", f"{label}={value!r} is not one of {sorted(valid)!r}"))


def get_nested(config: dict[str, Any], dotted: str) -> Any:
    current: Any = config
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_deepspeed_json(config: dict[str, Any], findings: list[Finding]) -> None:
    zero = config.get("zero_optimization")
    if zero is None:
        findings.append(Finding("error", "DeepSpeed JSON is missing zero_optimization"))
        return
    zero = as_dict(zero, "zero_optimization", findings)
    stage = zero.get("stage")
    if stage == "auto":
        findings.append(Finding("warning", "zero_optimization.stage is auto; ensure Accelerate fills it from launch/plugin settings"))
    elif isinstance(stage, str) and stage.isdigit():
        stage = int(stage)
    add_enum_check(findings, stage, VALID_ZERO_STAGES, "zero_optimization.stage")

    for name in ("offload_optimizer", "offload_param"):
        section = zero.get(name)
        if section is None:
            continue
        section = as_dict(section, f"zero_optimization.{name}", findings)
        device = section.get("device", "none")
        add_enum_check(findings, device, VALID_OFFLOAD_DEVICES, f"zero_optimization.{name}.device")
        if section.get("nvme_path") and device != "nvme":
            findings.append(Finding("warning", f"{name}.nvme_path is set but device is {device!r}, not 'nvme'"))

    if stage in {0, 1} and get_nested(config, "zero_optimization.offload_optimizer.device") in {"cpu", "nvme"}:
        findings.append(Finding("warning", "optimizer offload is normally relevant for ZeRO stage 2 or 3"))
    if stage != 3 and get_nested(config, "zero_optimization.offload_param.device") in {"cpu", "nvme"}:
        findings.append(Finding("error", "parameter offload is only valid for ZeRO stage 3"))
    if stage != 3 and zero.get("stage3_gather_16bit_weights_on_model_save") is not None:
        findings.append(Finding("warning", "stage3_gather_16bit_weights_on_model_save only matters for ZeRO stage 3"))
    if stage == 3 and isinstance(config.get("msamp"), dict) and config["msamp"].get("enabled"):
        findings.append(Finding("error", "MS-AMP is not supported with DeepSpeed ZeRO stage 3 in Accelerate"))

    for batch_key in ("train_batch_size", "train_micro_batch_size_per_gpu", "gradient_accumulation_steps"):
        if batch_key not in config:
            findings.append(Finding("warning", f"DeepSpeed JSON omits {batch_key}; Accelerate may fill it only if configured elsewhere"))


def validate_deepspeed_launch(ds_config: dict[str, Any], findings: list[Finding]) -> None:
    if "deepspeed_config_file" in ds_config:
        findings.append(Finding("info", "deepspeed_config_file points to an external DeepSpeed JSON; validate that file too"))
    stage = ds_config.get("zero_stage")
    if isinstance(stage, str) and stage.isdigit():
        stage = int(stage)
    if stage is not None:
        add_enum_check(findings, stage, VALID_ZERO_STAGES, "deepspeed_config.zero_stage")
    if "zero_optimization" in ds_config:
        findings.append(Finding("info", "deepspeed_config contains DeepSpeed JSON-style zero_optimization; treating it as inline DeepSpeed settings"))
        validate_deepspeed_json(ds_config, findings)
    offload_optimizer = ds_config.get("offload_optimizer_device")
    offload_param = ds_config.get("offload_param_device")
    add_enum_check(findings, offload_optimizer, VALID_OFFLOAD_DEVICES, "deepspeed_config.offload_optimizer_device")
    add_enum_check(findings, offload_param, VALID_OFFLOAD_DEVICES, "deepspeed_config.offload_param_device")
    if stage not in {2, 3, None} and offload_optimizer in {"cpu", "nvme"}:
        findings.append(Finding("warning", "optimizer offload is normally relevant for ZeRO stage 2 or 3"))
    if stage != 3 and offload_param in {"cpu", "nvme"}:
        findings.append(Finding("error", "parameter offload requires deepspeed_config.zero_stage: 3"))
    if ds_config.get("zero3_init_flag") and stage != 3:
        findings.append(Finding("warning", "zero3_init_flag only applies to ZeRO stage 3"))
    if ds_config.get("zero3_save_16bit_model") and stage != 3:
        findings.append(Finding("warning", "zero3_save_16bit_model only applies to ZeRO stage 3"))


def validate_fsdp(fsdp: dict[str, Any], findings: list[Finding]) -> None:
    version = fsdp.get("fsdp_version", fsdp.get("version"))
    if isinstance(version, str) and version.isdigit():
        version = int(version)
    if version is not None and version not in {1, 2}:
        findings.append(Finding("error", "fsdp_version must be 1 or 2"))

    state_dict = fsdp.get("fsdp_state_dict_type", fsdp.get("state_dict_type"))
    if state_dict is not None:
        add_enum_check(findings, normalize_str(state_dict).upper(), VALID_FSDP_STATE_DICT, "fsdp_state_dict_type")

    wrap = fsdp.get("fsdp_auto_wrap_policy", fsdp.get("auto_wrap_policy"))
    if wrap is not None:
        add_enum_check(findings, normalize_str(wrap).upper(), VALID_FSDP_WRAP, "fsdp_auto_wrap_policy")

    reshard = fsdp.get("fsdp_reshard_after_forward", fsdp.get("reshard_after_forward"))
    sharding = fsdp.get("fsdp_sharding_strategy", fsdp.get("sharding_strategy"))
    if version == 2:
        if reshard is not None and not isinstance(reshard, bool):
            findings.append(Finding("error", "FSDP2 requires fsdp_reshard_after_forward to be true/false, not a sharding strategy string"))
        if sharding is not None:
            findings.append(Finding("warning", "fsdp_sharding_strategy is FSDP1-style; prefer fsdp_reshard_after_forward for FSDP2"))
        if fsdp.get("fsdp_backward_prefetch_policy") or fsdp.get("backward_prefetch"):
            findings.append(Finding("warning", "backward prefetch is not supported in FSDP2 and may be ignored"))
    elif version == 1 and isinstance(reshard, bool):
        findings.append(Finding("error", "FSDP1 expects fsdp_reshard_after_forward as a strategy string, not a boolean"))

    if normalize_str(wrap).upper() == "TRANSFORMER_BASED_WRAP":
        layer_key_present = any(
            key in fsdp
            for key in (
                "fsdp_transformer_layer_cls_to_wrap",
                "transformer_cls_names_to_wrap",
                "transformer_layer_cls_to_wrap",
            )
        )
        if not layer_key_present:
            findings.append(Finding("warning", "transformer-based FSDP wrapping usually needs exact layer class names or model _no_split_modules"))


def validate_parallelism(parallelism: dict[str, Any], fsdp: dict[str, Any] | None, findings: list[Finding]) -> None:
    sizes = {
        "dp_replicate": parallelism.get("parallelism_config_dp_replicate_size", parallelism.get("dp_replicate_size", 1)),
        "dp_shard": parallelism.get("parallelism_config_dp_shard_size", parallelism.get("dp_shard_size", 1)),
        "tp": parallelism.get("parallelism_config_tp_size", parallelism.get("tp_size", 1)),
        "cp": parallelism.get("parallelism_config_cp_size", parallelism.get("cp_size", 1)),
        "sp": parallelism.get("parallelism_config_sp_size", parallelism.get("sp_size", 1)),
    }
    product = 1
    for name, value in sizes.items():
        try:
            integer = int(value)
        except (TypeError, ValueError):
            findings.append(Finding("error", f"parallelism {name} size must be an integer"))
            continue
        if integer < 1:
            findings.append(Finding("error", f"parallelism {name} size must be >= 1"))
        product *= max(integer, 1)
    if product > 1:
        findings.append(Finding("info", f"parallelism dimension product is {product}; compare with num_processes"))

    fsdp_version = None if fsdp is None else fsdp.get("fsdp_version", fsdp.get("version"))
    if isinstance(fsdp_version, str) and fsdp_version.isdigit():
        fsdp_version = int(fsdp_version)
    if product > 1 and fsdp_version != 2:
        findings.append(Finding("error", "parallelism_config requires FSDP2 (fsdp_config.fsdp_version: 2)"))

    cp_strategy = parallelism.get("parallelism_config_cp_comm_strategy", parallelism.get("cp_comm_strategy"))
    add_enum_check(findings, cp_strategy, VALID_CP_STRATEGIES, "parallelism_config_cp_comm_strategy")

    sp_attn = parallelism.get("parallelism_config_sp_attn_implementation", parallelism.get("sp_attn_implementation"))
    if sp_attn in UNSUPPORTED_SP_ATTN:
        findings.append(Finding("error", f"{sp_attn!r} attention is not supported for DeepSpeed sequence parallelism"))
    elif sp_attn and sp_attn not in VALID_SP_ATTN and not ("/" in str(sp_attn) and "flash-attn" in str(sp_attn)):
        findings.append(Finding("error", "sp attention implementation must be flash_attention_2, flash_attention_3, sdpa, or a hub-hosted flash-attn kernel"))

    fixed_sp = parallelism.get("parallelism_config_sp_seq_length_is_variable", parallelism.get("sp_seq_length_is_variable")) is False
    has_sp_length = parallelism.get("parallelism_config_sp_seq_length", parallelism.get("sp_seq_length")) is not None
    if fixed_sp and not has_sp_length:
        findings.append(Finding("error", "fixed sequence-parallel length requires parallelism_config_sp_seq_length"))


def validate_fp8(fp8: dict[str, Any], mixed_precision: Any, findings: list[Finding]) -> None:
    if fp8 and mixed_precision != "fp8":
        findings.append(Finding("warning", "fp8_config is present but mixed_precision is not 'fp8'"))
    if mixed_precision == "fp8" and not fp8:
        findings.append(Finding("warning", "mixed_precision is fp8 but no fp8_config is present; defaults depend on installed backend"))
    backend = fp8.get("fp8_backend", fp8.get("backend"))
    if backend is not None:
        backend_norm = normalize_str(backend).lower()
        add_enum_check(findings, backend_norm, VALID_FP8_BACKENDS, "fp8_backend")
    fp8_format = fp8.get("fp8_format")
    if fp8_format is not None:
        add_enum_check(findings, normalize_str(fp8_format).upper(), VALID_FP8_FORMATS, "fp8_format")
    algo = fp8.get("fp8_amax_compute_algo", fp8.get("amax_compute_algo"))
    if algo is not None:
        add_enum_check(findings, normalize_str(algo).lower(), VALID_AMAX_ALGOS, "fp8_amax_compute_algo")
    opt_level = fp8.get("fp8_opt_level", fp8.get("opt_level"))
    if opt_level is not None:
        add_enum_check(findings, normalize_str(opt_level).upper(), VALID_MSAMP_LEVELS, "fp8_opt_level")


def validate_quantization(config: dict[str, Any], findings: list[Finding]) -> None:
    if config.get("load_in_8bit") and config.get("load_in_4bit"):
        findings.append(Finding("error", "load_in_8bit and load_in_4bit cannot both be true"))
    quant_type = config.get("bnb_4bit_quant_type")
    if quant_type is not None and quant_type not in {"fp4", "nf4"}:
        findings.append(Finding("error", "bnb_4bit_quant_type must be 'fp4' or 'nf4'"))
    compute_dtype = config.get("bnb_4bit_compute_dtype")
    if compute_dtype is not None and str(compute_dtype).replace("torch.", "") not in {"fp32", "float32", "fp16", "float16", "bf16", "bfloat16"}:
        findings.append(Finding("warning", "bnb_4bit_compute_dtype is unusual; expected fp32/fp16/bf16 style value"))


def validate_accelerate_config(config: dict[str, Any], findings: list[Finding]) -> None:
    if "deepseed_config" in config:
        findings.append(Finding("error", "found 'deepseed_config'; did you mean 'deepspeed_config'?"))

    distributed_type = config.get("distributed_type")
    if distributed_type is not None:
        add_enum_check(findings, normalize_str(distributed_type).upper(), VALID_DISTRIBUTED_TYPES, "distributed_type")

    mixed_precision = config.get("mixed_precision")
    if mixed_precision is not None:
        add_enum_check(findings, normalize_str(mixed_precision).lower(), VALID_MIXED_PRECISION, "mixed_precision")
        mixed_precision = normalize_str(mixed_precision).lower()

    ds_config = config.get("deepspeed_config")
    fsdp_config = config.get("fsdp_config")
    parallelism = config.get("parallelism_config")
    fp8_config = config.get("fp8_config") or {}

    if normalize_str(distributed_type).upper() == "DEEPSPEED" and ds_config is None:
        findings.append(Finding("error", "distributed_type is DEEPSPEED but deepspeed_config is missing"))
    if normalize_str(distributed_type).upper() == "FSDP" and fsdp_config is None:
        findings.append(Finding("warning", "distributed_type is FSDP but fsdp_config is missing; defaults may be insufficient"))
    if normalize_str(distributed_type).upper() != "DEEPSPEED" and ds_config:
        findings.append(Finding("warning", "deepspeed_config is present but distributed_type is not DEEPSPEED"))
    if normalize_str(distributed_type).upper() != "FSDP" and fsdp_config:
        findings.append(Finding("warning", "fsdp_config is present but distributed_type is not FSDP"))

    if ds_config is not None:
        validate_deepspeed_launch(as_dict(ds_config, "deepspeed_config", findings), findings)
    fsdp_dict = None
    if fsdp_config is not None:
        fsdp_dict = as_dict(fsdp_config, "fsdp_config", findings)
        validate_fsdp(fsdp_dict, findings)
    if parallelism is not None:
        validate_parallelism(as_dict(parallelism, "parallelism_config", findings), fsdp_dict, findings)
    validate_fp8(as_dict(fp8_config, "fp8_config", findings), mixed_precision, findings)

    quantization = config.get("quantization_config") or config.get("bnb_quantization_config")
    if quantization is not None:
        validate_quantization(as_dict(quantization, "quantization_config", findings), findings)

    num_processes = config.get("num_processes")
    if num_processes is not None:
        try:
            if int(num_processes) < 1:
                findings.append(Finding("error", "num_processes must be >= 1"))
        except (TypeError, ValueError):
            findings.append(Finding("error", "num_processes must be an integer"))

    if config.get("tpu_use_cluster") and normalize_str(distributed_type).upper() != "XLA":
        findings.append(Finding("warning", "tpu_use_cluster is set but distributed_type is not XLA"))


def detect_format(config: Any, requested: str) -> str:
    if requested != "auto":
        return requested
    if not isinstance(config, dict):
        return "accelerate"
    if "zero_optimization" in config:
        return "deepspeed"
    if any(key in config for key in ("distributed_type", "deepspeed_config", "fsdp_config", "parallelism_config", "fp8_config")):
        return "accelerate"
    if any(key.startswith("fsdp_") for key in config):
        return "fsdp"
    if any(key.startswith("parallelism_config_") for key in config):
        return "parallelism"
    return "accelerate"


def check_imports(findings: list[Finding]) -> None:
    for label, module_name in OPTIONAL_IMPORTS.items():
        if importlib.util.find_spec(module_name) is None:
            findings.append(Finding("info", f"optional package not importable: {label}"))
        else:
            findings.append(Finding("info", f"optional package importable: {label}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Accelerate backend JSON/YAML snippets without launching backends.")
    parser.add_argument("config", type=Path, help="Path to JSON/YAML config snippet")
    parser.add_argument(
        "--format",
        choices=["auto", "accelerate", "deepspeed", "fsdp", "parallelism", "quantization"],
        default="auto",
        help="Config shape to validate; auto detects common Accelerate and DeepSpeed snippets",
    )
    parser.add_argument("--check-imports", action="store_true", help="Report optional backend package importability hints")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    try:
        loaded = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to load {args.config}: {exc}", file=sys.stderr)
        return 2

    config = as_dict(loaded, "top-level config", findings)
    detected = detect_format(config, args.format)
    findings.append(Finding("info", f"validating as {detected} config"))

    if detected == "accelerate":
        validate_accelerate_config(config, findings)
    elif detected == "deepspeed":
        validate_deepspeed_json(config, findings)
    elif detected == "fsdp":
        validate_fsdp(config, findings)
    elif detected == "parallelism":
        validate_parallelism(config, None, findings)
    elif detected == "quantization":
        validate_quantization(config, findings)

    if args.check_imports:
        check_imports(findings)

    error_count = sum(1 for finding in findings if finding.level == "error")
    warning_count = sum(1 for finding in findings if finding.level == "warning")
    for finding in findings:
        print(finding)
    print(f"SUMMARY: {error_count} error(s), {warning_count} warning(s)")
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
