# Training Troubleshooting

## Purpose

Use this reference to diagnose training launch, distributed backend, status, artifact, and performance failures. For column/schema errors, first use `../configuration-and-data/SKILL.md`; for metric/model internals use `../modeling-and-evaluation/SKILL.md`; for prompt/export failures use `../export-and-prompt/SKILL.md`.

## Quick triage

1. Run the environment checker without starting training:

   ```bash
   python sub-skills/training-and-experiments/scripts/check_training_environment.py \
     --config cfg.yaml \
     --check-torch \
     --check-cuda-home \
     --check-deepspeed
   ```

2. If multi-GPU, dry-run the command builder:

   ```bash
   sub-skills/training-and-experiments/scripts/distributed_train_wrapper.sh \
     --num-gpus 2 --yaml cfg.yaml
   ```

3. Inspect `<output_directory>/flags.json`, `logs.log`, and any `flags<N>.json` files.
4. Confirm `cfg.yaml` in the output directory reflects the CLI overrides you intended.

## Failure modes

| Symptom or error fragment | Likely cause | Recovery |
|---|---|---|
| `Please, provide a configuration file` | The command omitted both `-Y/--yaml` and deprecated `-C/--config`. | Use `python llm_studio/train.py -Y cfg.yaml`. |
| Override appears ignored | `--section.field` is misspelled or not present in the loaded config; unknown overrides are skipped. | Compare the saved output `cfg.yaml` with the intended value. Use exact field names from the config/data sub-skill. |
| `No GPU selected` | Config validation sees an empty GPU list. | Select at least one GPU in `environment.gpus`, or treat the run as a config-only smoke rather than a real trainer run. |
| `More GPUs selected than available` | Config was copied from a machine with different GPUs, or `CUDA_VISIBLE_DEVICES` hides selected devices. | Reset `environment.gpus` for the current visible devices and dry-run the launcher with the intended `CUDA_VISIBLE_DEVICES`. |
| `Deepspeed does not support single GPU training` | `environment.use_deepspeed` is true but fewer than two GPUs are selected. | Use at least two GPUs with DeepSpeed, or disable DeepSpeed. |
| `Deepspeed do not support backbone type int4/int8` | DeepSpeed is incompatible with quantized backbone dtypes in this trainer. | Set `architecture.backbone_dtype` to `float16` or `bfloat16`, or disable DeepSpeed. |
| `MissingCUDAException`, `CUDA_HOME`, `nvcc`, or DeepSpeed import fails before help text | PyTorch can see a driver but DeepSpeed cannot find a CUDA toolkit/compiler. | Install a CUDA toolkit compatible with the environment, set `CUDA_HOME` or `CUDA_PATH` to its root, ensure `bin/nvcc` exists, and rerun `check_training_environment.py --check-cuda-home --check-deepspeed`. |
| DeepSpeed import fails with a filesystem/`df` parsing `IndexError` | A known DeepSpeed filesystem-type probe can break on long wrapped device names in affected environments. | Use a patched DeepSpeed build or ask the environment owner to apply the repository's documented one-line `df -PT` fix to that DeepSpeed version; do not patch a shared environment without approval. |
| `GPU Out-of-Memory (OOM) error occurred` | Backbone, dtype, sequence length, batch size, or validation generation is too large for VRAM. | Lower `training.batch_size`, lower `tokenizer.max_length`, use LoRA, use `int4`/`int8` where compatible, enable gradient checkpointing, disable expensive validation settings, or use more GPUs/DeepSpeed. |
| `NaN caught in loss during training` | Learning rate, dtype, or mixed precision is unstable. | Reduce `training.learning_rate`, change precision dtype, disable `environment.mixed_precision`, or set `training.gradient_clip` above 0. |
| `NaN caught during mixed precision inference` | Validation/generation under mixed precision is unstable. | Disable mixed precision for the smoke, change dtype, reduce learning rate for retraining, or add gradient clipping. |
| W&B with relative step size rejected | `logging.logger: W&B` plus `logging.log_step_size: relative` is invalid. | Set `logging.log_step_size: absolute` for W&B. |
| `flags.json` never appears | Process died before the Wave launcher/trainer wrote status, often during imports, CUDA/DeepSpeed initialization, or path setup. | Run the environment checker and direct help/import checks; inspect terminal stderr and package installation. |
| `flags.json` says `failed` with `Data error` | Dataset path, columns, validation split, or problem-type schema failed during training. | Route to configuration/data troubleshooting and validate the dataset before relaunch. |
| `flags.json` says `failed` with `Metric error` | Selected metric is incompatible with problem type or data, or an AI judge metric lacks credentials/network. | Route metric compatibility to modeling/evaluation; provide credentials or switch to a local metric such as BLEU/Perplexity where appropriate. |
| `checkpoint.pth` missing after `finished` | Checkpoint saving was disabled, the run was zero/validation-only with incompatible settings, or checkpoint conversion failed. | Inspect `training.save_checkpoint`, logs, DeepSpeed conversion messages, and disk space. Export/chat requires checkpoints. |
| `validation_predictions.csv` missing | The run did not reach validation postprocessing or validation failed. | Inspect `logs.log`, metric settings, validation dataset, and `flags.json` status. |
| `Not enough disk space` | Config check found less free disk than required. | Move `output_directory`, free disk, or reduce checkpoint mode (`disable` for debugging only, `last` for normal use). |

## DeepSpeed/CUDA diagnosis recipe

```bash
python sub-skills/training-and-experiments/scripts/check_training_environment.py \
  --check-torch \
  --check-cuda-home \
  --check-deepspeed \
  --diagnose-error "MissingCUDAException: CUDA_HOME does not exist"
```

Expected useful output should answer:

- whether PyTorch imports and sees CUDA;
- which CUDA version PyTorch was built for;
- whether `CUDA_HOME`/`CUDA_PATH` is set;
- whether `nvcc` is discoverable;
- whether DeepSpeed imports;
- which concrete next step is needed.

## CPU and tiny-smoke caveat

The repository includes tiny CPU-labeled integration configs that reduce dtype/model settings and are useful for verification planning. The trainer is still GPU-oriented and current config checks validate selected GPU count. Treat generated CPU-like configs as safe construction aids until you have verified the exact package version and host behavior.
