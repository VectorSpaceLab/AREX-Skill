# Backend planning for AReaL

This reference is self-contained operating guidance for AReaL backend choices. It distills the repository docs, source, and tests into runtime rules; do not reopen the source checkout to use it.

## What this owns

- Per-engine backend strings for `rollout`, `actor`, `critic`, `ref`, and `teacher` roles.
- SGLang/vLLM inference backend selection and installation variants.
- FSDP2, Megatron, and Archon training backend selection.
- GPU world-size calculation, parallel dimensions, hybrid MoE syntax, and Ray/Slurm placement assumptions.
- LoRA, FP8, Torch Memory Saver, CUDA/NCCL, and backend optional-dependency prerequisites.

Route full experiment command choice to `post-training-experiments`; route service lifecycle to `services-cli-operations`.

## Backend install variants

AReaL has mutually different inference-backend environments. Choose the variant before installing or asking the user to install.

| Need | Preferred variant | Notes |
|---|---|---|
| Default CUDA training + SGLang rollout | `uv sync --extra cuda` or runtime image tagged for SGLang | Installs CUDA training packages plus SGLang. Linux x86_64 + CUDA-compatible NVIDIA driver required for GPU execution. |
| vLLM rollout | vLLM-specific pyproject/lock variant, then `uv sync --extra cuda`, or runtime image tagged for vLLM | SGLang and vLLM pin incompatible Torch/TorchAO stacks; do not mix them casually in one env. |
| Training packages without inference backend | `cuda-train` extra | Useful when rollout is external or service-managed elsewhere. |
| Torch Memory Saver/offload | `tms` extra | Needed for `offload: true` paths using torch-memory-saver. |
| Megatron backend | `megatron` or `cuda-train`/`cuda` extras plus compiled CUDA packages where required | Megatron-Core and Megatron-Bridge are Python deps; optimized MoE/FP8 often needs additional compiled packages and correct GPU architecture. |
| CPU-only inspection/dev | base install or `uv sync` without CUDA | Fine for import/config/script checks only. It does **not** prove SGLang, vLLM, FSDP, Megatron, Archon, NCCL, Ray, or Slurm runtime behavior. |

Safe validation commands:

```bash
# No training or services: parse backend strings and optional CUDA visibility.
python scripts/check_backend_plan.py --probe-env \
  rollout.backend=sglang:d2t4 actor.backend=fsdp:d8 \
  cluster.n_nodes=2 cluster.n_gpus_per_node=8

# Import checks are only surface checks, not backend runtime checks.
python - <<'PY'
import importlib.util
for name in ['areal', 'torch', 'sglang', 'vllm', 'megatron']:
    print(name, bool(importlib.util.find_spec(name)))
PY
```

## Per-engine backend fields

AReaL's modern configuration uses explicit per-engine `backend` fields:

```yaml
rollout:
  backend: "sglang:d2t4"
actor:
  backend: "fsdp:d8"
critic:
  backend: ""   # if this role is enabled and empty, it inherits actor.backend
ref:
  backend: ""   # if this role is enabled and empty, it inherits actor.backend
```

The top-level `allocation_mode` string is deprecated and retained for legacy SPMD launchers. Single-controller scheduling uses per-engine backend fields. `ModelAllocation.from_str()` accepts one component only; do not put `+`-separated multi-component strings into an engine's `backend` field.

### Syntax

```text
<backend>:<dims>
```

Explicit backend prefix is required. Bare strings like `d4t2` are invalid; use `fsdp:d4t2`, `megatron:d2p2t4`, `archon:d2`, `sglang:d4`, or `vllm:d2t4`.

| Dimension | Abbrev | Meaning | World-size effect | Valid for |
|---|---:|---|---:|---|
| Data parallel | `d` | Model replicas / data shards | multiplies | all backends |
| Tensor parallel | `t` | Shard tensor ops or inference worker TP | multiplies | all backends |
| Pipeline parallel | `p` | Split layers/stages | multiplies | SGLang/vLLM inference; Megatron/Archon training |
| Context parallel | `c` | Split sequence/context length | multiplies | FSDP/Megatron/Archon training |
| Expert parallel | `e` | Split MoE experts | does not multiply AReaL world directly; overlaid on mesh | Megatron/Archon training |

