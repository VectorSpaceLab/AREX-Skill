# Training Workflows

This reference distills ms-swift training behavior into reusable command and config patterns. It is intentionally self-contained: examples use public `swift` commands and bundled skill scripts only.

## Choose `swift sft` or `swift pt`

- `swift sft` is the default supervised fine-tuning route for instruction/chat datasets, multimodal SFT, LoRA/QLoRA/full tuning, validation splits, and most training-to-inference handoffs.
- `swift pt` is the continued pre-training route. It disables the chat template and calculates loss over all tokens. In practice, treat it as `swift sft --use_chat_template false --loss_scale all` plus the pre-training dataset expectations.
- Both routes are available through the `swift` console command. Config files can be passed as the first argument: `swift sft train.yaml` or `swift pt train.json`.
- If `NPROC_PER_NODE` or `NNODES` is set, the top-level `swift` launcher runs `pt`, `sft`, `rlhf`, and `infer` through `torch.distributed.run` with matching distributed arguments.

## Build a Minimal SFT Command

Start from the smallest explicit command, then add memory, validation, and distribution flags:

```bash
swift sft \
  --model Qwen/Qwen2.5-7B-Instruct \
  --dataset ./train.jsonl \
  --split_dataset_ratio 0.05 \
  --train_type lora \
  --output_dir output/qwen2_5_lora_sft \
  --max_length 2048 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 1e-4 \
  --save_steps 500 \
  --save_total_limit 2
```

Important defaults and implications:

- `learning_rate` defaults to `1e-4` for LoRA-like tuners and `1e-5` for full-parameter tuning when omitted.
- `gradient_checkpointing` defaults on for training to reduce memory at the cost of speed.
- `eval_strategy` follows `save_strategy` unless no validation data exists; then evaluation is disabled.
- `output_dir` defaults to a model-derived directory, but automation should pass it explicitly.
- `add_version` creates versioned output subdirectories by default, which prevents accidental overwrite but changes the final checkpoint path.

## Continued Pre-training Pattern

Use `swift pt` when training on generative/corpus text rather than chat-style supervised conversations:

```bash
swift pt \
  --model Qwen/Qwen2.5-7B \
  --dataset ./corpus.jsonl \
  --train_type lora \
  --output_dir output/qwen2_5_cpt \
  --max_length 4096 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16
```

Review `use_chat_template` carefully. `swift pt` defaults it to false, while `swift sft` defaults it to true. If a user wants SFT on a base model and the model fails to stop or emits template artifacts, try `--template default` instead of forcing a chat template meant for instruction models.

## YAML/JSON Config Launches

A config file maps keys to CLI flags. Lists expand to repeated values, dictionaries become JSON strings, and an optional top-level `ENV` map is applied before launch. Existing shell environment variables win over config `ENV` entries.

```yaml
ENV:
  CUDA_VISIBLE_DEVICES: "0"
  MAX_PIXELS: "1003520"
model: Qwen/Qwen2.5-7B-Instruct
dataset:
  - ./train.jsonl
split_dataset_ratio: 0.05
train_type: lora
output_dir: output/qwen2_5_lora_sft
max_length: 2048
per_device_train_batch_size: 1
gradient_accumulation_steps: 16
gradient_checkpointing_kwargs:
  use_reentrant: false
```

Run it with:

```bash
swift sft train.yaml
```

Before launch, use the bundled validator:

```bash
python scripts/validate_training_config.py train.yaml --route sft
```

## Offline and Source-controlled Runs

For a run that must avoid network access:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 swift sft \
  --model ./models/qwen2_5_7b_instruct \
  --dataset ./data/train.jsonl \
  --use_hf true \
  --check_model false \
  --train_type lora \
  --output_dir output/offline_lora_sft
