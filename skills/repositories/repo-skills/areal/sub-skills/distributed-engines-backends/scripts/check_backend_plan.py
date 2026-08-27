#!/usr/bin/env python3
"""Safe AReaL backend-plan checker.

This helper parses AReaL per-engine backend strings and checks resource,
LoRA, weight-update, and obvious backend-compatibility constraints. It does not
start training, launch inference services, download models, or prove GPU backend
runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BACKENDS_INFER = {"sglang", "vllm"}
BACKENDS_TRAIN = {"fsdp", "megatron", "archon"}
ALL_BACKENDS = BACKENDS_INFER | BACKENDS_TRAIN

ROLE_FLAGS = ("rollout", "actor", "critic", "ref", "teacher")


@dataclass
class Allocation:
    role: str
    spec: str
    backend: str
    dp: int = 1
    tp: int = 1
    pp: int = 1
    cp: int = 1
    ep: int = 1
    etp: int = 1
    hybrid: bool = False
    ffn_dp: int | None = None
    ffn_tp: int | None = None
    ffn_pp: int | None = None
    ffn_ep: int | None = None

    @property
    def world_size(self) -> int:
        return self.dp * self.tp * self.pp * self.cp

    @property
    def dims(self) -> str:
        parts = []
        if self.dp != 1:
            parts.append(f"d{self.dp}")
        if self.pp != 1:
            parts.append(f"p{self.pp}")
        if self.tp != 1:
            parts.append(f"t{self.tp}")
        if self.cp != 1:
            parts.append(f"c{self.cp}")
        if self.ep != 1:
            parts.append(f"e{self.ep}")
        if self.etp != 1:
            parts.append(f"etp{self.etp}")
        return "".join(parts) or "d1"


@dataclass
class CheckResult:
    allocations: dict[str, Allocation]
    separated_gpu_demand: int
    effective_gpu_demand: int
    cluster_gpus: int | None
    errors: list[str]
    warnings: list[str]
    notes: list[str]
    env: dict[str, Any] | None = None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _parse_int(value: Any, name: str, errors: list[str]) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} must be an integer, got {value!r}.")
        return None
    if parsed < 0:
        errors.append(f"{name} must be non-negative, got {parsed}.")
    return parsed


def _flatten_overrides(overrides: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in overrides:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _load_config(path: str, errors: list[str]) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        errors.append(f"Config file not found: {path}")
        return {}
    try:
        text = p.read_text()
        if p.suffix.lower() == ".json":
            data = json.loads(text)
        elif p.suffix.lower() in {".toml", ".tml"}:
            import tomllib

            data = tomllib.loads(text)
        else:
            try:
                import yaml  # type: ignore
            except Exception as exc:  # pragma: no cover - depends on environment
                errors.append(
                    "YAML config parsing needs PyYAML. Either install PyYAML or pass "
                    "backend strings as CLI overrides. Import error: " + repr(exc)
                )
                return {}
            data = yaml.safe_load(text) or {}
    except Exception as exc:
        errors.append(f"Failed to parse config {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"Config {path} did not parse to a mapping.")
        return {}
    return data


def _get_nested(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _collect_inputs(args: argparse.Namespace, errors: list[str]) -> dict[str, Any]:
    cfg = _load_config(args.config, errors)
    ov = _flatten_overrides(args.overrides)
    values: dict[str, Any] = {}

    for role in ROLE_FLAGS:
        cli_value = getattr(args, role)
        values[f"{role}.backend"] = (
            cli_value
            if cli_value is not None
            else ov.get(f"{role}.backend", _get_nested(cfg, f"{role}.backend", None))
        )

    values["actor.weight_update_mode"] = (
        args.weight_update_mode
        or ov.get("actor.weight_update_mode")
        or ov.get("weight_update_mode")
        or _get_nested(cfg, "actor.weight_update_mode", None)
        or "xccl"
    )
    values["actor.use_lora"] = (
        args.use_lora
        or _parse_bool(ov.get("actor.use_lora"))
        or _parse_bool(ov.get("use_lora"))
        or _parse_bool(_get_nested(cfg, "actor.use_lora", False))
    )
    values["rollout.use_lora"] = (
        _parse_bool(ov.get("rollout.use_lora"))
        or _parse_bool(_get_nested(cfg, "rollout.use_lora", False))
    )
    values["actor.megatron.bridge_type"] = (
        args.bridge_type
        or ov.get("actor.megatron.bridge_type")
        or _get_nested(cfg, "actor.megatron.bridge_type", None)
        or "mbridge"
    )
    values["actor.enable_tree_training"] = (
        _parse_bool(ov.get("actor.enable_tree_training"))
        or _parse_bool(_get_nested(cfg, "actor.enable_tree_training", False))
    )
    values["actor.megatron.use_deterministic_algorithms"] = (
        _parse_bool(ov.get("actor.megatron.use_deterministic_algorithms"))
        or _parse_bool(
            _get_nested(cfg, "actor.megatron.use_deterministic_algorithms", False)
        )
    )
    values["actor.archon.fp8_config.mode"] = (
        ov.get("actor.archon.fp8_config.mode")
        or _get_nested(cfg, "actor.archon.fp8_config.mode", None)
        or _get_nested(cfg, "actor.archon.fp8_config.mode", None)
    )
    values["actor.dtype"] = (
        ov.get("actor.dtype") or _get_nested(cfg, "actor.dtype", None) or "bfloat16"
    )

    n_nodes = args.n_nodes or ov.get("cluster.n_nodes") or _get_nested(cfg, "cluster.n_nodes")
    n_gpus = (
        args.n_gpus_per_node
        or ov.get("cluster.n_gpus_per_node")
        or _get_nested(cfg, "cluster.n_gpus_per_node")
    )
    total = args.cluster_gpus or ov.get("cluster.total_gpus") or ov.get("cluster.gpus")
    parsed_total = _parse_int(total, "cluster total GPUs", errors) if total is not None else None
    parsed_nodes = _parse_int(n_nodes, "cluster.n_nodes", errors) if n_nodes is not None else None
    parsed_gpn = (
        _parse_int(n_gpus, "cluster.n_gpus_per_node", errors)
        if n_gpus is not None
        else None
    )
    if parsed_total is None and parsed_nodes is not None and parsed_gpn is not None:
        parsed_total = parsed_nodes * parsed_gpn
    values["cluster_gpus"] = parsed_total
    values["n_nodes"] = parsed_nodes
    values["n_gpus_per_node"] = parsed_gpn
    values["colocated_actor_rollout"] = args.colocated_actor_rollout or _parse_bool(
        ov.get("actor_rollout_colocated")
    )
    return values


def _parse_dims(text: str, allowed: set[str], label: str, errors: list[str]) -> dict[str, int]:
    out = {"d": 1, "t": 1, "p": 1, "c": 1, "e": 1}
    pos = 0
    for match in re.finditer(r"([dtpce])([1-9][0-9]*)", text):
        if match.start() != pos:
            errors.append(f"Invalid dimension syntax in {label!r} near {text[pos:match.start()]!r}.")
            return out
        dim = match.group(1)
        if dim not in allowed:
            errors.append(
                f"Dimension {dim!r} is not allowed in {label}; allowed: {''.join(sorted(allowed))}."
            )
        if out[dim] != 1:
            errors.append(f"Duplicate dimension {dim!r} in {label!r}.")
        out[dim] = int(match.group(2))
        pos = match.end()
    if pos != len(text):
        errors.append(f"Invalid trailing dimension syntax in {label!r}: {text[pos:]!r}.")
    if pos == 0 and text:
        errors.append(f"No dimensions parsed in {label!r}.")
    return out


def parse_allocation(role: str, spec: str) -> tuple[Allocation | None, list[str]]:
    errors: list[str] = []
    original = spec
    spec = spec.strip().replace(" ", "")
    if not spec:
        return None, errors
    if "+" in spec:
        errors.append(
            f"{role}.backend contains '+'. ModelAllocation.from_str() expects one component; "
            "use separate per-engine backend fields instead."
        )
        return None, errors

    match = re.match(
        r"^(?P<backend>[a-z][a-z0-9_-]*)(?:\[[A-Za-z_][A-Za-z0-9_]*\]|\([A-Za-z_][A-Za-z0-9_]*\))?:(?P<body>.+)$",
        spec,
    )
    if match is None:
        if re.fullmatch(r"[dtpce][0-9].*", spec):
            errors.append(
                f"{role}.backend must include an explicit backend prefix, e.g. 'fsdp:d4' not {original!r}."
            )
        else:
            errors.append(f"Could not parse {role}.backend={original!r}.")
        return None, errors

    backend = match.group("backend")
    body = match.group("body")
    if backend not in ALL_BACKENDS:
        errors.append(f"Unknown backend {backend!r}; expected one of {sorted(ALL_BACKENDS)}.")
        return None, errors

    if "attn:" in body or "ffn:" in body:
        if backend not in {"megatron", "archon"}:
            errors.append("Hybrid attn/ffn MoE syntax is only for Megatron or Archon training backends.")
            return None, errors
        if body.startswith("(") and body.endswith(")"):
            body = body[1:-1]
        hm = re.fullmatch(r"attn:(?P<attn>[dtpc0-9]+)\|ffn:(?P<ffn>[dtpe0-9]+)", body)
        if hm is None:
            errors.append(
                "Hybrid MoE syntax must look like backend:(attn:d...p...t...c...|ffn:d...p...t...e...)."
            )
            return None, errors
        attn = _parse_dims(hm.group("attn"), {"d", "t", "p", "c"}, "attn", errors)
        ffn = _parse_dims(hm.group("ffn"), {"d", "t", "p", "e"}, "ffn", errors)
        if errors:
            return None, errors
        if ffn["p"] != 1 and ffn["p"] != attn["p"]:
            errors.append(
                f"Hybrid MoE requires identical PP for attn and ffn; got attn p{attn['p']} and ffn p{ffn['p']}."
            )
        ffn_pp = attn["p"] if ffn["p"] == 1 else ffn["p"]
        attn_world = attn["d"] * attn["t"] * attn["p"] * attn["c"]
        ffn_non_dp = ffn["t"] * ffn_pp * ffn["e"]
        ffn_dp = ffn["d"]
        # Match AReaL's parser behavior: omitted ffn d defaults to 1 at grammar
        # level, so derive only when the user did not write a d-dimension.
        if "d" not in re.findall(r"([dtpe])(?:[1-9][0-9]*)", hm.group("ffn")):
            if attn_world % ffn_non_dp != 0:
                errors.append(
                    f"Cannot derive ffn dp: attn world {attn_world} is not divisible by ffn t*p*e {ffn_non_dp}."
                )
            else:
                ffn_dp = attn_world // ffn_non_dp
        ffn_world = ffn_dp * ffn_non_dp
        if attn_world != ffn_world:
            errors.append(
                f"Hybrid MoE world sizes must match; attn world {attn_world}, ffn world {ffn_world}."
            )
        alloc = Allocation(
            role=role,
            spec=original,
            backend=backend,
            dp=attn["d"],
            tp=attn["t"],
            pp=attn["p"],
            cp=attn["c"],
            ep=ffn["e"],
            etp=ffn["t"],
            hybrid=True,
            ffn_dp=ffn_dp,
            ffn_tp=ffn["t"],
            ffn_pp=ffn_pp,
            ffn_ep=ffn["e"],
        )
        return alloc, errors

    if backend in BACKENDS_INFER:
        dims = _parse_dims(body, {"d", "t", "p"}, role, errors)
    else:
        dims = _parse_dims(body, {"d", "t", "p", "c", "e"}, role, errors)
    if backend == "fsdp" and (dims["p"] > 1 or dims["e"] > 1):
        errors.append("FSDP backend only supports data/tensor/context parallelism; p/e are invalid.")
    alloc = Allocation(
        role=role,
        spec=original,
        backend=backend,
        dp=dims["d"],
        tp=dims["t"],
        pp=dims["p"],
        cp=dims["c"],
        ep=dims["e"],
    )
    return alloc, errors


def _validate_archon(alloc: Allocation, errors: list[str], warnings: list[str]) -> None:
    if alloc.backend != "archon":
        return
    if alloc.etp not in (1, alloc.tp):
        errors.append(
            f"Archon requires expert tensor parallelism etp to be 1 or equal to tp; got etp={alloc.etp}, tp={alloc.tp}."
        )
    if alloc.ep > 1:
        if alloc.etp == alloc.tp:
            if alloc.ep % alloc.cp != 0 or (alloc.dp * alloc.cp) % alloc.ep != 0:
                errors.append(
                    "Archon EP/ETP constraint failed for etp=tp: ep must be divisible by cp and dp*cp must be divisible by ep."
                )
        else:
            if alloc.ep % (alloc.cp * alloc.tp) != 0 or (alloc.dp * alloc.cp * alloc.tp) % alloc.ep != 0:
                errors.append(
                    "Archon EP constraint failed for etp=1: ep must be divisible by cp*tp and dp*cp*tp must be divisible by ep."
                )
    if alloc.pp > 1:
        warnings.append(
            "Archon PP uses pipeline schedules; set actor.mb_spec.n_mbs high enough for all stages to avoid warmup activation spikes."
        )


def _visible_cuda_count(env: dict[str, Any] | None) -> int | None:
    if not env:
        return None
    torch_info = env.get("torch") or {}
    count = torch_info.get("cuda_device_count")
    if isinstance(count, int):
        return count
    cvd = env.get("CUDA_VISIBLE_DEVICES")
    if isinstance(cvd, str) and cvd.strip():
        return len([x for x in cvd.split(",") if x.strip()])
    return None


def probe_env() -> dict[str, Any]:
    result: dict[str, Any] = {
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "PYTORCH_CUDA_ALLOC_CONF": os.environ.get("PYTORCH_CUDA_ALLOC_CONF", ""),
        "note": "Environment probes do not verify that FSDP/Megatron/Archon/SGLang/vLLM jobs run.",
    }
    try:
        import torch  # type: ignore

        result["torch"] = {
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            result["torch"]["device_names"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]
    except Exception as exc:
        result["torch"] = {"import_error": repr(exc)}

    if shutil.which("nvidia-smi"):
        try:
            cp = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            result["nvidia_smi"] = {
                "returncode": cp.returncode,
                "stdout": cp.stdout.strip(),
                "stderr": cp.stderr.strip(),
            }
        except Exception as exc:
            result["nvidia_smi"] = {"error": repr(exc)}
    return result


def validate(values: dict[str, Any], env: dict[str, Any] | None) -> CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = [
        "This checker parses and sanity-checks a plan only; it is not GPU backend runtime verification."
    ]
    allocations: dict[str, Allocation] = {}

    for role in ROLE_FLAGS:
        raw = values.get(f"{role}.backend")
        if raw is None or str(raw).strip() == "":
            continue
        alloc, parse_errors = parse_allocation(role, str(raw))
        errors.extend([f"{role}: {e}" for e in parse_errors])
        if alloc is not None:
            allocations[role] = alloc
            _validate_archon(alloc, errors, warnings)

    actor = allocations.get("actor")
    rollout = allocations.get("rollout")
    mode = str(values.get("actor.weight_update_mode", "xccl")).lower()
    if mode not in {"disk", "xccl", "awex"}:
        errors.append(f"actor.weight_update_mode must be disk, xccl, or awex; got {mode!r}.")

    # Basic component/backend role checks.
    if actor and actor.backend not in BACKENDS_TRAIN:
        errors.append(f"actor.backend must be a training backend, got {actor.backend!r}.")
    if rollout and rollout.backend not in BACKENDS_INFER:
        errors.append(f"rollout.backend must be an inference backend, got {rollout.backend!r}.")
    for role in ("critic", "ref", "teacher"):
        alloc = allocations.get(role)
        if alloc and alloc.backend not in BACKENDS_TRAIN | BACKENDS_INFER:
            errors.append(f"{role}.backend has unknown backend {alloc.backend!r}.")

    if actor and actor.backend == "megatron":
        bridge = str(values.get("actor.megatron.bridge_type", "mbridge"))
        if bridge not in {"mbridge", "megatron-bridge"}:
            errors.append("actor.megatron.bridge_type must be 'mbridge' or 'megatron-bridge'.")
        if actor.ep > 1 and not _parse_bool(values.get("actor.megatron.use_deterministic_algorithms")):
            warnings.append(
                "Megatron MoE plans are more stable with actor.megatron.use_deterministic_algorithms=True, at a throughput cost."
            )
        if values.get("actor.enable_tree_training") and bridge != "mbridge":
            errors.append("Megatron tree training currently supports bridge_type='mbridge' only.")

    if actor and actor.backend == "archon":
        fp8_mode = values.get("actor.archon.fp8_config.mode")
        if fp8_mode and str(fp8_mode) != "disabled":
            if str(values.get("actor.dtype", "bfloat16")) not in {"bfloat16", "bf16"}:
                errors.append("Archon FP8 training requires actor.dtype=bfloat16.")
            warnings.append(
                "Archon blockwise FP8 also needs compatible Hopper-class hardware and 128-aligned local weight shards."
            )

    use_lora = bool(values.get("actor.use_lora") or values.get("rollout.use_lora"))
    if use_lora:
        if actor is None or rollout is None:
            errors.append("LoRA planning needs both actor.backend and rollout.backend.")
        elif rollout.backend not in {"sglang", "vllm"}:
            errors.append("AReaL LoRA rollout requires SGLang or vLLM.")
        elif actor.backend == "fsdp":
            if rollout.backend == "sglang" and mode != "disk":
                errors.append(
                    "SGLang distributed XCCL weight update does not support LoRA; set actor.weight_update_mode=disk."
                )
        elif actor.backend == "megatron":
            if rollout.backend != "vllm":
                errors.append("Megatron LoRA is supported with vLLM rollout, not SGLang rollout.")
            if str(values.get("actor.megatron.bridge_type")) != "megatron-bridge":
                errors.append("Megatron LoRA requires actor.megatron.bridge_type=megatron-bridge.")
        elif actor.backend == "archon":
            errors.append("Archon LoRA is not supported.")

    if mode == "awex":
        if actor is None or rollout is None:
            errors.append("AWEX requires both actor.backend and rollout.backend.")
        else:
            if actor.backend != "megatron" or rollout.backend != "sglang":
                errors.append("AWEX requires a Megatron actor and an SGLang rollout.")
            if use_lora:
                errors.append("Do not combine AWEX with LoRA unless you have explicit project evidence for that path.")
            if not values.get("colocated_actor_rollout"):
                warnings.append("AWEX targets colocated actor-rollout setups; pass --colocated-actor-rollout when that is intentional.")
        alloc_conf = os.environ.get("PYTORCH_CUDA_ALLOC_CONF", "")
        if "expandable_segments" in alloc_conf.lower():
            errors.append(
                "AWEX SGLang plugin rejects PYTORCH_CUDA_ALLOC_CONF with expandable_segments; move role-specific allocator config to scheduling_spec.env_vars."
            )
    elif mode == "disk":
        if values.get("n_nodes", 1) and int(values.get("n_nodes") or 1) > 1:
            warnings.append("Disk weight updates need cluster.fileroot on shared storage visible to all nodes.")
    elif mode == "xccl":
        notes.append("XCCL/NCCL updates can reduce disk I/O but use extra GPU buffers; tune weight_chunked_mem_mb if OOM occurs.")

    separated = sum(a.world_size for a in allocations.values())
    effective = separated
    if values.get("colocated_actor_rollout") and actor and rollout:
        effective = separated - actor.world_size - rollout.world_size + max(actor.world_size, rollout.world_size)
        if actor.world_size != rollout.world_size:
            warnings.append(
                f"Actor/rollout colocation has unequal world sizes ({actor.world_size} vs {rollout.world_size}); verify scheduler placement explicitly."
            )

    cluster_gpus = values.get("cluster_gpus")
    if cluster_gpus is not None and effective > int(cluster_gpus):
        errors.append(
            f"Planned effective GPU demand {effective} exceeds cluster GPUs {cluster_gpus}."
        )
    visible = _visible_cuda_count(env)
    if visible is not None and effective > visible:
        warnings.append(
            f"Planned effective GPU demand {effective} exceeds currently visible CUDA devices {visible}; this may be okay on Ray/Slurm multi-node jobs but is not runnable in this shell."
        )

    return CheckResult(
        allocations=allocations,
        separated_gpu_demand=separated,
        effective_gpu_demand=effective,
        cluster_gpus=cluster_gpus,
        errors=errors,
        warnings=warnings,
        notes=notes,
        env=env,
    )


def print_text(result: CheckResult) -> None:
    print("AReaL backend plan check")
    print("========================")
    if result.allocations:
        print("\nAllocations:")
        for role, alloc in result.allocations.items():
            extra = ""
            if alloc.hybrid:
                extra = f"; ffn=d{alloc.ffn_dp}p{alloc.ffn_pp}t{alloc.ffn_tp}e{alloc.ffn_ep}"
            print(
                f"- {role}: {alloc.spec} -> backend={alloc.backend}, world={alloc.world_size}, dims={alloc.dims}{extra}"
            )
    else:
        print("\nNo backend strings supplied.")
    print(f"\nSeparated GPU demand: {result.separated_gpu_demand}")
    print(f"Effective GPU demand:  {result.effective_gpu_demand}")
    if result.cluster_gpus is not None:
        print(f"Cluster GPUs:          {result.cluster_gpus}")
    if result.env:
        print("\nEnvironment probe:")
        print(json.dumps(result.env, indent=2, sort_keys=True))
    if result.errors:
        print("\nErrors:")
        for item in result.errors:
            print(f"- {item}")
    if result.warnings:
        print("\nWarnings:")
        for item in result.warnings:
            print(f"- {item}")
    if result.notes:
        print("\nNotes:")
        for item in result.notes:
            print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse AReaL backend strings and check GPU demand, LoRA, weight-update, "
            "and obvious backend constraints without launching training or services."
        )
    )
    parser.add_argument("overrides", nargs="*", help="Hydra-style overrides such as actor.backend=fsdp:d4")
    parser.add_argument("--config", default="", help="Optional JSON/TOML/YAML config to inspect safely")
    for role in ROLE_FLAGS:
        parser.add_argument(f"--{role}", help=f"{role}.backend string")
    parser.add_argument("--cluster-gpus", help="Total cluster GPUs available")
    parser.add_argument("--n-nodes", help="cluster.n_nodes")
    parser.add_argument("--n-gpus-per-node", help="cluster.n_gpus_per_node")
    parser.add_argument(
        "--weight-update-mode",
        choices=["disk", "xccl", "awex"],
        help="actor.weight_update_mode (default: xccl)",
    )
    parser.add_argument("--use-lora", action="store_true", help="Assume actor/rollout LoRA is enabled")
    parser.add_argument("--bridge-type", choices=["mbridge", "megatron-bridge"], help="actor.megatron.bridge_type")
    parser.add_argument(
        "--colocated-actor-rollout",
        action="store_true",
        help="Treat actor and rollout as intentionally sharing the same GPU placement for effective demand",
    )
    parser.add_argument(
        "--probe-env",
        action="store_true",
        help="Safely inspect CUDA visibility, torch import, and nvidia-smi; still not backend runtime verification",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    args = parser.parse_args(argv)
    input_errors: list[str] = []
    values = _collect_inputs(args, input_errors)
    env = probe_env() if args.probe_env else None
    result = validate(values, env)
    result.errors[:0] = input_errors

    if args.json:
        payload = asdict(result)
        payload["allocations"] = {k: asdict(v) for k, v in result.allocations.items()}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 2 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
