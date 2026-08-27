---
name: yi-val
description: "Operate YiVal prompt/model evaluation workflows, including YAML
  configs, CLI runs, data readers, prompt generators, evaluators, AHP selection,
  enhancers, and custom components."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: YiVal/YiVal
  package: yival
  version-baseline: "0.0.0 at 22a1fa0"
license: Apache 2.0
---

# YiVal operating skill

Use this skill when the task involves **YiVal** or the Python package **`yival`**: building or validating experiment YAML, running prompt/model comparisons, evaluating LLM outputs, selecting the best variation, enhancing prompts, or extending YiVal with custom readers/wrappers/evaluators/generators.

YiVal's core flow is:

1. produce input examples from a dataset, user input, or a data generator;
2. create combinations from wrapper variations and variation generators;
3. call a user `custom_function(..., state=ExperimentState)`;
4. evaluate outputs with individual, comparison, or all-results evaluators;
5. optionally select a best combination, enhance prompts, display results, or open the bot/UI.

## First checks

- Install or activate a Python environment with `yival` importable. The package supports Python `>=3.10,<3.13`.
- If using a checkout, install with `python -m pip install -e .`; for trainer workflows add `python -m pip install -e '.[trainers]'` only when local fine-tuning is explicitly needed.
- If root CLI import fails with `ModuleNotFoundError: pkg_resources`, install a compatible setuptools that still exposes the import: `python -m pip install 'setuptools<81'`.
- Run the bundled smoke check from this skill root: `python scripts/check_install.py --check-cli`.
- For a no-network mini experiment fixture, run: `python scripts/write_minimal_experiment.py --run`.

## Route map

| User intent | Read |
| --- | --- |
| Install YiVal, inspect CLI commands, initialize or validate YAML, choose dataset source fields | [setup](sub-skills/setup/SKILL.md) |
| Run `yival run`, `yival demo`, Dash/interactive/bot workflows, `ExperimentRunner`, `LiteExperimentRunner`, outputs | [run](sub-skills/run/SKILL.md) |
| Generate synthetic examples or prompt variations with OpenAI/document/chain-of-density/self-exemplar generators | [prompt-automation](sub-skills/prompt-automation/SKILL.md) |
| Configure evaluators, AHP selection, human ratings, OpenAI/Alpaca/BERTScore/ROUGE/Python validation, prompt enhancers | [evaluation-optimization](sub-skills/evaluation-optimization/SKILL.md) |
| Implement custom readers, wrappers, evaluators, data generators, variation generators, enhancers, selection strategies, or output parsers | [custom-components](sub-skills/custom-components/SKILL.md) |

Shared repo references:

- [Workflow map](references/workflow-map.md): YiVal architecture, execution stages, and cross-sub-skill responsibilities.
- [Registry overview](references/registry-overview.md): built-in component ids, registration behavior, and config keys.
- [Troubleshooting](references/troubleshooting.md): install, CLI, config, provider, UI, and safety failures.
- [Repo provenance](references/repo-provenance.md): source baseline and coverage limits.

## Common fast paths

### Create and validate a config

1. Read [setup](sub-skills/setup/SKILL.md).
2. Generate a template with either `yival init ...` or `python sub-skills/setup/scripts/build_config_template.py ...`.
3. Fill in `dataset`, `custom_function`, `variations`, and `evaluators`.
4. Validate with `yival validate config.yml` or `python - <<'PY'` using `load_and_validate_config`.

### Run a dataset-backed prompt comparison

1. Read [run](sub-skills/run/SKILL.md) for the execution model.
2. Use `dataset.source_type: dataset`, `reader: csv_reader`, and a CSV with columns matching the custom function arguments.
3. Wrap tunable prompt strings in `StringWrapper(name=<variation name>, state=state)`.
4. Run `yival run config.yml --output_path results.pkl` and inspect the generated `<stem>_0.pkl` or UI.

### Build automated prompt-generation and evaluation

1. Read [prompt-automation](sub-skills/prompt-automation/SKILL.md) for `openai_prompt_data_generator`, `document_data_generator`, and prompt variation generators.
2. Read [evaluation-optimization](sub-skills/evaluation-optimization/SKILL.md) for evaluators, AHP criteria names, and enhancers.
3. Keep provider-token requirements explicit; built-in OpenAI/Replicate/Alpaca workflows can bill or call network services.

### Extend YiVal with a custom component

1. Read [custom-components](sub-skills/custom-components/SKILL.md).
2. Implement the correct base class and config dataclass.
3. Add the corresponding `custom_*` block to YAML.
4. Run the root smoke script and a tiny local experiment before running provider-backed experiments.

## Scope and safety boundaries

- This skill covers core YiVal experiment setup, runtime, generation, evaluation, selection, enhancement, and custom-component workflows.
- Fine-tuning modules are present in YiVal but are optional and heavier. Treat local SFT, OpenAI fine-tuning jobs, and Replicate fine-tuning as out-of-scope unless the user explicitly requests training and approves required extras, credentials, cost, model downloads, and GPU/runtime needs.
- `python_validation_evaluator` executes model-produced Python with `exec`. Use only with sandboxed, trusted, tiny code snippets; never run untrusted code in a production or credentialed environment.
- OpenAI, Replicate, AlpacaEval, Hugging Face dataset URLs, Google Drive document loading, Streamlit/Dash/ngrok, and some demos require network access, credentials, or public services. Prefer the offline smoke fixture before provider-backed runs.

## Expected artifacts and outputs

- CLI runs can display Dash results, write pickled experiment objects as `<output_stem>_<config_index>.pkl`, or open interactive/bot modes.
- Programmatic runs use `ExperimentRunner(config_path).run(...)` for YAML-driven workflows or `LiteExperimentRunner(...).run_experiment(enable_selector=True/False)` when the caller already holds data, evaluator, token logger, and config objects.
- Data rows become `InputData(content={...}, expected_result=...)`; custom functions should return `MultimodalOutput(text_output=..., image_output=..., video_output=...)`.

## Refresh triggers

Refresh this skill when YiVal changes CLI subcommands, config schema names, registry ids, evaluator/enhancer contracts, OpenAI SDK support, optional trainer dependencies, or result object serialization.
