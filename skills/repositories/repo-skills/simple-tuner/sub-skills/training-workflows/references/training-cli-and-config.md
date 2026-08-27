# Training CLI and config

This reference owns the safe path from installation to a command line. It does not cover dataloader schema internals or adapter conversion details.

## Install and platform selection

Choose the install extra from the intended runtime hardware, not from the Creator inspection environment:

| Runtime target | Install route | Decision notes |
| --- | --- | --- |
| NVIDIA CUDA | `pip install 'simpletuner[cuda]'` | Normal CUDA route for most NVIDIA GPUs. Real training still needs matching driver, VRAM, model access, and data. |
| NVIDIA CUDA 13 / Blackwell | `pip install 'simpletuner[cuda13]' --extra-index-url https://download.pytorch.org/whl/cu130` | Use for CUDA 13/B-series targets; use the TransformerEngine extra only when FP8 TransformerEngine is explicitly planned. |
| AMD ROCm | `pip install 'simpletuner[rocm]' --extra-index-url https://download.pytorch.org/whl/rocm7.1` | DeepSpeed is not the normal route on ROCm. MI300-class hosts may need AMD SMI library setup; SimpleTuner also enables ROCm tunable-op/TF32 environment defaults when it detects a HIP build. |
| Apple Silicon | `pip install 'simpletuner[apple]'` | Use MPS-aware configs. Flux.1 training is documented as not currently working on Apple; some LTX Video 2 examples target MPS. Metal Flash Attention requires a separate manual build. |
| CPU-only | `pip install 'simpletuner[cpu]'` or base package for inspection | Acceptable for config inspection, help, and light validation. Treat real training as manual/expensive and usually impractical. |

SimpleTuner package metadata advertises Python `>=3.12,<3.14`. The docs often use Python 3.13 examples. Do not copy private environment prefixes into instructions.

## Public commands

| Command | Use it for | Notes |
| --- | --- | --- |
| `simpletuner configure` | Upstream interactive configuration route. | Recommended for creating or modifying a `config.json`. It does not replace dataloader preparation. It can be passed a config path such as `simpletuner configure config/foo/config.json` to edit an existing environment. |
| `simpletuner train` | Preferred wrapper for normal CLI training. | Supports `--env`, `--example`, or positional `env=...` / `example=...`; finds configs in the current directory or `config/`; builds an `accelerate launch` command. |
| `simpletuner-train` | Low-level training entry point. | Use when `ENV`/`CONFIG_BACKEND`/`CONFIG_PATH` are already resolved or when using the `cmd` backend. The wrapper is safer for examples and environment discovery. |

The `simpletuner train` wrapper passes extra training options as positional `key=value` tokens. Example:

```bash
simpletuner train --env flux-lora max_train_steps=100 report_to=none
```

For direct training entry, use normal option spelling:

```bash
CONFIG_BACKEND=cmd simpletuner-train --model_family=flux --model_type=lora --output_dir=output/flux-lora --data_backend_config=config/flux-lora/multidatabackend.json --optimizer=adamw_bf16
```

## Config backend decision table

SimpleTuner reads config selection from environment variables and from the wrapper:

- `ENV` / `SIMPLETUNER_ENV`: names a config environment such as `default` or `flux-lora`.
- `CONFIG_BACKEND` / `SIMPLETUNER_CONFIG_BACKEND` / `CONFIG_TYPE`: one of `json`, `toml`, `env`, or `cmd`.
- `CONFIG_PATH`: path override used reliably by the JSON loader and by wrapper environment validation. In this source snapshot, TOML and env-file loading are environment-directory based; do not assume an arbitrary `CONFIG_PATH` will redirect them.

| Backend | Typical layout | Choose when | Avoid when |
| --- | --- | --- | --- |
| `json` | `config/config.json` or `config/<env>/config.json` | You want explicit structured config, `simpletuner configure`, or a direct `CONFIG_PATH` override. JSON keys are the training option names without requiring leading `--`. | You need shell-style environment expansion as the primary config. |
| `toml` | `config/config.toml` or `config/<env>/config.toml` | You prefer TOML and the config is inside the standard environment layout. | The config lives at an arbitrary path outside `config/<env>/`; use JSON or `cmd` instead. |
| `env` | `config.env`, `config/config.env`, or `config/<env>/config.env` | You already maintain `config.env` variables such as `MODEL_FAMILY`, `TRAIN_BATCH_SIZE`, and `TRAINER_EXTRA_ARGS`. | You need nested structures or many model-specific fields; JSON is usually clearer. |
| `cmd` | CLI options passed directly | You are composing a one-off command or using `simpletuner-train` with explicit `--field=value` options. | You need a long, reviewable, reusable training plan. |

