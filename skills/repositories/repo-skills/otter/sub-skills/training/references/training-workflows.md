# Otter training workflows

This reference summarizes the training paths exposed by Otter's training scripts and demo launches. It is self-contained operational guidance; it does not require reopening repository docs. Entry point names such as `pipeline/train/instruction_following.py` are target-checkout commands for a user-controlled Otter checkout or equivalent deployment package; use the bundled command builder to construct them and do not launch training until the user explicitly authorizes a run.

## Choose the right workflow

| Goal | Entry point | Core data input | Model/instruction settings | Typical config |
|---|---|---|---|---|
| Instruction tuning / SFT | `pipeline/train/instruction_following.py` | `--training_data_yaml` | `--model_name=otter`, `--instruction_format=simple` for Otter-MPT; other choices below | `pipeline/accelerate_configs/accelerate_config_zero3.yaml` |
| OtterHD / Fuyu finetuning | `pipeline/train/instruction_following.py` | `--training_data_yaml` | `--model_name=fuyu`, `--instruction_format=fuyu`, often `--dynamic_resolution` | `pipeline/accelerate_configs/accelerate_config_zero2.yaml` |
| MMC4 + LAION pretraining | `pipeline/train/pretraining.py` | `--mmc4_shards`, `--laion_shards` | Otter/Flamingo initialization from `--pretrained_model_name_or_path` | ZeRO-2 or ZeRO-3 depending memory |
| CC3M pretraining | `pipeline/train/pretraining_cc3m.py` | `--cc3m_shards` | Otter/Flamingo initialization from `--pretrained_model_name_or_path` | ZeRO-2 or ZeRO-3 depending memory |

Use [pretraining](pretraining.md) for the pretraining-specific flags. Use [accelerate-and-deepspeed](accelerate-and-deepspeed.md) for launch config selection.

## SFT / instruction tuning command shape

The documented Otter SFT launch trains from converted OpenFlamingo-derived Otter weights, adds/uses the `<answer>` token for instruction tuning, and consumes a MIMIC-IT data YAML. A safe single-node command shape is:

```bash
export PYTHONPATH=.
RUN_NAME="Otter_MPT7B"
GPU=8
WORKERS=$((GPU * 2))

accelerate launch --config_file pipeline/accelerate_configs/accelerate_config_zero3.yaml \
  --num_processes=${GPU} \
  pipeline/train/instruction_following.py \
  --pretrained_model_name_or_path=luodian/OTTER-MPT7B-Init \
  --model_name=otter \
  --instruction_format=simple \
  --training_data_yaml=shared_scripts/Demo_Data.yaml \
  --batch_size=8 \
  --num_epochs=3 \
  --external_save_dir=checkpoints \
  --run_name=${RUN_NAME} \
  --workers=${WORKERS} \
  --lr_scheduler=cosine \
  --learning_rate=2e-5 \
  --warmup_steps_ratio=0.01 \
  --save_hf_model \
  --max_seq_len=1024
```

Add W&B flags only when logging is desired:

```bash
--report_to_wandb --wandb_entity=<entity> --wandb_project=<project>
```

For a generated command with validation and no launch, use:

```bash
python ../scripts/build_training_command.py \
  --mode sft \
  --pretrained-model luodian/OTTER-MPT7B-Init \
  --training-data-yaml shared_scripts/Demo_Data.yaml \
  --run-name Otter_MPT7B \
  --num-processes 8 \
  --batch-size 8 \
  --num-epochs 3 \
  --save-hf-model
```

## OtterHD / Fuyu finetuning

OtterHD is finetuned from Fuyu-8B and uses the same instruction-following entry point with Fuyu-specific model and instruction formats. The documented command shape is:

```bash
export PYTHONPATH=.

accelerate launch --config_file pipeline/accelerate_configs/accelerate_config_zero2.yaml \
  --num_processes=8 \
  --main_process_port=25000 \
  pipeline/train/instruction_following.py \
  --pretrained_model_name_or_path=adept/fuyu-8b \
  --training_data_yaml=shared_scripts/Demo_Data.yaml \
  --model_name=fuyu \
  --instruction_format=fuyu \
  --batch_size=8 \
  --gradient_accumulation_steps=2 \
  --num_epochs=3 \
  --external_save_dir=checkpoints \
  --save_hf_model \
  --run_name=OtterHD_Tester \
  --workers=1 \
  --lr_scheduler=linear \
  --learning_rate=1e-5 \
  --warmup_steps_ratio=0.01 \
  --dynamic_resolution \
  --weight_decay=0.1
```

