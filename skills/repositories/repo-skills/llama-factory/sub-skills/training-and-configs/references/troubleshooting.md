# Troubleshooting

Use this reference to diagnose LlamaFactory v0 training and config failures. Do not trigger downloads or training as part of diagnosis unless the user asks.

## Unknown or Deprecated Args

Symptom:

```text
Got unknown args, potentially deprecated arguments: [...]
ValueError: Some specified arguments are not used by the HfArgumentParser
```

Likely causes:

- A pure CLI command used a misspelled `--flag`.
- A v1-only config key was used with v0 default mode.
- A YAML/JSON override was written as `--key value` after a config file instead of `key=value`.
- A key belongs to export/inference rather than train.

Fix path:

1. If using a config file, rewrite overrides as `key=value`.
2. Check whether the key belongs to model/data/training/finetuning/generation train arguments.
3. Route v1 config shapes to `v1-experimental` or set `USE_V1=1` only for v1 workflows.
4. Route export keys such as `export_dir` or adapter merge requests to `model-loading-and-export`.

## YAML/JSON Override Surprises

Symptoms:

- Override has no effect.
- List-like values are parsed as one string or split unexpectedly later.
- Boolean values behave differently from pure CLI flags.

Facts:

- With YAML/JSON files, LlamaFactory merges OmegaConf CLI overrides after loading the file.
- Use `key=value`, for example `max_steps=1 report_to=none`.
- Comma-separated strings are split by several dataclass `__post_init__` methods, including `dataset`, `eval_dataset`, `adapter_name_or_path`, `lora_target`, and freeze target lists.
- For pure CLI, boolean flags can be passed as flags; for file overrides, use `flag=true` or `flag=false`.

Safe check:

```bash
python scripts/render_train_command.py train.yaml max_steps=1 report_to=none
```

This verifies merge intent without importing LlamaFactory.

## Required or Incompatible Data Keys

Common parser/data argument errors:

- `Cannot specify val_size if dataset is None`: add `dataset` or remove `val_size`.
- `Cannot specify val_size if eval_dataset is not None`: use either `eval_dataset` or `val_size`, not both.
- `interleave_probs is only valid for interleaved mixing`: change `mix_strategy` from `concat` to an interleave strategy or remove `interleave_probs`.
- `The length of dataset and interleave probs should be identical`: align comma-separated dataset count and probabilities.
- `Streaming mode should have an integer val size`: use integer `val_size` for streaming.
- ``max_samples` is incompatible with `streaming``: remove one.
- ``mask_history` is incompatible with `train_on_prompt``: choose one masking strategy.

Schema/template errors belong to `data-and-templates`.

## Adapter and Quantization Restrictions

Common messages and fixes:

| Message | Cause | Fix |
| --- | --- | --- |
| `Adapter is only valid for the LoRA method.` | `adapter_name_or_path` with non-LoRA finetuning in train args. | Use `finetuning_type: lora` for adapter training/loading or remove adapter path. |
| `Quantization is only compatible with the LoRA or OFT method.` | `quantization_bit` with `full` or `freeze`. | Switch to LoRA/OFT QLoRA-style tuning or remove quantization. |
| `Please use scripts/pissa_init.py to initialize PiSSA for a quantized model.` | `pissa_init` on quantized model. | Initialize PiSSA separately before quantized training, or disable PiSSA. |
| `Cannot resize embedding layers of a quantized model.` | `resize_vocab: true` with quantization. | Resize before quantization or train non-quantized. |
| `Cannot create new adapter upon a quantized model.` | Existing adapter plus `create_new_adapter` on quantized model. | Use one adapter path or non-quantized flow. |
| `Quantized model only accepts a single adapter. Merge them first.` | Multiple adapters with quantized model. | Merge adapters in export workflow, then train/load one adapter. |
| `Cannot merge adapters to a quantized model.` | Export/merge attempted on loaded quantized model. | Route to `model-loading-and-export`; merge from non-quantized base. |

## Preference/RLHF Misconfiguration

- PPO requires `reward_model`; add a reward model path/URL or switch to SFT/DPO.
- `reward_model_type: lora` requires `finetuning_type: lora`; `reward_model_type: oft` requires `finetuning_type: oft`.
- `dpo_label_smoothing` only works with `pref_loss: sigmoid`.
- `pissa_init` is rejected for PPO, KTO, or DPO variants that use a reference model.
- ORPO and SimPO are `stage: dpo` with `pref_loss: orpo` or `pref_loss: simpo`; do not set `stage: orpo` or `stage: simpo`.