```

Use local dataset paths. For HuggingFace model semantics, set `--use_hf true`; for ModelScope defaults, omit it or set `--use_hf false`. For international ModelScope access, set `MODELSCOPE_DOMAIN=www.modelscope.ai`. The model/download choice should be explicit in reproducible commands.

## Tuning Modes

- `--train_type lora` trains adapter weights and saves adapter checkpoints. Hand the checkpoint to inference with `--adapters`.
- `--train_type full` updates full model weights. Hand the checkpoint to inference/deploy/export with `--model`.
- `--train_type qlora` reduces memory by quantized loading. Do not promise LoRA merge or vLLM/SGLang/LMDeploy acceleration for QLoRA-trained adapters; plan LoRA/full training if accelerated merged inference is required.
- Multimodal LoRA can target LLM, vision/audio tower, and aligner behavior through `freeze_llm`, `freeze_vit`, `freeze_aligner`, `target_modules`, `target_regex`, and learning-rate overrides.
- `modules_to_save` saves specified original modules alongside adapter weights, useful when embeddings or heads are trained during adapter tuning.

## Memory and Throughput Levers

Apply these in order, stopping once the run fits and remains stable:

1. Reduce `max_length` and multimodal pixel caps such as `MAX_PIXELS` or `VIDEO_MAX_PIXELS`.
2. Reduce `per_device_train_batch_size`; increase `gradient_accumulation_steps` to preserve effective batch size.
3. Keep `gradient_checkpointing true`; for plain DDP, add `--gradient_checkpointing_kwargs '{"use_reentrant": false}'` when checkpointing-related reducer errors occur.
4. Use LoRA or QLoRA instead of full tuning when acceptable.
5. Enable `packing true` or `padding_free true` only with a flash attention implementation such as `--attn_impl flash_attn`.
6. Consider DeepSpeed ZeRO or FSDP2 for larger models, but do not combine FSDP2 with DeepSpeed.

## Packing, Padding-free, Lazy Tokenization, and Cached Datasets

- `packing` packs samples toward `max_length`, improves utilization, and automatically enables `padding_free`; adjust learning rate and accumulation because the apparent sample count changes.
- `padding_free` flattens batch data to reduce padding without the same preprocessing cost. It still requires a supported flash attention implementation.
- `lazy_tokenize` delays tokenization until training. It defaults to false for LLM training and true for multimodal training to avoid preloading all media.
- `streaming` datasets require an explicit `max_steps` because the dataset length is undefined.
- `cached_dataset` can reuse preprocessed length metadata. When `truncation_strategy split` is used during cache creation, training must use the same `max_length` and truncation strategy.

## Distributed Training Patterns

Single-node DDP:

```bash
NPROC_PER_NODE=4 swift sft train.yaml
```

DeepSpeed built-in preset:

```bash
NPROC_PER_NODE=4 swift sft train.yaml --deepspeed zero2
```

FSDP2 built-in preset:

```bash
NPROC_PER_NODE=4 swift sft train.yaml --fsdp fsdp2
```

Notes:

- DeepSpeed is an optional dependency; install it only for DeepSpeed runs.
- DeepSpeed is not compatible with `device_map` simple model parallelism in this training path.
- FSDP2 is not compatible with `device_map` or DeepSpeed. Prefer `activation_checkpointing` in `fsdp_config` over ordinary `gradient_checkpointing` for FSDP2.
- `deepspeed_autotp_size` requires a DeepSpeed preset or config and is intended for full-parameter fine-tuning.

## Multimodal Training

For multimodal models:

- Use `MAX_PIXELS`, `VIDEO_MAX_PIXELS`, and model-specific pixel/frame environment variables to bound visual memory.
- `freeze_vit` defaults true and `freeze_aligner` defaults true; disable these freezes when you intentionally want to train the vision/audio tower or projector.
- `vit_gradient_checkpointing` defaults based on `freeze_vit`; if the tower is trainable, keep checkpointing unless speed matters more than memory.
- `lazy_tokenize true` is often helpful because it avoids loading all media before training.
- Use `packing` only when the model, attention implementation, and data shape support it.

## Checkpoints and Resume Semantics

- `save_strategy`, `save_steps`, `save_total_limit`, and `output_dir` control checkpoint cadence and retention.
- `create_checkpoint_symlink true` creates stable `best` and `last` symlinks under `output_dir`, useful for automation.
- `resume_from_checkpoint` resumes weights, optimizer state, random seed, and training progress. Keep other parameters unchanged unless intentionally changing the experiment.
- `resume_only_model true` loads only model weights from `resume_from_checkpoint`. For adapter tuning it sets `adapters`; for full tuning it sets `model`.
- `adapters` alone loads adapter weights but does not restore optimizer/random state and does not skip already-trained data.
- Training `load_args` defaults false, so do not assume a checkpoint `args.json` fully reconstructs a training run unless explicitly enabled.

## Training-to-Inference Handoff

Use the training artifact type to choose the next route:

- LoRA checkpoint: `swift infer --model BASE_MODEL --adapters CHECKPOINT_DIR` or rely on checkpoint `args.json` when appropriate.
- Full checkpoint: `swift infer --model CHECKPOINT_DIR`.
- LoRA acceleration with vLLM/SGLang/LMDeploy: merge/export first when supported, then route to inference/deployment.
- QLoRA adapter: avoid promising merged accelerated inference; if the user needs vLLM acceleration, recommend retraining as LoRA/full or exporting a supported quantized full model after merge where applicable.

Keep detailed inference, deployment, export, quantization, and evaluation workflows in their sibling sub-skills; training content should only explain the handoff boundary.
