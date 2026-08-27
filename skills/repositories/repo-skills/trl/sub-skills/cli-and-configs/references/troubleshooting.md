# CLI and Config Troubleshooting

## Unknown CLI arguments

Typical error:

```text
Some specified arguments are not used by the HfArgumentParser: [...]
```

Checklist:

1. Confirm the flag belongs after the subcommand: use `trl sft --flag value`, not `trl --flag value sft`.
2. Confirm the flag exists for that method by checking `trl <method> --help`.
3. Try underscore and hyphen spellings for dataclass fields: `--model_name_or_path` and `--model-name-or-path` are both generated for `model_name_or_path`.
4. For list fields, put all values after the same flag: `--loss_type sigmoid bco_pair`, not repeated shell fragments unless help says repeated flags are accepted.
5. If the unknown argument is really an accelerate-launch option, make sure it appears in the `trl <method>` command or YAML so the training command can forward it to Accelerate.

Do not invent parser keys. If a Python trainer recipe uses custom Python objects, callbacks, callables, or dataset transforms, those may not have CLI equivalents.

## Unknown YAML config keys

Typical error:

```text
Unknown arguments from config file: ['--this_arg_does_not_exist', 'value'].
```

The YAML loader applies keys as parser defaults. Keys that do not match any known parser action are converted into remaining strings and fail by default.

Fixes:

- Rename the YAML key to the dataclass field name, usually the underscore form: `model_name_or_path`, `dataset_train_split`, `per_device_train_batch_size`.
- Remove comments or nested maps accidentally placed at the wrong level.
- Move accelerate config-file contents into an accelerate config file and reference it with `--accelerate_config`, unless the key is an actual accelerate-launch argument accepted by the command.
- Keep method-specific keys with the method that supports them; for example, reward-function flags are expected for GRPO/RLOO-style commands, not every trainer.

## Boolean flag spelling

Boolean fields parse explicit truthy/falsy strings:

```bash
trl sft --bf16 true --dataset_streaming false
trl sft --bf16 1 --dataset_streaming 0
```

Accepted strings are `yes/no`, `true/false`, `t/f`, `y/n`, and `1/0`, case-insensitive.

For boolean fields whose default is `True`, the parser also creates `--no_<field>` and `--no-<field>` complement flags. Use the complement only when help shows the default-enabled field exists for the command.

Common mistake:

```bash
trl sft --dataset_streaming maybe
```

This fails because `maybe` is not a valid boolean string.

## Config precedence surprises

Precedence order:

1. Dataclass defaults.
2. Values loaded from `--config` YAML.
3. CLI flags after config parsing.

So this command uses the YAML for everything except `learning_rate`:

```bash
trl sft --config sft.yaml --learning_rate 5e-5
```

If a value appears unchanged, check for shell quoting, repeated flags, or whether the field belongs to the selected command.

## `dataset_name` versus `datasets` mixture

`dataset_name` is the single-dataset shortcut. `datasets` is the dataset-mixture configuration. The dataset utility documents that when `datasets` is provided, single-dataset fields such as `dataset_name`, `dataset_config`, `dataset_train_split`, `dataset_test_split`, and `dataset_streaming` are ignored.

Problematic YAML:

```yaml
dataset_name: stanfordnlp/imdb
datasets:
  - path: trl-internal-testing/zen
    name: standard_language_modeling
```

Fix by choosing one style:

```yaml
dataset_name: stanfordnlp/imdb
```

or:

```yaml
datasets:
  - path: trl-internal-testing/zen
    name: standard_language_modeling
```

Route questions about required columns or whether a dataset is suitable for SFT/DPO/GRPO to data-and-rewards.

## Missing required fields

Training commands generally need at least a model, dataset input, and an output directory for a real training run. Parser or trainer errors often mention one of these:

- `model_name_or_path`: model identifier or path for training commands.
- `model`: required by `trl vllm-serve`.
- `output_dir`: required by training-argument configs in practical runs.
- `dataset_name` or `datasets`: dataset source.

Examples:

```yaml
model_name_or_path: Qwen/Qwen2.5-0.5B
dataset_name: stanfordnlp/imdb
output_dir: runs/sft
report_to: none
```

For `vllm-serve`, a config file can satisfy the required model field:

```yaml
model: Qwen/Qwen2.5-0.5B
```

```bash
trl vllm-serve --config serve.yaml
```

## Misplaced subcommand arguments

The top-level CLI parses only the subcommand name before dispatch. Put method arguments after the method:

Correct:

```bash
trl sft --config sft.yaml --num_processes 4
```

Incorrect:

```bash
trl --config sft.yaml sft --num_processes 4
```

For help, use:

```bash
trl --help
trl sft --help
trl skills --help
```

## Accelerate config errors

`--accelerate_config` must be followed by a value. The value must be a filesystem path or a predefined TRL accelerate config name bundled with the package.

Common failures:

```text
Expected a value after `--accelerate_config`.
Accelerate config X is neither a file nor a valid config in the `trl` package.
```

Fixes:

```bash
trl sft --config sft.yaml --accelerate_config single_gpu
trl sft --config sft.yaml --accelerate_config path/to/accelerate.yaml
```

If the question is about choosing DeepSpeed ZeRO stage, FSDP version, CP/SP/TP/DP sizes, vLLM memory, or hardware topology, route to scaling-and-backends.

## Command-specific warnings

- `trl kto` imports `KTOTrainer` and `KTOConfig` from TRL's experimental KTO namespace. Treat experimental API churn as expected; keep syntax examples conservative and verify with `trl kto --help`.
- GRPO and RLOO examples often include `reward_funcs`, `num_generations`, and `max_completion_length`. If a user asks what the reward function computes or how generations affect optimization, route to core-training or data-and-rewards.
- `trl vllm-serve` command/config syntax belongs here, but runtime serving failures, port/process orchestration, and backend compatibility belong to scaling-and-backends.

## `trl skills` errors

Common messages and fixes:

| Message | Fix |
| --- | --- |
| `Either provide a skill name or use --all` | Run `trl skills install trl-training` or `trl skills install --all`. |
| `Cannot specify both` | Do not combine a skill name with `--all`. |
| `Use --force to overwrite` | Add `--force` only when replacing an existing installed skill is intended. |
| Invalid scope | Use `--scope project` or `--scope global`. |

Use `trl skills list` to see bundled TRL skills available for installation and `trl skills list --target <target>` to list installed skills in a target.
