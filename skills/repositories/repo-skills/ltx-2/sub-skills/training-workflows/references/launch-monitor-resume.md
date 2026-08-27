# Launch, Monitor, Resume, W&B, Hub, and Handoff

Training is expensive and stateful. Build and review commands first; launch only after explicit user approval. The bundled command builder prints commands but never runs them.

```bash
python path/to/training-workflows/scripts/build_training_command.py /path/to/config.yaml --distributed none
python path/to/training-workflows/scripts/build_training_command.py /path/to/config.yaml --distributed fsdp --num-processes 4 --disable-progress-bars
```

## Safe Phase Sequence

For an end-to-end training request, keep the user-facing phases explicit:

1. Create or confirm a run workspace and record assumptions.
2. Confirm the training mode and whether the run is LoRA or full fine-tune.
3. Probe local model components, matching text encoder, preprocessed data, W&B/Hub intent, and GPU availability.
4. Write or patch the run config and show the user the material assumptions before expensive work.
5. Route raw data, captioning, masks, references, and latent preprocessing to `data-preparation`; do not start those steps from this sub-skill.
6. Run strict config validation and a command-builder dry check.
7. Ask for approval before launching any real training process.
8. Monitor factual signals and checkpoint state; avoid quality predictions.
9. On completion, hand the checkpoint and config facts to `inference-pipelines` for production inference.

Do not mutate user data outside the run workspace, and do not enable external writes such as Hub upload without explicit user approval.

## Bundled launcher

The generated skill includes a self-contained launcher:

```bash
python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml
python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

From a shell with Accelerate available:

```bash
uv run accelerate launch path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
uv run accelerate launch --num_processes 2 path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

The helper scripts in this skill do not train, download models, generate media, or push credentials.

## Single-GPU Launch

From the bundled launcher path:

```bash
python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml
```

If terminal progress bars make logs hard to follow:

```bash
python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

Optionally restrict the visible GPU:

```bash
CUDA_VISIBLE_DEVICES=0 python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml
```

Before launching, strict validation should pass and the config should point to an existing `data.preprocessed_data_root` with every directory required by the selected strategy.

## Multi-GPU and Accelerate

Accelerate supports default profiles and explicit DDP/FSDP configs. Use DDP when each GPU can hold the model shard needed by data parallelism. Use FSDP for full fine-tuning or memory-sharded runs that require parameter sharding.

### Default Accelerate profile

```bash
uv run accelerate launch path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

Override process count:

```bash
uv run accelerate launch --num_processes 2 path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

Restrict GPUs:

```bash
CUDA_VISIBLE_DEVICES=0,1 uv run accelerate launch --num_processes 2 path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

### Bundled DDP/FSDP config files

The generated skill bundles the named Accelerate presets under `references/accelerate/`:

- `references/accelerate/ddp.yaml`
- `references/accelerate/ddp_compile.yaml`
- `references/accelerate/fsdp.yaml`
- `references/accelerate/fsdp_compile.yaml`

Examples:

```bash
CUDA_VISIBLE_DEVICES=0,1 \
uv run accelerate launch --config_file path/to/training-workflows/references/accelerate/ddp.yaml --num_processes 2 \
  path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
uv run accelerate launch --config_file path/to/training-workflows/references/accelerate/fsdp.yaml --num_processes 4 \
  path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
```

Compile variants can reduce step time on compatible systems but add compile overhead and may complicate debugging. If compile fails, fall back to the non-compile config before changing model/data settings.

## W&B Logging

Config keys:

```yaml
wandb:
  enabled: true
  project: "ltx-2-trainer"
  entity: null
  tags: ["t2v", "lora"]
  log_validation_videos: true
```

Credential checks should use the `wandb` package's own resolution rather than scraping token files. A safe probe is:

```bash
uv run python -c "import wandb; print(bool(wandb.Api().api_key))"
```

If W&B is enabled and the run resumes from a training state that includes a W&B run id, the trainer attempts to resume the same W&B run. Do not print API keys.

## Hugging Face Hub Upload

Config keys:

