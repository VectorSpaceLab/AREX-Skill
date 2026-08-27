# Distributed Training and Long-Context Safety

Use this reference before proposing `torchrun`, fairseq, DeepSpeed, FSDP, multi-node, long-context, or custom-kernel commands for the architecture-heavy UniLM projects.

## Preflight Checklist

Before launching or recommending a launch, confirm:

- Hardware: GPU count, GPU memory, CUDA driver/runtime, interconnect, and whether `bf16` is supported.
- Process layout: `--nproc_per_node` equals the intended number of worker processes per node; `--nnodes`, `--node_rank`, `--master_addr`, and `--master_port` are consistent across nodes.
- Data: training/eval data exists, is readable by every node, and matches expected JSON/JSONL or fairseq-binarized formats.
- Checkpoints: model directory, checkpoint file, tokenizer files, and resume/output directories are separate and writable as needed.
- Dependencies: Apex, Flash-Attention, Deepspeed, fairseq fork, vLLM, or custom kernels are installed only in an isolated environment appropriate for that project.
- Scale: context length, batch size, update frequency, ZeRO stage, tensor/model parallel size, and gradient accumulation are realistic for the hardware.

## `torchrun` Variables

Single-node patterns normally need:

```bash
torchrun --nproc_per_node GPUS --master_port PORT SCRIPT.py ...
```

Multi-node patterns normally need:

```bash
torchrun --nnodes NNODES --nproc_per_node GPUS_PER_NODE \
  --node_rank NODE_RANK --master_addr MASTER_ADDR --master_port MASTER_PORT \
  SCRIPT.py ...
```

Common failure signals:

- Hang at initialization: wrong `MASTER_ADDR`, blocked `MASTER_PORT`, mismatched `NNODES`, or a missing node.
- Immediate rank errors: different commands/configs across nodes, inconsistent environment variables, or launch from the wrong working directory.
- NCCL timeout: network/firewall, bad GPU visibility, unsupported topology, or a previous dead rank.
- CUDA out of memory: context length, batch size, model size, KV cache, activation checkpointing, or ZeRO/FSDP settings exceed capacity.

## YOCO Launch Safety

YOCO examples use fairseq `train.py` and `validate.py` entry points. The native scripts assume a particular fairseq-adjacent working directory and heavyweight dependencies. In a self-contained skill, only emit templates and require the user to adapt the script location to their prepared YOCO environment.

Important YOCO controls:

- `--tokens-per-sample`: drives context length and memory use; `1048576` is benchmark-scale.
- `--interval`: for needle evaluation, usually equal to the max context length.
- `--criterion needle_haystack` or `--criterion multi_needle --needle-num N`: selects single or multi-needle retrieval.
- `--load-ckpt` and `--yoco-model`: both are required for evaluation.
- `--batch-size`: long-context needle examples use `1`; increasing it is unsafe without memory profiling.
- `--bf16`: recommended by source examples, but only safe on compatible GPUs.

Never hide benchmark-scale cost. A 1M-token needle evaluation may require large memory, custom attention kernels, and long wall time even with batch size `1`.

## DeepSpeed and PFPO Safety

PFPO training examples combine Hydra config directories with DeepSpeed. A safe plan must name:

- Hydra config path and config name (`-cp` and `-cn`).
- Output directory and checkpoint/resume policy.
- Training data or preference-pair file.
- DeepSpeed YAML, ZeRO stage, offload settings, and tensor/model parallel settings if used.
- `wandb` behavior; disable or configure it deliberately to avoid unexpected service calls.

DeepSpeed warning patterns:

- ZeRO-3 checkpoints are sharded; do not expect a single model file unless conversion is documented.
- Optimizer offload shifts memory pressure to CPU/RAM and storage bandwidth.
- Tensor parallel and FairScale settings must match the config and process count.
- Resume logic may scan `output_dir` for latest checkpoints; keep output dirs clean when doing dry runs.

## fairseq Fork Safety

YOCO, GAD, and IAD use fairseq-style or vendored fairseq code. Treat the fork as part of a prepared project runtime, not as something this skill can import. Common issues include:

- Entrypoints expect to be run from a directory where project modules are importable.
- `--user-dir` plugins must be discoverable.
- Checkpoint arguments from one fork may not load in another fork.
- Old fairseq forks may require older Python, PyTorch, CUDA, or compiler versions.

When a command includes `fairseq`, `validate.py`, `train.py`, or `--user-dir`, state the assumed working directory and module path explicitly.

## Flash Attention, Apex, and Custom Kernels

Architecture projects here often mention Flash-Attention, Apex, custom flash-diff kernels, TileLang, or sparse decoding kernels. Use these rules:

- Do not claim a kernel is available from a README alone; confirm installation and CUDA compatibility.
- Match Flash-Attention versions to PyTorch/CUDA/GPU architecture.
- Apex is optional but source YOCO notes it as separately installed; failed imports should route to environment preparation, not code changes.
- ReSA sparse decoding and long-context prefill can fail at runtime even if imports pass, because kernel limits depend on sequence length, dtype, and GPU.

## Memory Planning Heuristics

Reduce risk by changing one scale lever at a time:

- Lower `--tokens-per-sample`, `--limit`, generation length, or sequence length first.
- Keep `--batch-size 1` for long-context needle and ReSA smoke tests.
- Use `--nproc_per_node 1` for command validation before distributed runs.
- Prefer shorter synthetic JSONL samples for data-format validation.
- Increase `gradient_accumulation` or `--update-freq` instead of per-GPU batch size when training memory is tight.
- For DeepSpeed, choose ZeRO/offload settings deliberately rather than copying an 8xA100 or 2x8xV100 command to smaller hardware.

## Safe Launch Review Template

When responding to a user command, report:

1. Mode and expected entry point.
2. Required files/directories and whether the user supplied each one.
3. Process layout and any `nproc/world_size` mismatch.
4. Kernel/dependency assumptions.
5. Memory or benchmark-scale risk.
6. A dry-run helper invocation using `../scripts/check_training_plan.py`.
7. A launch template with placeholders, not machine-local paths.
