# CLI Reference

## Console entry point

The package exposes a `trl` console command. Running `trl` with no subcommand prints help and exits successfully. The registered commands are:

| Command | Purpose |
| --- | --- |
| `trl sft` | Launch the SFT training script. |
| `trl dpo` | Launch the DPO training script. |
| `trl grpo` | Launch the GRPO training script. |
| `trl reward` | Launch reward model training. |
| `trl rloo` | Launch RLOO training. |
| `trl kto` | Launch KTO training. |
| `trl env` | Print TRL and dependency environment information. |
| `trl skills` | List, install, or uninstall bundled TRL agent skills. |
| `trl vllm-serve` | Start the vLLM serving script used by online generation workflows. |

Training commands register without argparse's default top-level help on the subparser, but each script parser supports help:

```bash
trl sft --help
trl dpo --help
trl grpo --help
trl vllm-serve --help
```

## Training command shape

Training commands use the same high-level shape:

```bash
trl <method> --model_name_or_path <model> --dataset_name <dataset> --output_dir <out> [script/trainer/model flags] [accelerate launch flags]
```

The CLI imports the matching `trl/scripts/<method>.py` parser and then launches that script through `accelerate launch`. Remaining arguments understood by Accelerate are separated from script/trainer arguments and passed to the accelerate launcher. Common direct accelerate flags such as `--num_processes` can be placed in the same command.

Minimal examples:

```bash
trl sft --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name stanfordnlp/imdb --output_dir runs/sft
trl dpo --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name anthropic/hh-rlhf --output_dir runs/dpo
trl reward --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name trl-lib/ultrafeedback_binarized --output_dir runs/reward
trl grpo --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name HuggingFaceH4/Polaris-Dataset-53K --reward_funcs accuracy_reward --output_dir runs/grpo
trl rloo --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name HuggingFaceH4/Polaris-Dataset-53K --reward_funcs accuracy_reward --output_dir runs/rloo
trl kto --model_name_or_path Qwen/Qwen2.5-0.5B --dataset_name trl-lib/kto-mix-14k --output_dir runs/kto
```

## Dataclass-backed flags

Script parsers are built from dataclasses:

- `ScriptArguments` or a method-specific subclass: dataset loading flags such as `dataset_name`, `dataset_config`, `dataset_train_split`, `dataset_test_split`, `dataset_streaming`, and `ignore_bias_buffers`.
- Method config such as `SFTConfig`, `DPOConfig`, `GRPOConfig`, `RewardConfig`, `RLOOConfig`, or experimental `KTOConfig`: trainer and training-argument fields, including many standard `TrainingArguments` fields.
- `ModelConfig`: model loading fields such as `model_name_or_path` and related model/tokenizer/PEFT/quantization settings.
- `DatasetMixtureConfig`: YAML-oriented `datasets`, `streaming`, and `test_split_size` fields for dataset mixtures.

For each dataclass field, the parser accepts underscore and hyphen spellings when the field contains underscores. For example, `--model_name_or_path` and `--model-name-or-path` target the same destination.

List-typed flags consume one or more following values:

```bash
trl dpo --loss_type sigmoid bco_pair --loss_weights 1.0 0.5 ...
trl grpo --reward_funcs accuracy_reward format_reward ...
```

Boolean flags use explicit string parsing. Accepted values are `yes/no`, `true/false`, `t/f`, `y/n`, and `1/0`, case-insensitive. For booleans with a default of `True`, the parser also creates `--no_<field>` and `--no-<field>` complements.

Optional non-string fields can use `none` or `null` to pass Python `None`.

## `--config` YAML launch

Every training command and `trl vllm-serve` support YAML configs through `--config`:

```bash
trl sft --config sft_config.yaml
trl dpo --config dpo_config.yaml --learning_rate 5e-7
trl vllm-serve --config serve_config.yaml
```

The parser loads YAML, applies matching keys as parser defaults, then parses the remaining CLI flags. CLI flags override YAML values.

See `configuration.md` for full YAML examples, dataset mixtures, and `env:` behavior.

## Accelerate arguments

Training commands launch through `accelerate launch`, so accelerate-launch arguments may be included in the `trl` command or YAML config. Common examples:

```bash
trl sft --config sft.yaml --num_processes 4
trl dpo --config dpo.yaml --mixed_precision bf16 --num_machines 1
```

TRL also supports a convenience argument:

```bash
trl sft --config sft.yaml --accelerate_config single_gpu
trl sft --config sft.yaml --accelerate_config path/to/accelerate.yaml
```

`--accelerate_config <value>` is rewritten to Accelerate's `--config_file <path>`. The value may be a file path or the basename of a predefined TRL accelerate config bundled with the package. If it is neither, the command raises a clear config-not-found error.

Route questions about what a DeepSpeed/FSDP/parallelism setting means to the scaling-and-backends sub-skill.

## `trl env`

Use `trl env` to print TRL environment information. This is safe and does not launch training:

```bash
trl env
```

It is useful for bug reports and confirming package/dependency versions, but public skill content should not ask agents to paste machine-specific paths into reusable docs.

## `trl skills`

`trl skills` manages bundled TRL agent skills. With no skills subcommand, it prints help.

```bash
trl skills list
trl skills list --target agents
trl skills install trl-training
trl skills install --all --target claude --scope project
trl skills install trl-training --target claude --scope global --force
trl skills uninstall trl-training --target claude
```

Important parser facts:

- `install` defaults `--target` to `agents` and `--scope` to `project`.
- `--scope` accepts `project` or `global`.
- `install` requires either a skill name or `--all`, but not both.
- `--force` overwrites an already installed skill.
- `list` can be run without `--target` to show TRL skills available for installation.

## `trl vllm-serve`

`trl vllm-serve` parses its own `ScriptArguments` dataclass and can load required fields from `--config`. For example, a YAML file containing `model: <model-id>` satisfies the required model field.

```yaml
model: Qwen/Qwen2.5-0.5B
```

```bash
trl vllm-serve --config serve.yaml
```

Route backend capacity, serving topology, GPU memory, or vLLM runtime behavior to scaling-and-backends. Use this sub-skill only for command/config syntax.
