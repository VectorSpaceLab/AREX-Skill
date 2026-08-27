# Distributed And Multi-Node Training

Use this reference when planning torchrun, FSDP, SLURM, or multi-node torchtune training. It is about command construction and launch safety, not cluster administration.

## Core Placement Rule

`tune run` embeds torchrun arguments in its parser. Torchrun flags must come before the recipe name; recipe config and overrides come after the recipe name and `--config`.

Correct:

```bash
tune run --nnodes 1 --nproc_per_node 4 lora_finetune_distributed --config llama3_2/3B_lora output_dir='<output-dir>'
```

Incorrect:

```bash
tune run lora_finetune_distributed --config llama3_2/3B_lora --nproc_per_node 4
```

The second form treats `--nproc_per_node` like a recipe/config argument, not a torchrun launcher argument.

## Recipe Distributed Support

`tune run` checks the recipe registry. If any torchrun options are present for a registry recipe whose `supports_distributed` is false, it errors and tells the user to run without torchrun commands.

| Use distributed flags with | Do not use distributed flags with |
| --- | --- |
| `full_finetune_distributed` | `full_finetune_single_device` |
| `lora_finetune_distributed` | `lora_finetune_single_device` |
| `lora_dpo_distributed` | `lora_dpo_single_device` |
| `full_dpo_distributed` | `ppo_full_finetune_single_device` |
| `knowledge_distillation_distributed` | `knowledge_distillation_single_device` |
| `qat_distributed`, `qat_lora_finetune_distributed` | `qat_single_device` |
| `dev/grpo_full_finetune_distributed`, `dev/early_exit_finetune_distributed` | `dev/async_grpo_full_finetune_distributed` |

If a user wants multi-GPU but selected a single-device recipe, switch to the distributed counterpart when one exists and choose a matching distributed config.

## Single-Node Multi-GPU Pattern

Use this for one host with multiple devices:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  full_finetune_distributed llama3_1/8B_full \
  --nproc-per-node 4 \
  --override checkpointer.checkpoint_dir='<checkpoint-dir>' \
  --override output_dir='<output-dir>'
```

The printed command should look like:

```bash
tune run --nproc_per_node 4 full_finetune_distributed --config llama3_1/8B_full checkpointer.checkpoint_dir='<checkpoint-dir>' output_dir='<output-dir>'
```

When `--rdzv_endpoint` is omitted, `tune run` sets torchrun standalone mode for distributed execution.

## Multi-Node Torchrun Pattern

For multiple hosts, decide:

- `--nnodes`: number of participating nodes.
- `--nproc_per_node`: number of worker processes per node, usually one per GPU.
- `--rdzv_id`: stable job id shared by all nodes for this launch.
- `--rdzv_backend`: usually `c10d`.
- `--rdzv_endpoint`: host:port for the rendezvous endpoint, usually head node address.
- Shared filesystem or equivalent checkpoint/data availability for all nodes.

Safe dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_finetune_distributed llama3_3/70B_lora \
  --nnodes 2 \
  --nproc-per-node 8 \
  --rdzv-id 101 \
  --rdzv-backend c10d \
  --rdzv-endpoint '<head-node-ip>:29500' \
  --override checkpointer.checkpoint_dir='<shared-checkpoint-dir>' \
  --override output_dir='<shared-output-dir>'
```

The builder normalizes common underscore/dash spelling for torchrun options and prints the command only.

## SLURM / sbatch Template Guidance

The repo includes a reference SLURM template for full finetuning. Treat SLURM files as cluster-specific templates; do not copy source paths or local environment names into public instructions.

A cluster launch usually needs:

```bash
#SBATCH --nodes=<node-count>
#SBATCH --ntasks=<node-count>
#SBATCH --gpus-per-task=<gpus-per-node>
#SBATCH --cpus-per-task=<cpus-per-task>

nodes=( $( scontrol show hostnames $SLURM_JOB_NODELIST ) )
head_node=${nodes[0]}
head_node_ip=$(srun --nodes=1 --ntasks=1 -w "$head_node" hostname --ip-address)

export TORCH_DIST_INIT_BARRIER=1
export LOGLEVEL=INFO
# Optional for some clusters:
# export NCCL_SOCKET_IFNAME=<interface>
# export GLOO_SOCKET_IFNAME=<interface>

srun tune run --nnodes <node-count> --nproc_per_node <gpus-per-node> \
  --rdzv_id <job-id> --rdzv_backend c10d --rdzv_endpoint "$head_node_ip:29500" \
  full_finetune_distributed --config llama3_3/70B_full_multinode \
  checkpointer.checkpoint_dir='<shared-checkpoint-dir>' output_dir='<shared-output-dir>'
```

Use the exact cluster's module/venv activation, partition, filesystem, and networking values. Ask before submitting `sbatch`; this starts an expensive job.

## Multi-Node LoRA Case

For a difficult LoRA multi-node plan, assert all of these:

- Uses `lora_finetune_distributed`, not `lora_finetune_single_device`.
- Uses a distributed config such as a `*_lora` config, not only a `*_lora_single_device` config.
- Places `--nnodes`, `--nproc_per_node`, and rendezvous flags before the recipe name.
- Places `checkpointer.*`, `output_dir`, LoRA rank/alpha, and dataset overrides after `--config`.
- Uses shared checkpoint/data/output paths visible on all nodes.
- Avoids running until the user confirms cluster allocation, credentials, and shared storage.

Example dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_finetune_distributed llama3_2/3B_lora \
  --nnodes 2 --nproc-per-node 8 \
  --rdzv-id 402 --rdzv-backend c10d --rdzv-endpoint '<head-node>:29500' \
  --override model.lora_rank=32 \
  --override model.lora_alpha=64 \
  --override checkpointer.checkpoint_dir='<shared-model-dir>' \
  --override output_dir='<shared-output-dir>'
```

## Distributed Preflight Checklist

Before approving a real launch:

- Recipe supports distributed according to registry selection.
- GPU count equals intended world size: `nnodes * nproc_per_node`.
- Batch semantics are understood: effective batch often scales with device count, `batch_size`, and `gradient_accumulation_steps`.
- All nodes can read checkpoint and dataset paths and write to output/checkpoint paths.
- Tokenizer/checkpoint paths are identical from every worker's perspective.
- Rendezvous endpoint is reachable and port is free.
- `NCCL_SOCKET_IFNAME` / `GLOO_SOCKET_IFNAME` are set when cluster networking requires them.
- Optional loggers are configured to avoid every worker creating conflicting remote runs unless intended.
- Resume paths include recipe state and checkpoint shards from a compatible previous run.

## Failure Signals

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Recipe ... does not support distributed training` | Torchrun flags were used with a non-distributed recipe | Switch recipe/config or remove torchrun flags. |
| Torchrun flags ignored | Flags were placed after recipe/config | Move flags before recipe. |
| Rendezvous timeout | Wrong endpoint, blocked port, mismatched `nnodes`, or cluster network issue | Re-check head node IP, port, node count, and network interface. |
| Workers cannot find checkpoints | Paths are local to one node | Use shared filesystem or per-node staging with identical paths. |
| OOM on distributed run | Per-device batch too high or model/config too large | Reduce `batch_size`, increase accumulation, enable checkpointing/offload, or choose LoRA/QLoRA. |
