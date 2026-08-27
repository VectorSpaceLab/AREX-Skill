---
name: parallel-and-optimization
description: "Plans HunyuanVideo multi-GPU xDiT inference, FP8 command
  construction, memory trade-offs, and optional CUDA dependency
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo Parallel and Optimization

Use this sub-skill when the user mentions multi-GPU generation, xDiT, `torchrun`, `--ulysses-degree`, `--ring-degree`, FP8 weights, flash-attn, `xfuser`, memory pressure, or CUDA backend errors.

## Read first

- `references/parallel-and-fp8.md` for xDiT and FP8 command patterns.
- `references/memory-and-backends.md` for GPU memory and dependency planning.
- `references/troubleshooting.md` for xDiT, FP8, and flash-attn failures.
- `scripts/build_optimized_command.py` to build safe multi-GPU or FP8 commands without launching generation.

## Command-builder examples

Multi-GPU xDiT command:

```bash
python sub-skills/parallel-and-optimization/scripts/build_optimized_command.py multi-gpu \
  --prompt "A cat walks on the grass, realistic style." \
  --height 720 --width 1280 --nproc-per-node 4 --ulysses-degree 2 --ring-degree 2
```

FP8 command:

```bash
python sub-skills/parallel-and-optimization/scripts/build_optimized_command.py fp8 \
  --prompt "A cat walks on the grass, realistic style." \
  --dit-weight ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8.pt
```

The helper validates degree products and FP8 map paths. It prints commands only; actual generation remains a GPU/model job.

## Non-negotiable backend facts

- xDiT requires CUDA, NCCL, `xfuser`, and a valid `torchrun` world size.
- Distributed mode asserts `--use-cpu-offload` is false.
- `--nproc_per_node` must equal `--ulysses-degree * --ring-degree`.
- FP8 requires both the FP8 `.pt` weight and the derived `_map.pt` scale file.
- CPU imports do not verify xDiT or FP8 generation.
