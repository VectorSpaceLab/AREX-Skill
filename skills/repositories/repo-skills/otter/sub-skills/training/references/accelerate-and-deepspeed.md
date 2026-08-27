# Accelerate and DeepSpeed launch guidance

Otter training is launched in a target Otter checkout with `accelerate launch` and config names under `pipeline/accelerate_configs/`. This reference preserves the config choices and command shapes so future agents do not need to reopen source docs. Override process count, machines, rank, and port at launch time instead of editing configs for every run.

## Available config names

| Config | Distributed type | Mixed precision | Default processes | ZeRO/offload behavior | Use when |
|---|---|---|---:|---|---|
| `accelerate_config_ddp.yaml` | `MULTI_GPU` | `bf16` | `2` | No DeepSpeed | Small debugging or DDP-only multi-GPU jobs. |
| `accelerate_config_fsdp.yaml` | `no` | `bf16` with downcast | `1` | No FSDP despite the filename | Treat as a single-process/local template unless you inspect and revise it. |
| `accelerate_config_zero1.yaml` | `DEEPSPEED` | `bf16` | `8` | ZeRO-1, no offload | Lower overhead when memory allows. |
| `accelerate_config_zero2.yaml` | `DEEPSPEED` | `bf16` | `8` | ZeRO-2, no offload, config gradient accumulation `4` | Documented OtterHD/Fuyu finetuning default. |
| `accelerate_config_zero2_slurm.yaml` | `DEEPSPEED` | `bf16` | `8` | ZeRO-2 with CPU optimizer and parameter offload | Memory-pressure or SLURM-style jobs that accept slower CPU offload. |
| `accelerate_config_zero3.yaml` | `DEEPSPEED` | `bf16` | `8` | ZeRO-3, no offload, `zero3_init_flag`, gather 16-bit on save | Documented Otter SFT default for large Otter weights. |
| `accelerate_config_zero3_offload.yaml` | `DEEPSPEED` | `bf16` | `8` | ZeRO-3 with CPU optimizer and parameter offload | Severe GPU memory pressure; expect slower training and more host RAM/IO. |
| `accelerate_config_zero3_slurm.yaml` | `DEEPSPEED` | `bf16` | `16` over `2` machines | ZeRO-3 multinode standard launcher | Multi-node launch template. |
| `ds_zero3_config.json` | DeepSpeed JSON | auto fp16/bf16 | auto | ZeRO-3 with auto batch sizes and gather-on-save | Use only when a workflow expects a raw DeepSpeed JSON config rather than an Accelerate YAML. |

## Command skeleton

Single-node:

```bash
export PYTHONPATH=.
accelerate launch \
  --config_file pipeline/accelerate_configs/accelerate_config_zero3.yaml \
  --num_processes=8 \
  pipeline/train/instruction_following.py \
  --pretrained_model_name_or_path=<model-or-local-path> \
  --training_data_yaml=<training-yaml> \
  --model_name=otter \
  --instruction_format=simple \
  --batch_size=8 \
  --gradient_accumulation_steps=1 \
  --external_save_dir=checkpoints \
  --run_name=<run-name>
```

Multi-node pattern:

```bash
export PYTHONPATH=.
accelerate launch \
  --config_file pipeline/accelerate_configs/accelerate_config_zero2.yaml \
  --machine_rank=${MACHINE_RANK} \
  --main_process_ip=${MASTER_ADDR} \
  --main_process_port=${MASTER_PORT} \
  --num_machines=${NUM_MACHINES} \
  --num_processes=${TOTAL_PROCESSES} \
  pipeline/train/instruction_following.py \
  <training-script-flags>
```

The scheduler-specific way to populate `MACHINE_RANK`, `MASTER_ADDR`, `MASTER_PORT`, `NUM_MACHINES`, and `TOTAL_PROCESSES` is environment-dependent. Keep those values explicit in the job script.

## Batch-size and accumulation alignment

There are two places where gradient accumulation appears:

1. Accelerate/DeepSpeed YAML, for the launcher/plugin.
2. Training script CLI, for `Accelerator(gradient_accumulation_steps=...)` and dataloader/step accounting.

Keep them intentionally aligned. `instruction_following.py` also writes `train_micro_batch_size_per_gpu` into the DeepSpeed plugin from `--batch_size`; `pretraining_cc3m.py` does the same from `--batch_size_cc3m`.

Effective samples per optimizer step are approximately:

```text
per_process_batch * num_processes * gradient_accumulation_steps
```

For SFT, `per_process_batch` is `--batch_size`. For dual-stream pretraining, reason separately about `--batch_size_mmc4` and `--batch_size_laion`. For CC3M pretraining, use `--batch_size_cc3m`.

## Config selection heuristics

- Start from `accelerate_config_zero3.yaml` for large Otter 9B-style SFT when GPU memory is tight.
- Start from `accelerate_config_zero2.yaml` for OtterHD/Fuyu finetuning because that is the documented Fuyu example.
- Use offload configs only after reducing batch size, sequence length, workers, or enabling checkpointing is insufficient; CPU offload can be much slower.
- Use DDP only for smaller models or debug runs that fit without ZeRO partitioning.
- Treat `accelerate_config_fsdp.yaml` cautiously: its contents specify `distributed_type: no`, so it is not a ready FSDP template as named.
- Override `--main_process_port` when running multiple jobs on the same host or when a previous job left a port occupied.

## Resource constraints

- Real training is a CUDA/multi-GPU workflow in practice; CPU is useful for parser/config checks only.
- Configs use `bf16`; confirm that GPUs and installed PyTorch support bf16 or revise the precision strategy.
- `--max_seq_len`, Fuyu dynamic resolution, and image resolution strongly affect memory.
- DeepSpeed ZeRO-3 save/gather behavior can make checkpoint saving slow and disk-heavy.
- W&B logging and model downloads require network unless `--offline` and local caches are prepared.