Auto-detection checks for JSON, then TOML, then env files inside the selected config directory. If no backend is set and no config file exists, `simpletuner train` reports that no config file was found.

## Wrapper behaviour worth preserving

Source evidence: `simpletuner/cli/train.py` and `simpletuner/helpers/configuration/loader.py`.

- `simpletuner train` with no `--env`/`--example` searches the current directory first, then `config/`, for `config.json`, `config.toml`, or `config.env`.
- `simpletuner train --env name` validates a non-default environment against candidate config files before launching.
- `simpletuner train example=name` or `simpletuner train --example name` uses packaged examples and sets `ENV=examples/<name>`, `CONFIG_BACKEND`, and `CONFIG_PATH` from that example.
- The wrapper uses an existing Accelerate config if found; otherwise it emits `accelerate launch` with `mixed_precision`, `TRAINING_NUM_PROCESSES`, `TRAINING_NUM_MACHINES`, and `TRAINING_DYNAMO_BACKEND` values.
- Wrapper-specific extra controls include `accelerate_config`, `accelerate_extra_args`, `num_processes`, `num_machines`, and `dynamo_backend` when supplied as positional `key=value` tokens.

## Decision-level training options

Use these groups to decide the workflow shape; do not copy the full `OPTIONS.md` catalog into a run plan.

| Option group | Representative fields | Decision |
| --- | --- | --- |
| Model identity | `model_family`, `model_flavour`, `model_type`, `pretrained_model_name_or_path` | Pick a supported model family/flavour and whether the run is LoRA/LyCORIS/full. If adapter targets or formats matter, consult `sub-skills/model-and-adapter-tooling/`. |
| Data entry | `data_backend_config`, `train_batch_size`, `allow_dataset_oversubscription` | This sub-skill only checks high-level batch/topology implications. Route schema, captions, caches, and conditioning to `sub-skills/data-and-config/`. |
| Runtime length | `max_train_steps`, `num_train_epochs`, `strict_epoch_limit` | Use `max_train_steps` for bounded smoke tests and long fixed-step runs; use epochs when repeats/dataset passes define the objective. |
| Optimizer and LR | `optimizer`, `optimizer_config`, `learning_rate`, `lr_scheduler`, `gradient_accumulation_steps` | Choose a compatible optimizer/backend pair. Do not enable fused backward paths with gradient accumulation. |
| Precision and memory | `mixed_precision`, `base_model_precision`, `quantize_via`, `gradient_checkpointing`, `offload_during_startup`, group offload fields | Use lower precision, quantization, checkpointing, and offload to fit large models. Validate platform support before mixing with FSDP2, ROCm, MPS, or custom attention. |
| Distributed | `num_processes`, `num_machines`, DeepSpeed JSON, `fsdp_enable`, `context_parallel_size` | Plan with [distributed and memory](distributed-and-memory.md) before changing topology or resuming. |
| Validation/eval | `validation_method`, `validation_resolution`, `validation_step_interval`, `evaluation_type`, `eval_loss_disable`, `validation_using_datasets`, `eval_dataset_id` | Local validation is default. External validation requires a user-provided script and a checkpoint if `{local_checkpoint_path}` is used. CLIP scores and eval loss are useful but can add downloads/compute. |
| Checkpointing/resume | `checkpoint_step_interval`, `checkpoint_epoch_interval`, `checkpoints_total_limit`, `resume_from_checkpoint`, `delete_invalid_checkpoints`, disk-low fields | Keep resume topology stable. Use delete-invalid only for local checkpoints under `output_dir` and only when that behaviour is intended. |
| Reporting/publishing | `report_to`, `push_to_hub`, `publishing_config`, webhooks | Reporting to WandB/TensorBoard/Comet and publishing can require credentials or network; do not enable without approval. |

## Safe command builder recipes

The helper prints a shell command and never trains:

```bash
python skills/disco/simple-tuner/sub-skills/training-workflows/scripts/build_training_command.py --env flux-lora --config-backend json -- max_train_steps=100 report_to=none
```

Typical outputs are intentionally simple:

```bash
simpletuner train --env flux-lora max_train_steps=100 report_to=none
CONFIG_BACKEND=json CONFIG_PATH=config/flux-lora/config.json simpletuner-train --model_family=flux --model_type=lora
```

Before running any printed command, confirm the user-approved hardware, dataset paths, model access, `output_dir`, and resume topology.
