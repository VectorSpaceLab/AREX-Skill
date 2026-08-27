# Fine-tuning troubleshooting

Use this reference to diagnose setup, data, memory, DDP, W&B, and checkpoint issues for the LoRA fine-tuning workflow.

## Data validation failures

### `KeyError: 'input'` or missing-field validation errors

Cause: the training prompt builder indexes `instruction`, `input`, and `output` for every record. Even when no extra context is needed, the `input` key is expected.

Fix:

```json
{"instruction": "问题文本", "input": "", "output": "答案文本"}
```

Do not omit `input`; use an empty string. Confirm every JSONL line is an object and every required value is a string.

### `JSONDecodeError: Extra data` when using `json.load`

Cause: the medical training dataset is newline-delimited JSON even when the file suffix is `.json`. A whole-file `json.load()` expects one JSON document, not one object per line.

Fix: validate as JSONL, or use a loader that supports JSON lines. The training workflow's Datasets JSON loader can handle local `.json`/`.jsonl` data files, but custom validators must be JSONL-aware.

### Empty validation split or split-size errors

Cause: `val_set_size` is a fixed count. If it is larger than or too close to the dataset size, the train split may become empty or invalid.

Fix: lower `--val-size`, set `--val-size 0` to disable evaluation, or provide a larger dataset.

## Missing Python dependencies

The training implementation imports at least:

- `torch`
- `transformers`
- `peft`
- `datasets`
- `fire`
- `wandb`

The legacy requirements list includes `transformers`, `peft`, `datasets`, `fire`, `wandb`, `accelerate`, `bitsandbytes`, `sentencepiece`, and related utilities, but it does not pin or install `torch`. Install a Torch build that matches the target CUDA/driver or CPU-only validation scope before attempting real training.

Common symptoms:

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: No module named 'torch'` | Torch absent; requirements did not install it. | Install compatible Torch separately. |
| `ModuleNotFoundError: No module named 'peft'` | PEFT stack absent or wrong env active. | Install/activate the intended environment. |
| `ModuleNotFoundError: No module named 'fire'` | CLI dependency missing. | Install `fire` or use an environment with requirements installed. |
| `ModuleNotFoundError: No module named 'wandb'` | W&B package absent while default W&B reporting is enabled. | Install `wandb` or pass an empty W&B project/disable W&B. |

## CUDA, bitsandbytes, and 8-bit load issues

Actual training loads the base model with `load_in_8bit=True`, `torch_dtype=torch.float16`, and a device map. This usually requires a CUDA-capable environment with compatible `bitsandbytes`, Torch, CUDA runtime, GPU driver, and model architecture support.

Common symptoms:

- `ImportError` or warnings from `bitsandbytes` about CUDA libraries.
- `load_in_8bit=True` not supported in the installed Transformers/bitsandbytes combination.
- CPU-only Torch build selected accidentally.
- Device-map errors when CUDA devices are hidden or unavailable.

Actions:

1. Confirm the active environment has a CUDA-enabled Torch build if real training is intended.
2. Confirm `bitsandbytes` is compatible with the CUDA runtime and GPU architecture.
3. Confirm `CUDA_VISIBLE_DEVICES` exposes the intended GPUs.
4. Keep command-builder and data-validation checks separate from real model training; they do not prove CUDA readiness.

## Out-of-memory during training

Symptoms include CUDA OOM, allocation failure, kernel restarts, or immediate failure after model/tokenizer load.

Reduce memory in this order:

1. Lower `--micro-batch-size`; for 24GB GPUs start at `1` or `2`.
2. Lower `--batch-size` so gradient accumulation remains valid.
3. Lower `--cutoff-len` from `256` to `128` if the task tolerates shorter prompts.
4. Disable extra validation with `--val-size 0` only if evaluation memory is the blocker and a separate validation plan exists.
5. Avoid the shell example's `micro_batch_size=128` unless using high-memory hardware.

Remember: the README resource note describes an A100-SXM-80GB run where `batch_size=128` used about 40GB. That is not a safe default for 24GB hardware.

## DDP and launch problems

### `gradient_accumulation_steps` becomes zero

Cause: under DDP the implementation computes:

```text
(batch_size // micro_batch_size) // WORLD_SIZE
```

If the result is `0`, Trainer configuration is invalid.

Fix: increase `batch_size`, reduce `micro_batch_size`, or reduce DDP process count. Check the bundled builder warnings before launching.

### Wrong GPU per process or rank errors

Cause: DDP uses `LOCAL_RANK` to select the device map. Missing or mismatched rank variables can put all processes on one GPU or fail device mapping.

Fix:

- Use a launcher that sets `WORLD_SIZE` and `LOCAL_RANK` consistently.
- Ensure each process sees the intended CUDA devices.
- Avoid mixing manual `WORLD_SIZE`/`LOCAL_RANK` exports with an incompatible launcher.

### Unexpected DataParallel behavior

If multiple GPUs are visible but DDP is not active, the model is marked parallelizable to keep Trainer from using its own DataParallel. If multi-GPU behavior is needed, prefer explicit DDP launch rather than relying on implicit Trainer parallelism.

## W&B surprises

### W&B starts even though no run name was provided

Cause: default `wandb_project` is `llama_med`, which enables W&B. Environment variable `WANDB_PROJECT` can also enable it.

Fix: use `--disable-wandb` in the bundled builder, or explicitly pass an empty W&B project and clear inherited W&B environment variables before real execution.

### Authentication or network prompts

Cause: W&B logging is enabled in an environment without credentials or network access.

Fix: disable W&B for local/debug runs, or preconfigure W&B credentials intentionally.

## Checkpoint resume problems

### `Checkpoint ... not found`

Cause: the path does not contain `pytorch_model.bin` or `adapter_model.bin` in the expected location.

Fix: point `resume_from_checkpoint` at the checkpoint directory itself, not its parent, or use the final adapter directory if it contains adapter weights.

### Resume loads adapter but does not resume Trainer step

Cause: when only `adapter_model.bin` is found, the implementation loads PEFT weights and sets Trainer resume to false. This resumes adapter weights but not optimizer/scheduler/global-step state.

Fix: use a full Trainer checkpoint when optimizer/scheduler continuity matters; use adapter-only resume when warm-starting a new run is acceptable.

### Shape mismatch or incompatible adapter

Cause: LoRA rank, target modules, base model family, or tokenizer/model architecture changed between runs.

Fix: keep `lora_r`, `lora_alpha`, target modules, and base model compatible with the checkpointed adapter, or start a new output directory.

## Output directory issues

- Existing `output_dir` contents can mix old and new adapters. Use a fresh output directory for new experiments unless intentionally resuming.
- Trainer keeps at most five save checkpoints (`save_total_limit=5`), so older step checkpoints may be removed during long runs.
- Use `checkpoint-export` for adapter merge/export tasks; this sub-skill only covers training and adapter checkpoint expectations.
