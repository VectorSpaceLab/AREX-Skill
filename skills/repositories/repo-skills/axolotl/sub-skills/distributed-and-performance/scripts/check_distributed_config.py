#!/usr/bin/env python3
"""Static Axolotl distributed/performance config checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal Python envs
    yaml = None

CANONICAL_ATTN = {
    "eager",
    "sdpa",
    "flash_attention_2",
    "flash_attention_3",
    "flex_attention",
    "xformers",
    "sage",
    "fp8",
}
LEGACY_ATTN_FLAGS = {
    "flash_attention": "flash_attention_2",
    "xformers_attention": "xformers",
    "sdp_attention": "sdpa",
    "flex_attention": "flex_attention",
    "sage_attention": "sage",
    "eager_attention": "eager",
}
PACKING_ATTN = {"flash_attention_2", "flash_attention_3", "flex_attention", "xformers", "sage"}
FLASH_ATTN = {"flash_attention_2", "flash_attention_3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Statically check an Axolotl YAML for common DeepSpeed, FSDP, Ray, "
            "parallelism, attention, and performance conflicts. This script only "
            "reads local YAML/JSON files."
        )
    )
    parser.add_argument("config", type=Path, help="Path to an Axolotl YAML config file.")
    parser.add_argument(
        "--world-size",
        type=int,
        default=None,
        help="Optional total launched process/GPU count for divisibility/product checks.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional base directory for resolving relative DeepSpeed config paths. Defaults to the YAML directory.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif char == "#" and quote is None:
            return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    lowered = value.lower()
    if value == "":
        return ""
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def split_key_value(content: str) -> tuple[str, str] | None:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif char == ":" and quote is None:
            return content[:index].strip(), content[index + 1 :].strip()
    return None


def simple_yaml_load(text: str) -> Any:
    parsed_lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        clean = strip_comment(raw_line)
        if not clean.strip():
            continue
        indent = len(clean) - len(clean.lstrip(" "))
        parsed_lines.append((indent, clean.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(parsed_lines):
            return {}, index
        first_indent, first_content = parsed_lines[index]
        if first_indent < indent:
            return {}, index
        if first_content.startswith("- "):
            items: list[Any] = []
            while index < len(parsed_lines):
                line_indent, content = parsed_lines[index]
                if line_indent != first_indent or not content.startswith("- "):
                    break
                item_text = content[2:].strip()
                index += 1
                if not item_text:
                    child, index = parse_block(index, first_indent + 2)
                    items.append(child)
                    continue
                key_value = split_key_value(item_text)
                if key_value:
                    key, value = key_value
                    item: dict[str, Any] = {}
                    item[key] = parse_scalar(value) if value else {}
                    while index < len(parsed_lines) and parsed_lines[index][0] > first_indent:
                        child_indent, child_content = parsed_lines[index]
                        if child_indent < first_indent + 2:
                            break
                        child_key_value = split_key_value(child_content)
                        if child_key_value:
                            child_key, child_value = child_key_value
                            item[child_key] = parse_scalar(child_value) if child_value else {}
                        index += 1
                    items.append(item)
                else:
                    items.append(parse_scalar(item_text))
            return items, index

        mapping: dict[str, Any] = {}
        while index < len(parsed_lines):
            line_indent, content = parsed_lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                index += 1
                continue
            key_value = split_key_value(content)
            if not key_value:
                index += 1
                continue
            key, value = key_value
            index += 1
            if value:
                mapping[key] = parse_scalar(value)
            elif index < len(parsed_lines) and parsed_lines[index][0] > line_indent:
                mapping[key], index = parse_block(index, parsed_lines[index][0])
            else:
                mapping[key] = {}
        return mapping, index

    result, _ = parse_block(0, 0)
    return result


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"config file does not exist: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) if yaml is not None else simple_yaml_load(text)
    except yaml.YAMLError as exc:
        fail(f"failed to parse YAML {path}: {exc}")
    except OSError as exc:
        fail(f"failed to read {path}: {exc}")
    if data is None:
        return {}
    if not isinstance(data, dict):
        fail("top-level YAML must be a mapping/object")
    return data


def as_bool(value: Any) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "none", "null"}


def as_positive_int(data: dict[str, Any], key: str, default: int = 1) -> int:
    value = data.get(key, default)
    if value in (None, False):
        return default
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return default
    return integer if integer > 0 else default


def resolve_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def check_deepspeed(data: dict[str, Any], base_dir: Path, errors: list[str], warnings: list[str]) -> None:
    deepspeed = data.get("deepspeed")
    fsdp_config = data.get("fsdp_config")
    fsdp_legacy = data.get("fsdp")
    if deepspeed and fsdp_config:
        errors.append("choose either `deepspeed` or `fsdp_config`; Axolotl configs should not enable both sharding stacks")
    if deepspeed and fsdp_legacy:
        errors.append("choose either `deepspeed` or legacy `fsdp`; do not combine DeepSpeed and FSDP")
    if isinstance(deepspeed, str):
        ds_path = resolve_path(deepspeed, base_dir)
        if not ds_path.exists():
            errors.append(f"DeepSpeed config path does not exist relative to {base_dir}: {deepspeed}")
            return
        try:
            ds_data = json.loads(ds_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"DeepSpeed config is not valid JSON: {deepspeed}: {exc}")
            return
        except OSError as exc:
            errors.append(f"failed to read DeepSpeed config {deepspeed}: {exc}")
            return
        stage = ds_data.get("zero_optimization", {}).get("stage")
        if stage is None:
            warnings.append(f"DeepSpeed config {deepspeed} has no zero_optimization.stage")
        else:
            filename = Path(deepspeed).name.lower()
            for expected_stage in (1, 2, 3):
                if f"zero{expected_stage}" in filename and int(stage) != expected_stage:
                    warnings.append(
                        f"DeepSpeed filename suggests ZeRO-{expected_stage}, but zero_optimization.stage is {stage}"
                    )
        if any("offload" in key for key in json.dumps(ds_data).lower().split('"')):
            warnings.append("DeepSpeed CPU/NVMe offload appears enabled; expect slower training and verify host memory/storage")
    elif isinstance(deepspeed, dict):
        stage = deepspeed.get("zero_optimization", {}).get("stage")
        if stage is None:
            warnings.append("inline `deepspeed` config has no zero_optimization.stage")
    elif deepspeed:
        errors.append("`deepspeed` must be a path string or mapping")


def check_fsdp(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    fsdp_config = data.get("fsdp_config")
    fsdp_version = data.get("fsdp_version")
    if data.get("fsdp"):
        warnings.append("legacy `fsdp` list is deprecated; prefer `fsdp_version: 2` with `fsdp_config`")
    if fsdp_version and not fsdp_config:
        warnings.append("`fsdp_version` is set but `fsdp_config` is missing; Axolotl treats `fsdp_config` as the FSDP signal")
    if fsdp_config and str(fsdp_version) != "2":
        warnings.append("FSDP is configured without `fsdp_version: 2`; FSDP2 is recommended for new Axolotl configs")
    if data.get("fp32_norms"):
        if not fsdp_config:
            errors.append("`fp32_norms: true` requires `fsdp_config`")
        if str(fsdp_version) != "2":
            errors.append("`fp32_norms: true` requires `fsdp_version: 2`")
    adapter = str(data.get("adapter", "")).lower()
    if adapter == "qlora" and fsdp_version and not fsdp_config:
        warnings.append("FSDP+QLoRA requires an actual `fsdp_config`; `fsdp_version` alone is insufficient")
    if isinstance(fsdp_config, dict):
        if fsdp_config.get("offload_params") and fsdp_config.get("cpu_offload_pin_memory") is False:
            warnings.append("FSDP CPU offload with pin memory disabled may use swap and can be very slow")


def check_attention(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    attn_impl = data.get("attn_implementation")
    legacy_enabled = [flag for flag in LEGACY_ATTN_FLAGS if as_bool(data.get(flag))]
    if attn_impl and legacy_enabled:
        errors.append(
            "do not combine `attn_implementation` with legacy attention flags: " + ", ".join(sorted(legacy_enabled))
        )
    if not attn_impl and legacy_enabled:
        warnings.append(
            "legacy attention flags are deprecated; replace with `attn_implementation: "
            + LEGACY_ATTN_FLAGS[legacy_enabled[0]]
            + "`"
        )
        attn_impl = LEGACY_ATTN_FLAGS[legacy_enabled[0]]
    if attn_impl and not isinstance(attn_impl, str):
        errors.append("`attn_implementation` must be a string")
    elif isinstance(attn_impl, str) and attn_impl not in CANONICAL_ATTN and "/" not in attn_impl:
        errors.append(
            "unrecognized `attn_implementation`: "
            f"{attn_impl!r}; use a canonical backend such as 'flash_attention_2', 'sdpa', 'xformers', or a hub-kernel path"
        )
    if as_bool(data.get("sample_packing")) and (not attn_impl or (attn_impl not in PACKING_ATTN and "/" not in str(attn_impl))):
        warnings.append("`sample_packing: true` should use a varlen-capable attention backend such as flash_attention_2, flex_attention, xformers, or sage")
    if as_positive_int(data, "context_parallel_size") > 1 and attn_impl not in FLASH_ATTN:
        warnings.append("`context_parallel_size > 1` usually requires `attn_implementation: flash_attention_2` for ring attention")


def check_parallelism(data: dict[str, Any], world_size: int | None, errors: list[str], warnings: list[str]) -> None:
    dp_shard = as_positive_int(data, "dp_shard_size")
    dp_replicate = as_positive_int(data, "dp_replicate_size")
    tensor_parallel = as_positive_int(data, "tensor_parallel_size")
    context_parallel = as_positive_int(data, "context_parallel_size")
    expert_parallel = as_positive_int(data, "expert_parallel_size")
    fsdp_configured = bool(data.get("fsdp_config"))
    deepspeed_configured = bool(data.get("deepspeed"))

    if data.get("sequence_parallel_degree"):
        warnings.append("`sequence_parallel_degree` is deprecated; use `context_parallel_size`")
    if deepspeed_configured and (context_parallel > 1 or expert_parallel > 1 or dp_shard > 1 or dp_replicate > 1):
        warnings.append("DeepSpeed is documented as compatible only with `tensor_parallel_size` among Axolotl N-D parallel axes; prefer FSDP for DP/CP/EP meshes")
    if (tensor_parallel > 1 or context_parallel > 1) and dp_replicate > 1 and dp_shard <= 1:
        errors.append("DDP-style replication with TP/CP is not supported; use FSDP sharding (`dp_shard_size > 1` plus `fsdp_config`) or remove TP/CP")
    if dp_shard > 1 and not fsdp_configured and not deepspeed_configured:
        warnings.append("`dp_shard_size > 1` should normally be paired with `fsdp_config` for Axolotl N-D parallelism")
    if expert_parallel > 1:
        plugins = data.get("plugins") or []
        plugin_text = " ".join(str(item) for item in plugins)
        if "expert_parallel" not in plugin_text:
            warnings.append("`expert_parallel_size > 1` usually requires the expert parallel plugin in `plugins`")
        if data.get("use_sonicmoe"):
            errors.append("`use_sonicmoe: true` is not supported with `expert_parallel_size > 1`; use ScatterMoE or disable EP")
    if world_size is not None:
        if world_size < 1:
            errors.append("`--world-size` must be positive")
            return
        if context_parallel > 1 and world_size % context_parallel != 0:
            errors.append(f"world size {world_size} is not divisible by `context_parallel_size` {context_parallel}")
        if tensor_parallel > 1 and world_size % tensor_parallel != 0:
            warnings.append(f"world size {world_size} is not divisible by `tensor_parallel_size` {tensor_parallel}")
        if expert_parallel > 1:
            product = expert_parallel * dp_shard * tensor_parallel * context_parallel
            if product != world_size:
                errors.append(
                    "when expert parallel is active, expected "
                    "expert_parallel_size * dp_shard_size * tensor_parallel_size * context_parallel_size "
                    f"to equal world size; got {expert_parallel} * {dp_shard} * {tensor_parallel} * {context_parallel} = {product}, world size {world_size}"
                )
        elif fsdp_configured and not deepspeed_configured:
            product = dp_shard * dp_replicate * tensor_parallel * context_parallel
            if product > 1 and product != world_size:
                warnings.append(
                    "parallelism axes product does not match world size: "
                    f"dp_shard({dp_shard}) * dp_replicate({dp_replicate}) * tensor({tensor_parallel}) * context({context_parallel}) = {product}, world size {world_size}"
                )
    if context_parallel > 1 and as_positive_int(data, "micro_batch_size") > 1:
        warnings.append("Axolotl context-parallel examples use `micro_batch_size: 1`; verify memory before increasing it")


def check_ray(data: dict[str, Any], world_size: int | None, warnings: list[str]) -> None:
    if not as_bool(data.get("use_ray")):
        return
    ray_workers = data.get("ray_num_workers")
    if ray_workers is None:
        warnings.append("`use_ray: true` is set without `ray_num_workers`; ensure CLI or defaults provide the intended worker count")
        return
    try:
        workers = int(ray_workers)
    except (TypeError, ValueError):
        warnings.append("`ray_num_workers` should be an integer worker/GPU count")
        return
    if workers < 1:
        warnings.append("`ray_num_workers` should be positive")
    if world_size is not None and workers != world_size:
        warnings.append(f"`ray_num_workers` ({workers}) differs from supplied `--world-size` ({world_size})")


def check_performance(data: dict[str, Any], warnings: list[str]) -> None:
    if data.get("fp8") and str(data.get("fsdp_version")) == "2" and not data.get("fp8_enable_fsdp_float8_all_gather"):
        warnings.append("FP8 with FSDP2 often pairs with `fp8_enable_fsdp_float8_all_gather: true`; benchmark both settings")
    if data.get("activation_offloading") and not data.get("gradient_checkpointing"):
        warnings.append("activation offloading should be paired with `gradient_checkpointing: true`")
    if data.get("profiler_steps") and int(data.get("profiler_steps") or 0) > 100:
        warnings.append("large `profiler_steps` values can distort performance and create large profiler outputs")
    if data.get("liger_rms_norm") and as_positive_int(data, "tensor_parallel_size") > 1:
        warnings.append("Liger RMSNorm has tensor-parallel caveats; verify the selected Liger flags against Axolotl integration validation")
    if data.get("liger_fused_linear_cross_entropy") and as_positive_int(data, "tensor_parallel_size") > 1:
        warnings.append("Liger fused linear cross entropy has tensor-parallel caveats; consider disabling it for TP runs")


def main() -> int:
    args = parse_args()
    config_path = args.config.resolve()
    data = load_yaml(config_path)
    base_dir = (args.repo_root.resolve() if args.repo_root else config_path.parent)
    errors: list[str] = []
    warnings: list[str] = []

    check_deepspeed(data, base_dir, errors, warnings)
    check_fsdp(data, errors, warnings)
    check_attention(data, errors, warnings)
    check_parallelism(data, args.world_size, errors, warnings)
    check_ray(data, args.world_size, warnings)
    check_performance(data, warnings)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"OK: no blocking distributed config errors ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
