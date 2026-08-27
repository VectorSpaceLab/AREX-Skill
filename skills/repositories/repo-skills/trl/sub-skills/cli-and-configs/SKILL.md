---
name: cli-and-configs
description: "Build and debug TRL CLI commands, YAML configs, dataset mixture
  configs, accelerate-launch argument patterns, env configs, and bundled TRL
  skills commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TRL CLI and Configs

Use this sub-skill when a task is about invoking `trl`, constructing reproducible CLI/YAML configurations, translating Python trainer arguments into CLI flags, or debugging parser/config errors.

## Use this for

- Choosing top-level commands: `trl sft`, `trl dpo`, `trl grpo`, `trl reward`, `trl rloo`, `trl kto`, `trl env`, `trl skills`, and `trl vllm-serve`.
- Building safe command lines or YAML files from model, dataset, training, and accelerate-launch arguments.
- Explaining `--config` YAML behavior, `env:` sections, CLI-overrides-config precedence, and dataset mixture syntax.
- Debugging unknown arguments, boolean flag spelling, required `output_dir` or `model_name_or_path`/`model` errors, and misplaced subcommand arguments.
- Using `trl skills list/install/uninstall` command syntax.

## Route away

- Trainer objectives, loss semantics, reward modeling behavior, and algorithm-specific hyperparameter meaning belong in `../core-training/SKILL.md`.
- Distributed strategy meaning, vLLM server architecture, DeepSpeed/FSDP tradeoffs, and backend troubleshooting belong in `../scaling-and-backends/SKILL.md`.
- Dataset column schemas, reward function contracts, chat template formatting, and data preprocessing semantics belong in `../data-and-rewards/SKILL.md`.

## Fast workflow

1. Identify the command family and whether the user wants a shell command, a YAML file, or both.
2. Put `trl <subcommand>` first; training subcommands accept script/trainer/model/dataset fields and also pass remaining accelerate-launch flags through `accelerate launch`.
3. Prefer YAML for reproducibility when there are more than a few flags, environment variables, or dataset mixtures.
4. Use CLI flags after `--config path.yaml` only for intentional overrides; command-line values win over YAML defaults.
5. For safe template generation, run `python scripts/build_trl_command.py --help` from this sub-skill directory, or copy the helper into a scratch location and render templates without launching training.

## References

- `references/cli-reference.md` covers commands, parser behavior, common flags, `trl env`, `trl skills`, and `trl vllm-serve`.
- `references/configuration.md` covers YAML config files, dataset mixtures, environment variables, accelerate config patterns, and conversion from Python recipes.
- `references/troubleshooting.md` covers parser errors, bool spelling, config precedence, dataset conflict handling, and command-specific warnings.
- `scripts/build_trl_command.py` renders shell/YAML templates for `sft`, `dpo`, `grpo`, `reward`, `rloo`, and `kto`; it does not import TRL or start training.
