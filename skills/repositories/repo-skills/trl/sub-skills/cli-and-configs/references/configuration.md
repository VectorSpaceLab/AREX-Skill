# Configuration Reference

## Prefer YAML for reproducible runs

TRL training commands can take the same dataclass-backed fields from CLI flags or YAML. YAML is better when a run has many arguments, environment variables, dataset mixtures, or accelerate launch settings.

Basic SFT YAML:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: stanfordnlp/imdb
output_dir: runs/sft-imdb
report_to: none
learning_rate: 0.0001
lr_scheduler_type: cosine
```

Launch:

```bash
trl sft --config sft.yaml
```

For one-off changes, put overrides after the config:

```bash
trl sft --config sft.yaml --learning_rate 5e-5 --output_dir runs/sft-debug
```

Command-line flags override YAML defaults. Unknown YAML keys are reported as unknown config arguments unless the caller explicitly disables that check in code.

## YAML `env:` section

A YAML config may set environment variables with an `env:` mapping. Values are converted to strings before being written to the process environment.

```yaml
env:
  CUDA_VISIBLE_DEVICES: 0
  WANDB_DISABLED: true
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: stanfordnlp/imdb
output_dir: runs/sft
report_to: none
```

`env:` must be a mapping. A scalar or list under `env` raises:

```text
`env` field should be a dict in the YAML file.
```

Do not put local machine paths, private tokens, or API keys into reusable skill examples.

## Common training keys

The exact accepted fields depend on the subcommand's parser, but these fields are common patterns:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
output_dir: runs/example
report_to: none
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 0.00001
num_train_epochs: 1
max_steps: 100
save_strategy: steps
save_steps: 50
logging_steps: 10
bf16: true
```

Dataset shortcuts from `ScriptArguments`:

```yaml
dataset_name: trl-internal-testing/zen
dataset_config: standard_language_modeling
dataset_train_split: train
dataset_test_split: test
dataset_streaming: false
```

Use `dataset_name` for a single dataset. Use `datasets` for mixtures and avoid setting both unless you intentionally rely on the mixture taking precedence.

## Dataset mixture YAML

`DatasetMixtureConfig` supports YAML-only-style nested dataset entries. Each entry mirrors `datasets.load_dataset` parameters plus optional column filtering:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
output_dir: runs/sft-mixture
report_to: none
datasets:
  - path: trl-internal-testing/zen
    name: standard_prompt_only
    split: train
  - path: trl-internal-testing/zen
    name: standard_preference
    split: train
    columns:
      - prompt
streaming: false
test_split_size: 0.1
```

Dataset entry keys:

| Key | Meaning |
| --- | --- |
| `path` | Required dataset path or name. |
| `name` | Optional dataset configuration name. |
| `data_dir` | Optional dataset data directory. |
| `data_files` | Optional dataset file path, list, or mapping. |
| `split` | Dataset split; defaults to `train`. |
| `columns` | Optional list of columns to keep. |

When `datasets` is provided, `dataset_name`, `dataset_config`, `dataset_train_split`, `dataset_test_split`, and `dataset_streaming` are documented as ignored by the dataset loading utility. Route dataset schema and column compatibility questions to data-and-rewards.

## Method-specific YAML skeletons

SFT:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: stanfordnlp/imdb
output_dir: runs/sft
report_to: none
learning_rate: 0.0001
```

DPO:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: anthropic/hh-rlhf
output_dir: runs/dpo
report_to: none
loss_type:
  - sigmoid
```

Reward:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: trl-lib/ultrafeedback_binarized
output_dir: runs/reward
report_to: none
```

GRPO:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: HuggingFaceH4/Polaris-Dataset-53K
output_dir: runs/grpo
report_to: none
reward_funcs:
  - accuracy_reward
num_generations: 4
max_completion_length: 32
```

RLOO:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: HuggingFaceH4/Polaris-Dataset-53K
output_dir: runs/rloo
report_to: none
reward_funcs:
  - accuracy_reward
num_generations: 2
max_completion_length: 32
```

KTO:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: trl-lib/kto-mix-14k
output_dir: runs/kto
report_to: none
```

KTO currently imports its trainer/config from TRL's experimental namespace. Treat warning or API-stability questions as command-specific troubleshooting unless the question is about KTO algorithm semantics, which belongs in core-training.

## Accelerate patterns

Training commands pass launch arguments to Accelerate. For quick runs, include launch flags directly:

```bash
trl sft --config sft.yaml --num_processes 4 --mixed_precision bf16
```

For reusable setups, put accelerate fields into the same YAML config or pass `--accelerate_config`:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: stanfordnlp/imdb
output_dir: runs/sft-4gpu
report_to: none
num_processes: 4
mixed_precision: bf16
```

```bash
trl sft --config sft.yaml
trl sft --config sft.yaml --accelerate_config single_gpu
trl sft --config sft.yaml --accelerate_config multi_gpu
```

Distilled accelerate config families:

| Family | Typical keys | Use this sub-skill for |
| --- | --- | --- |
| Single GPU | `distributed_type: "NO"`, `num_processes: 1`, `mixed_precision: bf16` | Command placement and config-file syntax. |
| Multi GPU | `distributed_type: MULTI_GPU`, `gpu_ids: all`, `num_processes: N` | Passing config names/files and launch flags. |
| DeepSpeed | `distributed_type: DEEPSPEED`, `deepspeed_config.zero_stage` | YAML shape only; route ZeRO meaning to scaling-and-backends. |
| FSDP | `distributed_type: FSDP`, `fsdp_config.*` | YAML shape only; route FSDP behavior to scaling-and-backends. |
| Parallelism | `parallelism_config.*` | Argument names only; route CP/SP/TP/DP semantics to scaling-and-backends. |

## Converting a Python trainer recipe to CLI/YAML

When given Python code like:

```python
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    args=SFTConfig(output_dir="runs/sft", learning_rate=1e-4, report_to="none"),
    train_dataset=dataset,
)
```

Create YAML by mapping constructor/config fields into parser names:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
output_dir: runs/sft
learning_rate: 0.0001
report_to: none
```

If the Python recipe builds a dataset mixture, represent it under `datasets`:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
output_dir: runs/sft-mixture
report_to: none
datasets:
  - path: org/dataset-a
    name: prompt_completion
    split: train
    columns:
      - prompt
      - completion
  - path: org/dataset-b
    name: language_modeling
    split: train[:20%]
streaming: false
test_split_size: 0.05
```

Then launch:

```bash
trl sft --config sft_mixture.yaml
```

If a Python-only callback, custom collator, custom reward function, or pre-tokenized schema cannot be expressed as parser fields, route the semantic conversion to the appropriate sibling skill rather than inventing unsupported CLI keys.

## Safe template helper

The bundled helper renders command and YAML templates without importing TRL or launching training:

```bash
python scripts/build_trl_command.py --command sft --model Qwen/Qwen2.5-0.5B --dataset stanfordnlp/imdb --output-dir runs/sft
python scripts/build_trl_command.py --command grpo --model Qwen/Qwen2.5-0.5B --dataset HuggingFaceH4/Polaris-Dataset-53K --reward-func accuracy_reward --format yaml
python scripts/build_trl_command.py --command sft --mixture-example --format both
```