World size for a role is:

```text
world_size = d * t * p * c
```

Expert parallelism changes expert placement but not the role's `world_size` formula.

### Examples

| String | Role type | GPUs | Use |
|---|---|---:|---|
| `sglang:d4` | inference | 4 | four independent SGLang server replicas |
| `sglang:d2t4` | inference | 8 | two SGLang replicas, each tensor-parallel across four GPUs |
| `vllm:d2t4p2` | inference | 16 | two vLLM replicas, TP=4, PP=2 |
| `fsdp:d8` | training | 8 | FSDP2 data/FSDP sharding across eight ranks |
| `fsdp:d2c2` | training | 4 | FSDP2 plus Ulysses context/sequence parallelism |
| `megatron:d2p2t4` | training | 16 | Megatron DP=2, PP=2, TP=4 |
| `archon:d4p2t2` | training | 16 | Archon DP-shard=4, PP=2, TP=2 |
| `megatron:(attn:d4p2t2c2|ffn:d2p2t4e2)` | training MoE | 32 | hybrid MoE attention/FFN placement |

Use the checker to catch invalid combinations:

```bash
python scripts/check_backend_plan.py \
  rollout.backend=vllm:d2t4 actor.backend=megatron:d2p2t4 \
  cluster.n_nodes=4 cluster.n_gpus_per_node=8
```

## Backend capability matrix

| Backend | Role | Strengths | Important constraints |
|---|---|---|---|
| SGLang | inference | Default AReaL rollout backend, supports OpenAI-like HTTP generation, routed-experts return for MoE, memory controls such as `sglang.mem_fraction_static` | Requires SGLang runtime version compatible with AReaL. AReaL allocation `d` launches server replicas; SGLang internal DP attention/EP settings do not change AReaL GPU allocation. Beam search is not supported by the SGLang remote backend. LoRA over distributed XCCL is not supported; use disk update for SGLang LoRA. |
| vLLM | inference | vLLM OpenAI-compatible completions/chat endpoints, LoRA update endpoints, optional sleep/wake memory control | Uses separate dependency variant. AReaL disables prefix caching by default for RL correctness. Requires matching vLLM/Torch/TorchAO versions. |
| FSDP2 | training | Production default for HuggingFace models, FSDP2 sharding, optional tensor/context parallelism, LoRA support, VLM support | Supports only `d`, `t`, `c`; `p` and `e` are invalid. Requires Torch FSDP2 support. `memory_efficient_load` cannot combine with `init_from_scratch`. Tree training cannot combine with sequence/context parallel size > 1 in the FSDP path. |
| Megatron | training | Production large-model/MoE backend with DP/TP/PP/CP/EP, virtual PP, distributed optimizer, deterministic MoE option, FP8 paths | Requires Megatron dependencies and model bridge support. `bridge_type` is `mbridge` by default; prefer `megatron-bridge` for new workflows and LoRA, but tree training currently supports `mbridge` only. CP is unsupported for VLMs and padded-sequence GDN/SSM models. |
| Archon | training | Experimental PyTorch-native engine with DP/TP/PP/CP/EP/ETP, torch.compile, flexible activation checkpointing, async checkpoint saving, Qwen-family built-ins | Experimental. Built-in models are limited to supported Archon specs. LoRA is not supported. PP with tied embeddings is unsupported. Tree training warns/overrides attention type. FP8 blockwise requires BF16 training and compatible hardware/aligned local shards. |

## Hybrid MoE syntax

Use hybrid syntax for Megatron or Archon MoE models when attention and FFN/expert modules need different TP/CP/EP placement:

```text
megatron:(attn:d4p2t2c2|ffn:d2p2t4e2)
archon:(attn:d1p4t2c2|ffn:d1p4t1e4)
```

Rules:

