# Parallelism reference

## Core formula

For dense language-model training:

```text
total GPUs = tensor parallel (TP) × pipeline parallel (PP) × context parallel (CP) × data parallel (DP)
```

For MoE, expert parallelism (EP) constrains the expert/data layout. EP does not remove the need for the total world size to be compatible with TP/PP/CP/DP and with the number of experts.

## Strategy roles

| Strategy | What it splits | Use when |
|---|---|---|
| DP | batch dimension | More data throughput; default replication/sharding axis. |
| TP | tensors inside layers | Hidden/attention/MLP dimensions are too large for one GPU. |
| PP | layer depth | Model depth does not fit or needs stage-level parallelism. |
| CP | sequence dimension | Long context, usually 8K+ tokens, where activations dominate. |
| EP | MoE experts | Mixture-of-Experts models with many experts. |
| Megatron-FSDP | parameters, gradients, optimizer states | Model state memory reduction and data-parallel sharding. |

## Decision checklist

1. Start from available GPUs and model family.
2. Choose TP so attention heads and hidden dimensions divide cleanly.
3. Choose PP so layers and special embedding/loss/MTP/hybrid positions are balanced.
4. Add CP for long sequence lengths when activation memory or CP-supported model code warrants it.
5. Add EP for MoE; verify `num_experts`, expert top-k, and ETP/EP constraints.
6. Compute DP from remaining world size.
7. Decide whether Megatron-FSDP should shard optimizer states, gradients, and/or parameters.
8. Re-check batch sizes: global batch must be compatible with micro-batch, DP, and gradient accumulation.

## Common flags by area

### Tensor/context/pipeline

```bash
--tensor-model-parallel-size <TP>
--pipeline-model-parallel-size <PP>
--context-parallel-size <CP>
--sequence-parallel
```

Sequence parallel is especially important with TP and required for some TP+EP combinations.

### MoE

```bash
--num-experts <N>
--expert-model-parallel-size <EP>
--moe-router-topk <K>
--moe-grouped-gemm
--moe-token-dispatcher-type alltoall
```

When combining TP and EP, check head, expert, and data-parallel divisibility together. Router and dispatcher flags can require optional kernels or communication backends.

### Megatron-FSDP

```bash
--use-megatron-fsdp
--data-parallel-sharding-strategy optim_grads_params
--ckpt-format fsdp_dtensor
--init-model-with-meta-device
```

Useful additions include per-token loss, BF16 gradient communication, NCCL user buffers, and double buffering when the hardware/network supports them. These options are performance-sensitive; verify against the target cluster.

## `CUDA_DEVICE_MAX_CONNECTIONS`

Do not set this environment variable blindly.

| Configuration | Rule |
|---|---|
| Pre-Blackwell Hopper/Ampere with TP>1 or CP>1, non-FSDP | Set `CUDA_DEVICE_MAX_CONNECTIONS=1` when the code path requires it. |
| Blackwell/GB200 | Usually not required. |
| Torch-FSDP2 or Megatron-FSDP | Do **not** set it to `1`; leave unset or set greater than `1`. |
| `overlap_moe_expert_parallel_comm` | Use `32`. |

If a user reports an assertion mentioning this variable, inspect the training command and hardware before recommending a value.

## Example reasoning patterns

### 64-GPU dense long-context model

A plausible route is TP=4, PP=4, CP=2, DP=2. Validate:

- 64 = 4 × 4 × 2 × 2.
- Attention heads divide by 4.
- Layer count can be split across 4 pipeline stages.
- Global batch is compatible with DP=2 and micro-batch size.

### MoE model with 64 experts

Start from expert layout:

- EP should divide or otherwise be compatible with expert count and data parallelism.
- If TP is also used, enable sequence parallel when required.
- MoE grouped GEMM/flex/DeepEP flags may need optional kernels; if unavailable, choose a supported dispatcher or document the block.

## Validation before launch

- Print or log resolved TP/PP/CP/EP/DP sizes.
- Confirm `WORLD_SIZE` equals the planned product.
- Confirm divisibility of `num_attention_heads`, hidden size, number of layers, and experts.
- Confirm checkpoint format matches the sharding/FSDP plan.
- Confirm the environment backend actually supports the requested precision/kernels.
