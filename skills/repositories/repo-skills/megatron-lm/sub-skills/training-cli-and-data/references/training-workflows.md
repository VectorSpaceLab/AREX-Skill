# Training workflows

## First-run pattern

Before using a large recipe, verify the environment and launch plumbing with mock data and a tiny model/iteration count. A first-run command should answer:

- Does the selected Python import Megatron Core and Torch CUDA?
- Do ranks initialize NCCL and Megatron process groups?
- Do the requested TP/PP/CP/EP sizes multiply into the world size?
- Can the run write logs/checkpoints to the selected filesystem?

Use the bundled `render_pretrain_command.py` to create a conservative template, then adapt model dimensions and data/checkpoint paths.

## Pretrain entrypoint families

| Entrypoint family | Use when | Key inputs |
|---|---|---|
| GPT pretraining/SFT | Decoder-only language models, GPT/LLaMA/Mixtral-like flows. | Model size, tokenizer, data prefix or mock data, TP/PP/CP/EP, checkpoint paths. |
| Hybrid | Hybrid attention/MLP/Mamba/GDN/DSA layer-pattern models. | `--hybrid-layer-pattern`, model dimensions, checkpoint compatibility. |
| Mamba | State-space model flows. | Mamba optional dependencies and model-specific args. |
| VLM/multimodal | Text+vision/audio/video training. | Media manifests, encoder/LLM topology, multimodal configs. |
| RL/GRPO | Post-training RL. | Route to post-training/rl sub-skill for rewards, rollouts, and packed data. |

## Distributed launch template

Single node:

```bash
python -m torch.distributed.run \
  --nproc-per-node <GPUS_PER_NODE> \
  pretrain_gpt.py \
  --tensor-model-parallel-size <TP> \
  --pipeline-model-parallel-size <PP> \
  --num-layers <LAYERS> \
  --hidden-size <HIDDEN> \
  --num-attention-heads <HEADS> \
  --seq-length <SEQ> \
  --micro-batch-size <MBS> \
  --global-batch-size <GBS> \
  --train-iters <ITERS> \
  --bf16 \
  --mock-data
```

Multi-node adds `--nnodes`, `--node-rank`, `--master-addr`, and `--master-port`. In SLURM, launch one task per node and run `python -m torch.distributed.run` inside each task with `SLURM_NODEID` as node rank.

## SLURM essentials

- Submit from a worktree path visible to every node.
- Set `MASTER_ADDR` from the first host in `SLURM_JOB_NODELIST`.
- Set `WORLD_SIZE = NNODES × GPUS_PER_NODE` and make it consistent with Megatron parallel sizes.
- Write checkpoints, TensorBoard data, and logs to shared storage.
- Scan all rank logs; the first non-NCCL Python traceback is usually the root cause.

## Precision and backend checks

| Precision/path | Requirement |
|---|---|
| BF16 | Common default on modern NVIDIA GPUs. |
| FP16 | Older-compatible mixed precision; watch loss scaling. |
| FP8/FP4 | Requires supported GPU generation and TransformerEngine/NVIDIA kernels; do not validate on A100 as if it were H100/Blackwell. |
| Megatron-FSDP | See core parallelism; do not set `CUDA_DEVICE_MAX_CONNECTIONS=1`. |

## Validation signals

A successful short run should show:

- Ranks initialize without immediate NCCL errors.
- Iteration/loss logging appears on rank 0.
- Checkpoint save/load paths are writable when enabled.
- No shape/divisibility assertions from model or parallel setup.
- Data loader starts without long cache-building stalls unless expected.

## Model-family recipe adaptation

When adapting a recipe from Megatron-LM examples, do not blindly preserve every flag. Extract:

1. Model architecture dimensions and tokenizer assumptions.
2. Parallelism/precision settings and hardware assumptions.
3. Data mode (`--mock-data`, data prefix, object storage, SFT/FIM/multimodal).
4. Checkpoint save/load format and intervals.
5. Optional dependency requirements (TransformerEngine, ModelOpt, Mamba, multimodal codecs).
6. Validation objective for the user's run: smoke, throughput, convergence, or CI parity.