- `attn:` allows `d`, `p`, `t`, `c`.
- `ffn:` allows `d`, `p`, `t`, `e`; `e` is expert parallelism and is only valid in `ffn`.
- Attention and FFN pipeline size must match. If `ffn:p` is omitted, it inherits `attn:p`.
- Attention world and FFN world must match. If `ffn:d` is omitted, derive it from `attn_world / (ffn_t * ffn_p * ffn_e)`.
- For Archon, expert tensor parallelism (`ffn:t`, stored as ETP) must be either `1` or equal to attention TP. Archon EP divisibility follows its DeviceMesh rules; use the checker before sending a run.

## FSDP2 planning notes

Use FSDP2 when you want broad HuggingFace model compatibility and no PP/EP requirement.

Key fields:

```yaml
actor:
  backend: "fsdp:d4t2"        # d/t/c only
  dtype: bfloat16              # compute dtype
  optimizer_dtype: float32     # default fp32 master weights
  gradient_checkpointing: true
  fsdp:
    memory_efficient_load: true
    offload_params: false
    per_layer_optim_step: false
    optim_step_prefetch_layers: 1
```

Memory/compatibility notes:

- `optimizer_dtype: float32` stores fp32 master weights and Adam states; forward/backward still use `dtype` through FSDP2 mixed precision.
- To reduce optimizer memory, pair `optimizer_dtype: bfloat16` with `actor.optimizer.type: adam_bf16`; do not pair plain `adam` with bf16 optimizer storage.
- `fsdp.memory_efficient_load: true` reduces GPU initialization memory for large LLMs by CPU/meta loading and rank-0 broadcast, but VLMs load independently on CPU and still need CPU/disk bandwidth.
- `fsdp.per_layer_optim_step: true` streams Adam states layer-by-layer and requires optimizer type `adam`.
- Ulysses context parallelism (`c`) must divide the model attention-head count; invalid CP often appears as shape or collective failures.

## Megatron planning notes

Use Megatron when the model and environment can support Megatron-Core and you need PP/EP/MoE scaling.

Key fields:

```yaml
actor:
  backend: "megatron:d2p2t4"
  megatron:
    bridge_type: megatron-bridge  # mbridge is default/backward compatible
    virtual_pipeline_parallel_size: 1
    use_deterministic_algorithms: true  # recommended for MoE stability
    use_bridge_for_update_weights: false
```

Bridge choice:

- `mbridge`: default/backward-compatible and still required for tree-training in Megatron.
- `megatron-bridge`: preferred for new GPU training, newer model architectures, and Megatron LoRA; supports optimized HF load/save paths.
- If `use_bridge_for_update_weights: true` but the path is unsupported (FP8/quantized, LoRA, or non-bridge backend), runtime falls back to registry conversion and logs why.

Other notes:

- Megatron initializes model-parallel groups in `tp-cp-ep-dp-pp` order.
- `virtual_pipeline_parallel_size > 1` requires `p > 1`.
- `actor.optimizer.type: adam_bf16` is normalized to Megatron precision-aware optimizer settings.
- Tree training with Megatron requires `bridge_type: mbridge` and currently does not support CP.
- For VLMs and some padded-sequence model types, CP > 1 is unsupported.

## Archon planning notes

Use Archon when you want PyTorch-native distributed internals, full 5D/ETP flexibility, or easier experimentation than Megatron, while accepting experimental status.

Key fields:

```yaml
actor:
  backend: "archon:d4p2t2"
  gradient_checkpointing: true
  archon:
    pp_schedule: Interleaved1F1B
    enable_compile: true
    ac_mode: selective
    reshard_after_forward_policy: default
    use_deterministic_algorithms: false
```

Archon-specific constraints:

