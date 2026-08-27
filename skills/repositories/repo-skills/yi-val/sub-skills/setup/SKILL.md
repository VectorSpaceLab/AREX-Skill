---
name: setup
description: "Install YiVal, inspect CLI commands, create/validate experiment
  YAML, and choose dataset/config fields."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# YiVal setup and configuration

Use this sub-skill when the user needs to install YiVal, inspect `yival` CLI behavior, initialize or validate YAML, choose dataset source fields, or debug early config loading before an experiment run.

## Read first

- [CLI reference](references/cli-reference.md): subcommands, flags, and defaults.
- [Config quickstart](references/config-quickstart.md): minimal YAML shapes for dataset, machine-generated, and user-input workflows.
- [Data formats](references/data-formats.md): CSV and Hugging Face reader details.
- [Setup troubleshooting](references/troubleshooting.md): setup-specific errors.

Useful bundled helper:

- `python sub-skills/setup/scripts/build_config_template.py --help` builds a starter YAML through YiVal's own config-generation utility after importing built-ins.

## Installation checklist

1. Use Python `>=3.10,<3.13`.
2. Install YiVal in the target environment:
   - from PyPI/package index: `python -m pip install yival`
   - from a source checkout: `python -m pip install -e .`
3. Install optional trainer extras only for approved fine-tuning: `python -m pip install 'yival[trainers]'` or `python -m pip install -e '.[trainers]'`.
4. If CLI import errors mention `pkg_resources`, run `python -m pip install 'setuptools<81'`.
5. Confirm the environment from the skill root: `python scripts/check_install.py --check-cli`.

## CLI setup routes

| Task | Command shape |
| --- | --- |
| Show root help | `python -m yival --help` or `yival --help` |
| Generate a template | `yival init --config_path config.yml --function my_module.my_func --source_type dataset ...` |
| Validate YAML | `yival validate config.yml` |
| Run a config | `yival run config.yml --output_path results.pkl` |
| Try packaged demos | `yival demo --qa_expected_results`, `yival demo --basic_interactive`, `yival demo --auto_prompts` |
| Interactive auto-config | `yival gen` or `yival task` |

Important defaults:

- `yival run --display` is an `action="store_true"` flag with default `True`; CLI runs normally display Dash results unless you call `ExperimentRunner.run(display=False)` programmatically.
- `yival bot` defaults to `interactive=True` and `display=False`.
- `yival demo` copies a packaged demo config into the current working directory before running it.

## YAML minimum contract

Every useful config needs:

```yaml
description: short experiment description
custom_function: module.path.function_name
dataset:
  source_type: dataset
```

Then add fields according to source type:

- `source_type: dataset`: include `file_path` and `reader`.
- `source_type: machine_generated`: include `data_generators`.
- `source_type: user_input`: normally no file path; used for interactive UI.

For prompt/model comparisons, also add `variations` and one or more `evaluators`.

## Decision points

- If rows already exist, prefer `source_type: dataset` with `csv_reader` and a small fixture first.
- If examples must be generated from a prompt or document, route to [prompt-automation](../prompt-automation/SKILL.md) before running provider-backed generation.
- If the task is mostly metric/selector design, route to [evaluation-optimization](../evaluation-optimization/SKILL.md).
- If YAML contains `custom_*` sections, route to [custom-components](../custom-components/SKILL.md) to verify class/config paths and registry keys.
- For no-network smoke tests, run the root helper `python scripts/write_minimal_experiment.py --run` from the skill root.

## Validation workflow

1. Load or generate YAML.
2. Check `custom_function` importability. For local modules, ensure the module's directory is on `PYTHONPATH` or run from a working directory where it imports directly.
3. Check dataset row keys match the custom function's parameters except `state`.
4. Check variation names match the `StringWrapper(name=...)` calls in the custom function.
5. Check evaluator/reader/generator ids exist in [registry overview](../../references/registry-overview.md).
6. Run `yival validate config.yml`; if it passes, run a tiny dataset before scaling up.

## Handoff to running

After setup is valid, read [run](../run/SKILL.md) for execution, result pickle names, Dash/interactive behavior, and programmatic runner choices.
