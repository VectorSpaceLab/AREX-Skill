# Backend And Performance

## Purpose

Read this before selecting devices, distributed launchers, DeepSpeed, precision, optimizer/scheduler settings, or memory-saving fine-tuning options.

## Baseline runtime expectations

H2O LLM Studio is GPU-oriented. The public setup guidance requires Python 3.10, Linux/Ubuntu-class hosts, a recent NVIDIA driver, and recommends at least 24GB GPU memory for larger models. CPU and CPU-like tiny configs are useful for command construction, config/data mechanics, and limited smoke verification, but they are not proof of production fine-tuning performance.

Start small: a small backbone, low `tokenizer.max_length`, small per-GPU `training.batch_size`, `training.epochs: 0` or `1`, and a local output directory with enough free disk.

## CUDA and `nvcc`

PyTorch CUDA availability and DeepSpeed CUDA extension checks are separate. A system can have `torch.cuda.is_available() == True` and still fail DeepSpeed import or `llm_studio/train.py -h` if no CUDA toolkit with `nvcc` is visible.

Use the bundled checker:

```bash
python sub-skills/training-and-experiments/scripts/check_training_environment.py \
  --check-torch \
  --check-cuda-home \
  --check-deepspeed
```

A healthy CUDA toolkit setup has:

- `CUDA_HOME` or `CUDA_PATH` pointing to a toolkit root, not just a driver directory;
- an executable `bin/nvcc` under that toolkit root, or `nvcc` available on `PATH`;
- PyTorch built for a CUDA version compatible with the driver;
- enough free GPU memory for the chosen backbone, dtype, sequence length, and batch size.

## DDP and DeepSpeed

`torchrun`/DDP is the direct multi-GPU path. The trainer infers distributed mode from `WORLD_SIZE` and `LOCAL_RANK`, then uses NCCL for GPU process groups and a Gloo CPU group for coordination.

DeepSpeed is enabled by `environment.use_deepspeed: true`. H2O LLM Studio builds a DeepSpeed config from the experiment config:

- `environment.deepspeed_method: ZeRO2` uses ZeRO stage 2 with all-gather settings;
- `environment.deepspeed_method: ZeRO3` uses ZeRO stage 3 with stage-3 prefetch and persistence thresholds;
- `training.batch_size` becomes `train_micro_batch_size_per_gpu`;
- `training.grad_accumulation` becomes `gradient_accumulation_steps`;
- `architecture.backbone_dtype` controls DeepSpeed fp16/bf16 enablement.

Hard constraints verified in the config checks and trainer:

- DeepSpeed is rejected for single-GPU training; select at least two GPUs or disable DeepSpeed.
- DeepSpeed is rejected with `architecture.backbone_dtype: int4` or `int8`; use `float16` or `bfloat16`.
- DeepSpeed handles mixed precision internally, so the trainer does not wrap DeepSpeed forward passes in a nested PyTorch autocast context.
- Torch compile is skipped when DeepSpeed is enabled.

DeepSpeed can reduce memory pressure for large models but may slow training and requires a working CUDA toolkit. The public docs also recommend NVLink for DeepSpeed sharded training.

## Precision, quantization, and memory levers

High-impact memory settings:

- `architecture.backbone_dtype`: `int4`/`int8` reduce memory for quantized pretrained backbones; `float16`/`bfloat16` are required for DeepSpeed.
- `training.lora`: LoRA is the default memory-efficient fine-tuning path for causal language modeling configs.
- `training.use_dora`: enables DoRA, a LoRA-based method expected to help especially at low ranks such as `lora_r: 4`.
- `training.use_rslora`: switches scaling from `lora_alpha / lora_r` to `lora_alpha / sqrt(lora_r)` for Rank-Stabilized LoRA.
- `training.lora_target_modules`: empty string means H2O LLM Studio targets all linear layers.
- `architecture.gradient_checkpointing`: reduces VRAM at the cost of extra forward computation; enable when hitting OOM.
- `tokenizer.max_length`: shorter sequences reduce memory and runtime.
- `training.batch_size`: this is per GPU; lower it before changing more invasive settings.
- `training.grad_accumulation`: increases effective batch size without increasing per-step memory as much as `batch_size`.
- `environment.mixed_precision` and `environment.mixed_precision_dtype`: reduce memory/speed cost on compatible hardware; disable or change dtype if NaNs occur.
- `training.gradient_clip`: can stabilize training with volatile gradients.

The FAQ emphasizes that backbone dtype and maximum sequence length have the largest impact on GPU memory; batch size and model size are the next practical knobs.

## Optimizers and schedulers

Verified optimizer names:

- `Adam`
- `AdamW`
- `SGD`
- `RMSprop`
- `Adadelta`
- `AdamW8bit`

`AdamW8bit` comes from bitsandbytes and is therefore more backend-sensitive than plain PyTorch optimizers.

Verified scheduler names:

- `Constant`
- `Cosine`
- `Linear`

Scheduler knobs include `training.warmup_epochs`, `training.min_learning_rate_ratio`, and `training.evaluation_epochs`. `training.evaluation_epochs` can be fractional and controls validation frequency.

## Logging and external services

`logging.logger: None` keeps only local logs/charts. `logging.logger: W&B` initializes Weights & Biases with project/entity settings and requires a valid API key and network. H2O LLM Studio disables code/git upload for W&B and falls back to a dummy external logger if initialization fails.

AI-judge validation metrics and Hugging Face model downloads can introduce network, credential, or rate-limit failures; route metric internals to `../modeling-and-evaluation/SKILL.md` and export/publish actions to `../export-and-prompt/SKILL.md`.