- Built-in model specs cover Qwen2/Qwen3/Qwen3 MoE families; other architectures require a model spec before use.
- `pp_schedule` choices include `1F1B`, `Interleaved1F1B`, `InterleavedZeroBubble`, and `ZBVZeroBubble`.
- `ac_mode=memory_budget` requires compile support.
- `reshard_after_forward_policy` controls FSDP memory/communication trade-off: `default`, `always`, or `never`.
- PP with `tie_word_embeddings=True` is unsupported; use PP=1 or a model without tied input/output embeddings.
- For PP, set enough microbatches (`actor.mb_spec.n_mbs`) for total stages to avoid warmup activation spikes.

## LoRA support matrix

| Training engine | Rollout backend | Support | Required notes |
|---|---|---|---|
| FSDP2 | vLLM | supported | Set `actor.use_lora=true`; keep `rollout.use_lora`/`lora_name` aligned. XCCL and disk update paths are available. |
| FSDP2 | SGLang | supported | Use disk weight updates for LoRA because SGLang distributed XCCL LoRA update raises at runtime. |
| Megatron | vLLM | supported | Requires `actor.megatron.bridge_type=megatron-bridge`; target modules map from Megatron bridge names to HF/vLLM names. |
| Megatron | SGLang | not supported | Use vLLM for Megatron LoRA rollout or disable LoRA. |
| Archon | any | not supported | Use FSDP2/Megatron or full-parameter Archon training. |

Common LoRA fields:

```yaml
actor:
  use_lora: true
  lora_rank: 32
  lora_alpha: 16
  target_modules: [all-linear]
  peft_type: lora
rollout:
  use_lora: true
  lora_name: my-adapter
```

Set a bounded LoRA retention policy for long asynchronous runs so old adapter versions do not accumulate in inference memory. Keep enough versions for your off-policy window.

## FP8 planning

### Megatron FP8

Megatron uses `actor.megatron.fp8_config` (when not `None`) to configure TransformerEngine-style FP8 behavior. Runtime validates that FP8 training has matching FP8/quantized weights; otherwise it raises a configuration error. FP8 paths may fall back to registry conversion for weight sync.

### Archon blockwise FP8

Archon uses:

```yaml
actor:
  dtype: bfloat16
  archon:
    fp8_config:
      mode: blockwise
      include_experts: false
      exclude_modules: [output, router, score]
      use_triton: true
```

Rules:

- `actor.dtype` must be `bfloat16`.
- Blockwise FP8 uses 128x128-aligned local matrix dimensions after TP/ETP/PP sharding; adjust TP/ETP or exclude modules when validation complains.
- The default excluded module substrings (`output`, `router`, `score`) are precision-sensitive. In YAML, setting `exclude_modules` replaces the entire list; include every module you still want in BF16.
- Archon blockwise FP8 is hardware-sensitive; do not infer success from CPU import or from a non-FP8 CUDA smoke.

## Ray/Slurm and cluster placement checklist

Before accepting a plan:

1. Compute every separated role's `world_size`. Sum them unless the scheduler explicitly colocates roles.
2. If roles are colocated, document which roles share devices and why; verify their placement strategy, device visibility, memory budget, and whether unequal worlds are intentional.
3. Confirm `cluster.n_nodes * cluster.n_gpus_per_node` covers the effective demand.
4. Confirm a shared filesystem for disk weight updates, checkpoints, logs, and recovery when the job spans nodes.
5. Keep role-specific allocator or debug env vars in the role's scheduling spec; do not rely on package import side effects.
6. For Slurm colocation, verify local rank/device mapping. AWEX colocation paths derive SGLang base GPU IDs from node-local rank to avoid duplicate claims.
7. Reserve enough CPU, RAM, ports, shared memory, and container mounts for each worker/server role.
8. If using `disk` weight updates or recovery checkpoints, ensure all nodes can read/write `cluster.fileroot` with adequate quota and bandwidth.

## Acceptance checklist

A backend plan is ready to pass back to the experiment/service owner when it states:

- role backends and worlds;
- install variant and optional backend packages;
- cluster GPU demand and colocation assumptions;
- weight-update mode and shared-storage/NCCL/AWEX prerequisites;
- LoRA/FP8 constraints if enabled;
- which checks were actually run and which GPU/multi-node/service checks remain unverified.