## Optional Kernel or Package Missing

Common optional features and packages:

- `use_unsloth: true` requires `unsloth`.
- `enable_liger_kernel: true` requires `liger-kernel`.
- `use_galore: true` requires `galore_torch`.
- `use_apollo: true` requires `apollo_torch`.
- `use_badam: true` requires `badam>=1.2.1`.
- `use_kt` paths require KTransformers-related packages.
- `USE_MCA=1` or `use_mca: true` requires `mcore_adapter`.
- `use_hyper_parallel: true` requires `hyper_parallel` and is limited to supported `pt`/`sft` paths.
- vLLM/SGLang keys are inference-oriented; route serving backend issues to `inference-and-serving`.

Fix path:

1. Disable the optional feature to validate the base config.
2. Install only the package needed for the selected feature.
3. Confirm hardware/backend compatibility before re-enabling.

## Memory and Precision Failures

Typical mitigations:

- Reduce `per_device_train_batch_size` and raise `gradient_accumulation_steps` to preserve effective batch size.
- Lower `cutoff_len` or enable packing only when it matches the data objective.
- Use `finetuning_type: lora` or QLoRA (`quantization_bit`) instead of full tuning.
- For full tuning, add DeepSpeed ZeRO-3 or FSDP and force torchrun.
- Use `bf16: true` on BF16-capable hardware; otherwise try `fp16: true` if supported.
- Disable expensive options: `compute_accuracy`, profiling, long generation metrics, large `eval_dataset`, or frequent evaluation.
- Set `save_only_model: true` only if optimizer/scheduler state is not needed for resume.

Do not promise that a config fits memory without knowing model size, sequence length, batch size, precision, optimizer, and GPU memory.

## Distributed Hangs and NCCL Errors

Check in order:

1. All nodes use the same code, config, visible devices, package versions, and dataset/model access.
2. `NNODES`, `NODE_RANK`, `NPROC_PER_NODE`, `MASTER_ADDR`, and `MASTER_PORT` are consistent.
3. `MASTER_ADDR:MASTER_PORT` is reachable between nodes and not blocked by firewalls.
4. `ddp_timeout` is large enough for model load and dataset preprocessing.
5. `deepspeed` or FSDP config path exists on every node.
6. Output/checkpoint paths are safe for the storage topology; avoid multiple nodes writing incompatible local paths.
7. If elastic launch is used, `RDZV_ID`, `MIN_NNODES`, `MAX_NNODES`, and `MAX_RESTARTS` are intentionally set.

For one-node debugging, simplify to:

```bash
FORCE_TORCHRUN=1 NPROC_PER_NODE=1 llamafactory-cli train train.yaml max_steps=1 report_to=none
```

Then scale to all local GPUs, then multi-node.

## Tracking and Logging Failures

- Use `report_to: none` to disable external integrations during debug.
- For Trackio, set `project`; otherwise validation raises ``--project` must be specified when using Trackio.`
- For SwanLab, prefer environment/secret management for API keys and set `use_swanlab: true` only when credentials and network are ready.
- For W&B/TensorBoard/MLflow/Neptune, ensure the corresponding package is installed and credentials are configured externally.
- If logging floods output, increase `logging_steps`.
- If `plot_loss: true` does not create the expected plot, confirm training reached logging steps and output directory is writable.

## Resume and Output Directory Issues

- `overwrite_output_dir: true` can replace prior outputs; ask before recommending it for valuable runs.
- `resume_from_checkpoint: null` starts fresh.
- Set `resume_from_checkpoint: path/to/checkpoint` to resume a specific checkpoint.
- If a run stopped before saving optimizer state and `save_only_model: true` was set, full resume may not be possible.
- If checkpoint discovery picks the wrong directory, pass an explicit `resume_from_checkpoint`.

## When to Escalate to Other Sub-Skills

- Dataset not found, dataset column mismatch, template mismatch, media load failure: `data-and-templates`.
- Adapter merge, value-head export, quantized export, tokenizer save, or hub export: `model-loading-and-export`.
- Prediction, chat, API, Web UI, vLLM, SGLang: `inference-and-serving`.
- Nested v1 configs, v1 trainer architecture, or `USE_V1=1`: `v1-experimental`.
