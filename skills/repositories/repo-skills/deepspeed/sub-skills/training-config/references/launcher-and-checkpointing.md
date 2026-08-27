# Launcher and Checkpointing

## Launcher Basics

DeepSpeed installs a `deepspeed` launcher entry point. Treat every launcher command in this reference as a non-executed template until the user explicitly approves a real run. Before running `deepspeed`, verify the hostfile or local resources, include/exclude filters, node ranks, master address/port, log locations, expected working directory, and cleanup plan.

A standard training command appends the user script and user arguments after DeepSpeed launcher options:

```bash
deepspeed --hostfile hosts.txt train.py --deepspeed --deepspeed_config ds_config.json
```

Hostfile lines use OpenMPI/Horovod-style syntax:

```text
worker-1 slots=4
worker-2 slots=4
```

If no hostfile is supplied or found, DeepSpeed falls back to local resources. If the accelerator count is zero or unavailable, resource discovery can fail or produce local-only behavior; validate hardware before promising a multi-GPU run.

## Include and Exclude Filters

Filter syntax is `NODE[:SLOT[,SLOT...]][@NODE[:SLOT...]]`.

Examples:

```bash
# Only slots 0 and 1 on worker-2
deepspeed --include "worker-2:0,1" train.py --deepspeed --deepspeed_config ds_config.json

# Everything except selected slots
deepspeed --exclude "worker-2:0@worker-3:0,1" train.py --deepspeed --deepspeed_config ds_config.json
```

Rules:

- `--include` and `--exclude` are mutually exclusive.
- `--num_nodes`/`--num_gpus` are mutually exclusive with `--include`/`--exclude`.
- A host without `:slots` means all slots for include, or the whole host for exclude.
- Duplicate included slots are de-duplicated.
- Unknown hosts, unknown slots, malformed entries, duplicate hostfile entries, and empty hostfiles are invalid.

Preview a filter safely:

```bash
python scripts/launcher_resource_preview.py \
  --hostfile hosts.txt \
  --include "worker-0:0,1@worker-1"
```

## Launching Without Passwordless SSH

`--no_ssh` mode runs the launcher separately on each node. The examples below are templates only; do not execute them until the user confirms hostnames, rank-to-node mapping, reachable master address/port, log locations, and that starting one launcher per node is intended. Provide a consistent `--master_addr`, `--master_port`, `--node_rank`, and total node count on every node. Do not combine conflicting include/exclude filters.

Example pattern:

```bash
# Run on node 0
deepspeed --no_ssh --node_rank 0 --master_addr worker-0 --master_port 29500 \
  --hostfile hosts.txt train.py --deepspeed --deepspeed_config ds_config.json

# Run on node 1
deepspeed --no_ssh --node_rank 1 --master_addr worker-0 --master_port 29500 \
  --hostfile hosts.txt train.py --deepspeed --deepspeed_config ds_config.json
```

For cloud schedulers, ensure each node sees the same hostfile ordering and config. If using `--no_ssh`, an include/exclude conflict is still a config error, not a launch-time workaround.

## Checkpoint Save and Load

DeepSpeed checkpoint APIs hide optimizer, scheduler, and model-state details, but they are distributed operations:

```python
client_state = {"step": global_step}
engine.save_checkpoint(save_dir, tag=f"global_step{global_step}", client_state=client_state)

load_path, client_state = engine.load_checkpoint(load_dir, tag=resume_tag)
```

Guardrails:

- All ranks must call `save_checkpoint`; rank-0-only save can hang.
- Keep `tag` consistent across ranks. Use config checkpoint tag validation when restoring across different layouts.
- Store application-specific resume metadata in `client_state` and restore dataloaders/samplers consistently.
- Do not immediately call `load_checkpoint` on the same ZeRO-3-partitioned engine instance that just saved unless the training flow is known to support it; reinitialize or use the documented conversion/export path when producing a consolidated artifact.

## Exporting ZeRO Checkpoints

For a 16-bit model export during training:

```json
{
  "zero_optimization": {
    "stage": 3,
    "stage3_gather_16bit_weights_on_model_save": true
  }
}
```

Then call:

```python
engine.save_16bit_model(output_dir, output_file="pytorch_model.bin")
```

If `stage3_gather_16bit_weights_on_model_save` is false under ZeRO-3, a normal module `state_dict` does not contain full partitioned weights, so no consolidated weights should be expected from `save_16bit_model()`.

For FP32 consolidation, use the `zero_to_fp32.py` script generated in a saved ZeRO checkpoint directory or DeepSpeed's `deepspeed.utils.zero_to_fp32` utilities. Plan host RAM carefully because consolidation can require about twice the final checkpoint size in CPU memory.