```yaml
hub:
  push_to_hub: true
  hub_model_id: "username/repository-name"
```

Hub upload occurs after checkpoint saving. It requires write access to the target repo and appropriate Hugging Face credentials, such as a logged-in CLI session or an environment token. Ask before enabling automatic upload because it writes external state.

## Output Files

The trainer writes under `output_dir`:

| Output | Meaning |
| --- | --- |
| `training_config.yaml` | Serialized final config used by the trainer. |
| `samples/` | Training-time validation outputs when validation is enabled. These are monitoring artifacts, not proof of final quality. |
| `checkpoints/lora_weights_step_00000.safetensors` | LoRA checkpoint weights for LoRA runs. Step number changes with the save step. |
| `checkpoints/model_weights_step_00000.safetensors` | Full model checkpoint weights for full fine-tunes. |
| `checkpoints/training_state_step_00000.pt` | Optional resume state, controlled by `checkpoints.save_training_state`. |

`checkpoints.keep_last_n` also controls cleanup of old training-state files.

## Resume vs Load Weights Fresh

Resume is explicit. The trainer does not automatically scan `output_dir` for prior checkpoints. Use `model.load_checkpoint`.

```yaml
model:
  load_checkpoint: "/path/to/outputs/checkpoints/lora_weights_step_01000.safetensors"
checkpoints:
  no_resume: false
```

Behavior matrix:

| Config | Behavior |
| --- | --- |
| `model.load_checkpoint: null` | Start from base model at step 0, even if `output_dir/checkpoints/` exists. |
| `load_checkpoint` points to weights and matching `training_state_step_*.pt` exists, `no_resume: false` | Load weights and resume scheduler/RNG/step state; W&B may resume if the state has a run id. |
| `load_checkpoint` points to weights but no matching state file exists | Load weights; start step counter at 0 with a warning. |
| `checkpoints.no_resume: true` | Load weights but intentionally ignore training state and start from step 0. Use when changing optimizer/scheduler/rank or doing a fresh continuation. |
| `save_training_state: "off"` | Future full resume is not possible from checkpoints saved by this run. |

If optimizer type, scheduler type, training mode, or LoRA rank differs from the saved state's fingerprint, the trainer warns and starts at step 0. Do not represent that as a proper resume.

## Monitoring Loop

During a live run, inspect without modifying state:

```bash
# Process status
ps -eo pid,etimes,cmd | grep -E 'launch_training.py|accelerate launch' | grep -v grep

# Recent log tail if logs are captured by the run manager
tail -n 80 /path/to/run.log

# GPU utilization and memory
nvidia-smi

# Checkpoints produced so far
find /path/to/output_dir/checkpoints -maxdepth 1 -type f | sort
```

Report factual signals only: current step, loss if logged, validation/checkpoint timestamps, GPU memory, W&B URL if available, and the exact next action. Avoid judging final quality from early validation samples.

## Interruption Recovery

1. Identify the latest complete weights file under `output_dir/checkpoints/`.
2. Check whether the matching `training_state_step_<same-step>.pt` exists and has nonzero size.
3. Patch `model.load_checkpoint` to the latest weights path.
4. Keep `checkpoints.no_resume: false` for a real resume; set it to `true` only when intentionally loading weights fresh.
5. Validate the config strictly.
6. Rebuild the launch command with the same distributed mode/GPU count unless the user deliberately changes hardware.

If the run was interrupted during a model-version change, verify preprocessing freshness before resume. LTX-2.3 and LTX 2.5 text embeddings are not interchangeable.

## Handoff to Inference

After training finishes, hand off to `inference-pipelines` with:

- Checkpoint path and whether it is LoRA or full weights.
- Base model/checkpoint family used for training.
- Training mode and relevant reference scale metadata for IC-LoRA.
- Validation prompts and sample paths, if the user wants them reviewed.
- Any unresolved caveats such as skipped validation, stale preprocessing risk, or partial backend verification.

Do not run production inference from this sub-skill unless the root skill explicitly routes that request here; inference pipelines own loading trained LoRAs for generation.
