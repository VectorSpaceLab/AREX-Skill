# Evaluation

This reference covers the evaluation CLI surfaces and the files they read and write.

## What the evaluation commands consume

The policy-based evaluation workflow uses an eval config directory made of YAML or JSON files with top-level keys such as:

- `policies`
- `interactions`
- `models`
- `prompts`
- `expected_latencies`

The files are merged by top-level key. File names are flexible; the top-level keys are what matter.

An interaction set can use either plain text inputs or message-style inputs. Expected outputs can be `generic`, `refusal`, or `similar_message`.

## CLI hierarchy

```text
nemoguardrails eval
├── run
├── check-compliance
├── ui
└── rail
    ├── topical
    ├── moderation
    ├── hallucination
    └── fact-checking
```

> The command name is `fact-checking`; the underlying implementation is named `fact_checking`.

### `eval run`

Runs the interactions from an eval config through a guardrail config.

- Inputs:
  - `--eval-config-path` / `-e`
  - `--guardrail-config-path` / `-g`
  - optional `--output-path`
  - optional `--output-format` (`json` or `yaml`)
  - optional `--parallel`
- Outputs:
  - a result directory containing `results.(json|yaml)` and `logs.(json|yaml)`
  - the default output directory is derived from the guardrail config folder name when `--output-path` is omitted
- Notes:
  - `run` calls the configured guardrail model; it is not offline by default.
  - The output files store the same `EvalOutput` structure used by the UI: a `results` list and a `logs` list.
  - Re-running can reuse prior results when the interaction input is unchanged.

### `eval check-compliance`

Adds LLM-as-a-judge compliance checks to one or more evaluation result directories.

- Inputs:
  - required `--llm-judge`
  - optional `--eval-config-path` / `-e`
  - optional `--output-path` / `-o` one or more directories
  - optional `--policy-ids` / `-p`
  - optional `--verbose`, `--force`, `--reset`, `--parallel`
  - optional `--disable-llm-cache`
- Outputs:
  - writes compliance checks back into the same output directories
  - if `--output-path` is omitted, the CLI auto-discovers output folders in the current directory, excluding `config`
- Judge caveats:
  - the judge model must be declared in the eval config as an `llm-judge` model
  - the judge prompt must return exactly two lines: `Reason:` and `Compliance:`
  - invalid judge responses are ignored
  - `Compliance: n/a` is only acceptable for non-targeted policies
- Cache caveats:
  - caching is on by default when the LangChain cache dependency is available
  - `--disable-llm-cache` bypasses it
  - if LangChain cache support is missing, caching is unavailable

### `eval ui`

Launches the Streamlit review app for the evaluation outputs.

- Inputs:
  - optional `--eval-config-path`
  - optional `--output-path`
- Outputs:
  - a Streamlit UI for review and analysis
  - the UI can write reviewed results, logs, and latency annotations back to the same files
- Notes:
  - if output paths are omitted, the CLI discovers folders in the current directory, excluding `config`
  - this command needs the Streamlit dependency

### `eval rail topical`

Evaluates topical rails for canonical-form detection, next-step generation, and bot message generation.

- Inputs:
  - `--config`
  - optional `--verbose`
  - optional `--test-percentage`
  - optional `--max-tests-intent`
  - optional `--max-samples-intent`
  - optional `--results-frequency`
  - optional `--sim-threshold`
  - optional `--random-seed`
  - optional `--output-dir`
- Outputs:
  - one JSON file in the output directory containing prediction rows
  - the exact filename is derived from the config path, main model, shot count, and similarity threshold
- Notes:
  - only one guardrail config is supported
  - the command uses the configured guardrail model and can call a live provider
  - `--sim-threshold > 0` requires sentence-transformers for semantic intent matching

### `eval rail moderation`

Evaluates jailbreak detection and output moderation.

- Inputs:
  - `--config`
  - optional `--dataset-path`
  - optional `--num-samples`
  - optional `--check-input` / `--no-check-input`
  - optional `--check-output` / `--no-check-output`
  - optional `--output-dir`
  - optional `--write-outputs` / `--no-write-outputs`
  - optional `--split` (`harmful` or `helpful`)
- Outputs:
  - a JSON file named from the dataset and split, ending in `_moderation_results.json`
- Notes:
  - the command uses the configured guardrail model and can call a live provider
  - output moderation is harder to judge automatically; manual review is still recommended

### `eval rail hallucination`

Evaluates hallucination rails.

- Inputs:
  - `--config`
  - optional `--dataset-path`
  - optional `--num-samples`
  - optional `--output-dir`
  - optional `--write-outputs` / `--no-write-outputs`
- Outputs:
  - a JSON file named from the dataset, ending in `_hallucination_predictions.json`
- Notes:
  - the command uses the configured guardrail model and can call a live provider
  - the scoring loop is only a heuristic; inspect the predictions manually

### `eval rail fact-checking`

Evaluates fact-checking rails.

- Inputs:
  - `--config`
  - optional `--dataset-path`
  - optional `--num-samples`
  - optional `--create-negatives` / `--no-create-negatives`
  - optional `--output-dir`
  - optional `--write-outputs` / `--no-write-outputs`
- Outputs:
  - a positive JSON file and a negative JSON file, both named from the dataset
- Notes:
  - the command can synthesize incorrect answers before scoring
  - the command uses the configured guardrail model and can call a live provider

## Live-model boundary

The `eval run` and `eval rail` commands call the configured guardrail model. The compliance checker also calls the judge model defined in the eval config.

If you need an offline path, use a fake or deterministic model config, recorded fixtures, or repository tests that mock the provider calls. Do not assume the CLI is offline-safe just because the package has unit tests.

## Result interpretation

- `results` holds the interaction outputs and per-policy compliance state.
- `logs` holds the interaction trace, activated rails, and compliance-check details.
- `check-compliance` can append multiple compliance checks to the same interaction.
- The UI and compliance checker may update the same files in place, so keep result folders under version control only when that is intentional.