Important Fuyu/OtterHD warning: the documented throughput relies on Flash-Attention 2 plus fused layernorm, fused square ReLU, fused rotary positional embedding, and related fused operators. These are CUDA/PyTorch-version-sensitive build dependencies. If they are absent or ABI-incompatible, Fuyu training may fail at import time or run much slower. Confirm GPU, CUDA, PyTorch, and fused-op compatibility before scheduling a multi-GPU job.

## `train_args.py` choices and defaults for SFT

`pipeline/train/train_args.py` controls `instruction_following.py`.

### Model and format choices

- `--model_name`: `otter` (default), `flamingo`, `idefics`, `llama2`, `debug_model`, `fuyu`.
- `--instruction_format`: `simple` (default), `llama2`, `idefics`, `fuyu`.
- Fuyu/OtterHD should use `--model_name=fuyu --instruction_format=fuyu`.
- Otter-MPT instruction tuning should normally use `--model_name=otter --instruction_format=simple`.

### High-impact defaults

| Flag | Default | Notes |
|---|---:|---|
| `--run_name` | `otter-9b` | Used for the save directory and W&B run name. |
| `--training_data_yaml` | empty string | Must point to the prepared training YAML for SFT. |
| `--num_epochs` | `1` | Demo commands commonly use `3`. |
| `--batch_size` | `128` | This is per-process micro-batch for the script; demos override to `8`. |
| `--gradient_accumulation_steps` | `1` | Keep this consistent with Accelerate/DeepSpeed config intent. |
| `--learning_rate` | `1e-4` | Demo SFT uses `2e-5`; Fuyu demo uses `1e-5`. |
| `--lr_scheduler` | `constant` | Script accepts `constant`, `linear`, or `cosine` by convention. |
| `--warmup_steps` | `1000` | If `--warmup_steps_ratio` is set, the script computes warmup from total steps. |
| `--weight_decay` | `0.1` | Applied by grouped parameter selection. |
| `--workers` | `4` | Shared scripts derive it from GPU count and cap it for large jobs. |
| `--max_seq_len` | `2048` | SFT demo uses `1024`; lower it for memory pressure. |
| `--image_resolution` | `224,224` | The parser expects `x,y` with no spaces. |

### Logging, offline, and checkpoint flags

- `--report_to_wandb` enables `wandb.init(project=..., entity=..., name=run_name)` on rank 0.
- `--wandb_project` and `--wandb_entity` are only meaningful with `--report_to_wandb`.
- `--save_checkpoints_to_wandb` requires `--report_to_wandb`; the parser raises an error otherwise.
- `--offline` sets `WANDB_MODE=offline` and `TRANSFORMERS_OFFLINE=1`; all models and data must already be local/cache-available.
- `--external_save_dir` is joined with `--run_name`; if `--external_save_dir=checkpoints --run_name=my_run`, outputs go under `checkpoints/my_run`.
- `--save_hf_model` saves Hugging Face-format model assets. This is convenient for reuse but can consume large disk space.
- `--save_ckpt_each_epoch` saves final-weight style output after each SFT epoch and again at the end.
- `--save_steps_interval` enables intermediate SFT step checkpoints when positive.
- `--trained_ckpt` loads an existing PyTorch checkpoint state into the model before training.

## Data YAML handoff

Training only consumes the data YAML; schema authoring and conversion belong to [data-preparation](../../data-preparation/SKILL.md). For SFT, hand off or request a YAML with these operational properties:

- Top-level groups should be among `IMAGE_TEXT`, `TEXT_ONLY`, `VIDEO_TEXT`, and `IMAGE_TEXT_IN_CONTEXT`.
- Each dataset entry should identify a MIMIC-IT instruction JSON path via `mimicit_path`.
- Image/video datasets should also identify media storage through an `images_path`-style field.
- `num_samples` can limit samples; `-1` means use all samples in the documented demo pattern.
- At training startup, rank 0 runs a prerun YAML check through pytest and the loader also checks that referenced paths exist.

Do not solve schema or conversion errors inside this training sub-skill; route them to [data-preparation](../../data-preparation/SKILL.md).

## Shared script launch patterns

The shared demo launches add practical cluster patterns around the same `accelerate launch` command:

- Set `PYTHONPATH=.` before launching from the repository root.
- Derive hostnames, `MASTER_ADDR`, `MASTER_PORT`, machine count, and machine rank from the scheduler in multi-node runs.
- Pass `--machine_rank`, `--main_process_ip`, `--main_process_port`, `--num_machines`, and total `--num_processes` to `accelerate launch`.
- Derive workers from total GPU count and cap workers for large jobs to avoid excessive dataloader processes.
- Avoid destructive cleanup such as killing unrelated Python processes unless the user explicitly owns the node/session.
