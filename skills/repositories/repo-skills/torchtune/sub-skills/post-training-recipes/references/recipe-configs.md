# Recipe Configs

Use this reference to adapt torchtune training configs safely. For general CLI/config syntax, use `../cli-and-config/SKILL.md`; this file focuses on training-recipe-specific fields and method choices.

## Config Discovery Pattern

- List recipe/config pairs: `tune ls` or `tune ls <recipe>`.
- Inspect a config: `tune cat <config-name>`.
- Copy before extensive edits: `tune cp <config-name> ./custom.yaml --make-parents`.
- Validate local YAML: `tune validate ./custom.yaml`.
- Build command without execution: `python sub-skills/post-training-recipes/scripts/build_tune_command.py ...`.

`tune validate` accepts a local YAML path. It checks config shape/component validation but does not prove the model files, dataset, GPU count, optional packages, or credentials are available.

## Override Placement

The command shape is:

```bash
tune run [TORCHRUN-OPTIONS] <recipe> --config <config-or-path> [KEY=VALUE OVERRIDES]
```

- Torchrun options belong before `<recipe>`.
- Config overrides belong after `--config <...>`.
- Use `~key` deletion syntax when the sibling CLI/config skill confirms the target config supports it and the copied YAML still has the field.
- Quote shell-sensitive values such as lists, paths with spaces, or JSON-like strings.

## Common Training Config Sections

| Section | What to check before execution |
| --- | --- |
| `model` | Builder family matches checkpoint/tokenizer; LoRA/QLoRA/DoRA/QAT flags are coherent. |
| `tokenizer` | Tokenizer path matches the model family and checkpoint source. |
| `checkpointer` | Component matches checkpoint format; directory, files, output dir, and model type are correct. |
| `ref_checkpointer` | DPO/PPO reference model points to the intended frozen reference. |
| `teacher_checkpointer` | KD teacher points to the intended larger/fine-tuned teacher. |
| `dataset` / `dataset_val` | Dataset component and local/remote data fields match the task and split. |
| `optimizer` | Optional optimizer package is installed; optimizer fields match the selected optimizer. |
| `lr_scheduler` | Scheduler arguments match steps/epochs. |
| `loss` | Loss component matches method: CE/SFT, DPO/RSO, PPO, KD, or QAT flow. |
| `quantizer` | QAT recipes use QAT quantizers; inference/quantize recipes use post-training quantizers. |
| `metric_logger` | DiskLogger is local-only; W&B/Comet require optional package and login. |
| `device` / `dtype` | Hardware supports the device and dtype, especially `bf16`. |
| `output_dir` | Directory is writable, durable enough, and not a temporary path that will disappear. |

## LoRA / QLoRA / DoRA Fields

LoRA recipe configs generally use model builders whose component path contains `lora_`. Important knobs:

| Field | Meaning | Notes |
| --- | --- | --- |
| `model.lora_attn_modules` | Attention projection modules to adapt | Common values include `q_proj`, `k_proj`, `v_proj`, `output_proj`. |
| `model.apply_lora_to_mlp` | Add adapters to MLP layers | More trainable params and memory; often improves quality. |
| `model.apply_lora_to_output` | Add adapter to output projection | Can be large for vocab-sized projection. |
| `model.lora_rank` | Adapter rank | Higher rank increases capacity and memory. |
| `model.lora_alpha` | Adapter scaling | Often scaled with rank in experiments. |
| `model.lora_dropout` | Adapter dropout | Defaults are often `0.0`; tune for regularization. |
| `model.quantize_base` | QLoRA/QDoRA base-weight quantization | Requires torchao/NF4 support and suitable hardware/runtime. |
| `model.use_dora` | DoRA behavior | Adds magnitude parameter overhead; may improve quality at low ranks. |

Example dry QLoRA adaptation:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_finetune_single_device llama3_2/3B_qlora_single_device \
  --override model.lora_rank=16 \
  --override model.lora_alpha=32 \
  --override model.quantize_base=True \
  --override optimizer='bitsandbytes.optim.PagedAdamW8bit' \
  --override '~optimizer.foreach' \
  --override output_dir='./runs/qlora-dry-plan'
