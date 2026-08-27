# Training Workflows

This reference covers LlamaFactory v0 training entry points. The public package version represented by this skill is `0.9.6.dev0`; `llamafactory-cli` and `lmf` both route to `llamafactory.cli:main`, and v0 is the default unless `USE_V1=1` is set.

## Entry Point

- Primary command: `llamafactory-cli train path/to/config.yaml`.
- Alias: `lmf train path/to/config.yaml`.
- Direct CLI flags are accepted: `llamafactory-cli train --model_name_or_path ... --stage sft ...`.
- For YAML/JSON configs, additional arguments after the file are OmegaConf-style overrides, for example `learning_rate=5e-5 output_dir=saves/debug`.
- `llamafactory-cli train -h` or `llamafactory-cli train --help` reaches the same train argument parser.

## Core Config Skeleton

A minimal train config usually contains these groups:

```yaml
model_name_or_path: Qwen/Qwen3-4B-Instruct-2507
trust_remote_code: true

stage: sft
do_train: true
finetuning_type: lora
lora_rank: 8
lora_target: all

dataset: identity,alpaca_en_demo
template: qwen3_nothink
cutoff_len: 2048
max_samples: 1000
preprocessing_num_workers: 16

output_dir: saves/qwen3-4b/lora/sft
logging_steps: 10
save_steps: 500
plot_loss: true
overwrite_output_dir: true
save_only_model: false
report_to: none

per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 1.0e-4
num_train_epochs: 3.0
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
ddp_timeout: 180000000
resume_from_checkpoint: null
```

Use small `max_samples` or `max_steps: 1` only for smoke tests. Real training requires explicit user intent, hardware, model access, and dataset readiness.

## Stage Selection

`stage` is parsed by `FinetuningArguments` and dispatched by the train tuner.

| Stage | Purpose | Key extras | Notes |
| --- | --- | --- | --- |
| `pt` | Continued pre-training | Usually raw text/pretrain dataset | `packing` is automatically enabled by data processing for pre-training-like flows. |
| `sft` | Supervised fine-tuning | Prompt template, supervised dataset | Most examples use `finetuning_type: lora`; full SFT often pairs with DeepSpeed/FSDP. |
| `rm` | Reward model training | Preference-pair dataset | Saves reward/value-head artifacts used by PPO. |
| `ppo` | PPO RLHF | `reward_model`, optional `reward_model_type` | `reward_model` is required; LoRA reward model type requires LoRA/OFT-compatible training. |
| `dpo` | Direct preference optimization | `pref_beta`, `pref_loss`, optional ref model | `pref_loss: sigmoid` is standard DPO. |
| `kto` | KTO preference training | `pref_beta`, KTO weights | Uses KTO-labelled preference data. |

ORPO and SimPO are not separate `stage` values. Use `stage: dpo` with `pref_loss: orpo` or `pref_loss: simpo`; these turn off the separate reference-model path because `use_ref_model` is false for those losses.

## Fine-Tuning Type Choices

| `finetuning_type` | When to use | Common keys | Constraints |
| --- | --- | --- | --- |
| `lora` | Default parameter-efficient tuning | `lora_rank`, `lora_alpha`, `lora_dropout`, `lora_target`, `additional_target` | Compatible with quantized training (`quantization_bit`) and most examples. |
| `oft` | Orthogonal fine-tuning | `oft_rank`, `oft_block_size`, `oft_target` | Quantized training is allowed by the parser; LoRA-only keys do not apply. |
| `freeze` | Train selected existing modules | `freeze_trainable_layers`, `freeze_trainable_modules`, `freeze_extra_modules` | Quantized training is rejected. |
| `full` | Full-parameter tuning | Standard trainer/DeepSpeed/FSDP keys | Highest memory cost; quantized training is rejected. |

Useful LoRA details:

- `lora_target: all` means all linear modules; comma-separated module names narrow the target set.
- If `lora_alpha` is omitted, it defaults to `lora_rank * 2`.
- `additional_target` names non-LoRA modules that remain trainable and are saved with the adapter.
- `loraplus_lr_ratio`, `use_rslora`, `use_dora`, and `pissa_init` are LoRA-only.
- LoRA cannot be combined with `use_galore`, `use_apollo`, or `use_badam`.

## QLoRA and Quantized Training

QLoRA-style configs add `quantization_bit` while keeping `finetuning_type: lora` or `finetuning_type: oft`:

```yaml
quantization_bit: 4
model_name_or_path: TechxGenus/Meta-Llama-3-8B-Instruct-GPTQ
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 8
lora_target: all
```

Parser restrictions to preserve:

- Quantization is compatible only with `finetuning_type: lora` or `oft`.
- Quantized models cannot use `resize_vocab: true`.
- Quantized models cannot create a new adapter on top of an existing adapter.
- A quantized model accepts only a single adapter path; merge multiple adapters first in the export workflow.
- PiSSA initialization on a quantized model is rejected; initialize PiSSA separately before quantized use.

Do not tell users to merge adapters into a quantized model during training diagnostics; adapter merge/export belongs to `model-loading-and-export`.

## Preference Training Patterns

### DPO

```yaml
stage: dpo
do_train: true
finetuning_type: lora
pref_beta: 0.1
pref_loss: sigmoid
```

- `pref_loss` choices include `sigmoid`, `hinge`, `ipo`, `kto_pair`, `orpo`, and `simpo`.
- `dpo_label_smoothing` applies only to `pref_loss: sigmoid`.
- `pref_ftx` mixes supervised fine-tuning loss into DPO.

### ORPO / SimPO

```yaml
stage: dpo
pref_loss: orpo    # or simpo
pref_beta: 0.1
simpo_gamma: 0.5   # for SimPO
```

- These are DPO-stage loss variants, not independent stages.
- Because no separate reference model is used for `orpo` or `simpo`, remove `ref_model` unless a different loss needs it.

### PPO

```yaml
stage: ppo
do_train: true
finetuning_type: lora
reward_model: saves/qwen3-4b/lora/reward
reward_model_type: lora
ppo_buffer_size: 1
ppo_epochs: 4
ppo_target: 6.0
```

- `reward_model` is mandatory.
- `reward_model_type: api` expects a full URL.
- `reward_model_type: lora` requires compatible LoRA training; `oft` similarly requires OFT.

### RM and KTO

- RM commonly reuses preference-pair datasets such as DPO-format examples and trains a reward/value head.
- KTO uses `stage: kto`, `pref_beta`, `kto_chosen_weight`, and `kto_rejected_weight`.

## Preprocess Mode

For large datasets, use `tokenized_path` to save or load pre-tokenized data. A preprocess-oriented config keeps model/data/template/tokenization settings and points `tokenized_path` at the output cache:

```yaml
stage: sft
do_train: true
finetuning_type: lora
dataset: identity,alpaca_en_demo
template: qwen3_nothink
cutoff_len: 2048
preprocessing_num_workers: 16
tokenized_path: saves/qwen3-4b/dataset/sft
output_dir: saves/qwen3-4b/lora/sft
overwrite_output_dir: true
```

Behavior from `DataArguments`: if `tokenized_path` does not exist, LlamaFactory saves tokenized datasets there; if it exists, LlamaFactory loads from it. Keep the same `template`, `cutoff_len`, dataset selection, and tokenizer/model family between preprocessing and training.

## Safe Verification Candidates

Use these only after the full generated skill has been integrated and verification is ready:

- Parse/render a representative train YAML without importing LlamaFactory or downloading models.
- When dependencies are complete, run a tiny train smoke with `max_steps: 1`, `report_to: none`, and tiny model/data fixtures.
- For SFT trainer behavior, verify shuffling on/off with a tiny supervised dataset and a one-step trainer run.
