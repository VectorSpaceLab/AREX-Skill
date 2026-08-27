---
name: distributed-training-backends
description: "Select, configure, and diagnose Accelerate distributed training
  backends including DeepSpeed, FSDP/FSDP2, Megatron-LM, torch native
  parallelism, TPU/XLA, FP8, quantization, compilation, Local SGD, and DDP
  communication hooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distributed Training Backends

Use this sub-skill when an agent must choose or configure an Accelerate backend beyond a plain single-process training loop: DeepSpeed ZeRO, FSDP/FSDP2, Megatron-LM, torch native tensor/context/sequence parallelism, TPU/XLA, Gaudi/HPU, FP8 or low precision, bitsandbytes/torchao quantization, `torch.compile`, Local SGD, or DDP communication hooks.

## Routing

- For `accelerate config`, `accelerate launch`, config-file locations, or generic CLI flag syntax, use `../configuration-and-cli/` first, then return here for backend-specific keys and compatibility.
- For where to instantiate `Accelerator`, how to call `prepare`, `backward`, `accumulate`, or unwrap models in a training loop, use `../training-loop-integration/`.
- For `save_state`, `load_state`, FSDP weight merging, DeepSpeed checkpoint folders, or tracker artifacts, use `../checkpointing-and-tracking/`.
- For backend choice, plugin objects, optional dependencies, hardware constraints, or config-vs-plugin precedence, stay in this sub-skill.

## Fast Backend Triage

- Choose **DeepSpeed** for ZeRO optimizer/parameter partitioning, CPU/NVMe offload, DeepSpeed-specific optimizers/schedulers, or existing DeepSpeed JSON; see `references/deepspeed-fsdp.md`.
- Choose **FSDP/FSDP2** for PyTorch-native sharding, `transformer_based_wrap`, state-dict control, CPU-RAM-efficient Transformers loading, and FSDP2 composition with native parallelism; see `references/deepspeed-fsdp.md`.
- Choose **torch native parallelism** when using `parallelism_config` for data replication/sharding, tensor parallelism, context parallelism, or DeepSpeed sequence parallelism; see `references/parallelism-and-precision.md`.
- Choose **Megatron-LM** only when the training stack is Megatron-aware and needs tensor/pipeline/sequence parallelism plus Megatron dummy optimizer/scheduler integration.
- Choose **TPU/XLA** only when `torch_xla` and TPU runtime are available; CPU-only inspection can validate config shape, not TPU execution.
- Choose **FP8/quantization/compile/communication options** as add-ons after the distributed backend is selected; verify optional dependency and hardware support before promising speedups.

## Required References

- `references/deepspeed-fsdp.md` — DeepSpeed, FSDP/FSDP2 selection, launch/config implications, and plugin usage.
- `references/parallelism-and-precision.md` — torch native parallelism, Megatron-LM, TPU/XLA, Gaudi/HPU, FP8, low precision, quantization, compilation, Local SGD, and DDP hooks.
- `references/api-reference.md` — primary Accelerate plugin/config classes, common constructor fields, environment/config key mapping, and minimal snippets.
- `references/troubleshooting.md` — dependency, hardware, ZeRO/offload, FSDP wrapping, FP8 mismatch, multi-node, and precedence diagnostics.

## Bundled Helper

Use `scripts/validate_backend_config.py` to statically validate JSON or YAML snippets for backend key shape and common contradictions:

```bash
python sub-skills/distributed-training-backends/scripts/validate_backend_config.py path/to/config.yaml
python sub-skills/distributed-training-backends/scripts/validate_backend_config.py --format deepspeed deepspeed.json
python sub-skills/distributed-training-backends/scripts/validate_backend_config.py --check-imports config.yaml
```

The helper does not launch distributed jobs, import Accelerate, initialize process groups, or require GPUs/TPUs. It reports missing optional packages only as hints when `--check-imports` is passed.

## Safety Notes

- Label DeepSpeed, FSDP2, Megatron-LM, TPU/XLA, FP8, bitsandbytes, torchao, transformer-engine, ms-amp, and Gaudi as optional dependency or hardware paths.
- Do not promise that config parsing proves runtime correctness; distributed execution still depends on process count, network/rendezvous setup, device availability, backend package versions, and model compatibility.
- Prefer explicit plugin objects in Python when code must be reproducible, and prefer config files when users rely on `accelerate config`/`launch` workflows. If both are present, check precedence and mismatch rules in `references/troubleshooting.md`.