```

Dependency warning: `bitsandbytes` optimizers are optional and are mainly documented for single-device low-memory use. Torchao is used for QLoRA/QAT quantization components. Do not run until optional packages are installed and the device supports the selected path.

## DPO Config Pattern

DPO configs require preference data and a policy/reference relationship.

- LoRA DPO recipes: `lora_dpo_single_device`, `lora_dpo_distributed`.
- Full DPO recipe: `full_dpo_distributed`.
- Common loss component: `torchtune.rlhf.loss.DPOLoss` or related DPO-style losses.
- `ref_checkpointer` should intentionally point to the frozen reference model, not accidentally to the just-trained policy output.
- If using LoRA adapters as policy/reference separation, verify adapter checkpoint behavior with `../training-utilities-and-rlhf/SKILL.md`.

Safe dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_dpo_distributed llama3_1/8B_lora_dpo \
  --nproc-per-node 2 \
  --override checkpointer.checkpoint_dir='<policy-start-dir>' \
  --override ref_checkpointer.checkpoint_dir='<reference-dir>' \
  --override output_dir='<dpo-output-dir>'
```

## PPO Config Pattern

PPO configs are more complex than SFT/DPO. Expect policy, reference policy, value model, reward model, PPO batch controls, and sometimes optional `bitsandbytes` optimizers.

Preflight checklist:

- `output_dir` exists or the recipe-specific notes say to create it first.
- Policy, reference policy, value, and reward checkpointers are deliberate.
- `batch_size`, `ppo_batch_size`, `forward_batch_size`, and `gradient_accumulation_steps` fit memory.
- Optional `bitsandbytes` package is installed if the optimizer component uses it.
- `dtype` is `bf16` or `fp32`; PPO recipe docs reject full `fp16`.

## KD Config Pattern

KD configs contain both student and teacher paths. Use KD when the target is to train a smaller model or adapter from a larger/better teacher.

Common controls:

- `teacher_checkpointer.*`: larger/fine-tuned teacher source.
- `checkpointer.*`: student source.
- `kd_ratio`: balances class loss vs distillation loss.
- `optimizer.lr`: often tuned in KD experiments.
- `loss`: KD configs commonly use memory-conscious KD loss components.

Safe dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  knowledge_distillation_distributed qwen2/1.5_to_0.5B_KD_lora_distributed \
  --nproc-per-node 4 \
  --override teacher_checkpointer.checkpoint_dir='<teacher-dir>' \
  --override checkpointer.checkpoint_dir='<student-dir>' \
  --override kd_ratio=0.25 \
  --override output_dir='<kd-output-dir>'
```

## QAT Config Pattern

QAT training simulates quantization during finetuning, but the follow-up conversion/evaluation belongs to the inference/eval/quantization sub-skill.

- Full QAT: `qat_single_device` or `qat_distributed`.
- QAT + LoRA: `qat_lora_finetune_distributed`.
- QAT configs must contain a QAT quantizer such as `torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer`.
- QAT recipe code rejects non-QAT quantizer modes for QAT finetuning.
- Some QAT recipe paths reject or limit `compile=True`; keep `compile=False` unless current evidence proves support for the exact recipe.

Safe dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  qat_distributed llama3/8B_qat_full \
  --nproc-per-node 4 \
  --override quantizer._component_='torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer' \
  --override compile=False \
  --override output_dir='<qat-output-dir>'
```

## Memory And Performance Knobs

| Knob | Use when | Cautions |
| --- | --- | --- |
| `batch_size` | Controls microbatch size | Larger values raise memory use. |
| `gradient_accumulation_steps` | Increase effective batch without fitting larger microbatches | More steps per optimizer update. |
| `enable_activation_checkpointing=True` | Save activation memory | Trades compute for memory. |
| `enable_activation_offloading=True` | Further reduce GPU memory | Use with activation checkpointing; may slow training. |
| `optimizer_in_bwd=True` | Save optimizer memory for supported recipes | Often requires `gradient_accumulation_steps=1`. |
| `fsdp_cpu_offload=True` | Distributed CPU offload | Slower; use FSDP/distributed recipe guidance. |
| `compile=True` | Speed/memory improvements in supported paths | Not universal; QAT paths may reject compile. |
| `dtype=bf16` | Memory/performance on supported hardware | Recipe code checks support and rejects unsupported bf16 in some paths. |
| low-bit optimizer | Single-device low-memory optimizer | Optional packages and optimizer field compatibility matter. |

## Safe Config Editing Pattern

For non-trivial edits, prefer copied YAML plus validation over long commands:

```bash
tune cp llama3_2/3B_lora ./configs/custom_3B_lora.yaml --make-parents
tune cat ./configs/custom_3B_lora.yaml
tune validate ./configs/custom_3B_lora.yaml
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_finetune_distributed ./configs/custom_3B_lora.yaml \
  --nproc-per-node 4 \
  --override max_steps_per_epoch=20 \
  --override output_dir='./runs/custom_3B_lora'
```

Ask the user before executing the printed command.
