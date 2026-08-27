# Config Catalog

OpenCompass ships many Python config files under its installed `opencompass.configs` package. Agents should discover and compare these configs before authoring custom variants.

## Naming Conventions

Dataset config files are organized as flattened dataset directories, commonly with names like:

```text
<dataset>/<dataset>_<method>.py
<dataset>/<dataset>_<method>_<prompt_hash>.py
```

Examples:

```text
mmlu/mmlu_gen.py
mmlu/mmlu_ppl_ac766d.py
gsm8k/gsm8k_gen.py
gpqa/gpqa_0shot_nocot_genericllmeval_gen_772ea0.py
```

Interpretation:

- `gen`: generation-based evaluation using `GenInferencer`.
- `ppl`: perplexity/choice scoring using `PPLInferencer`.
- `llmjudge`, `genericllmeval`, `cascade`: evaluator or workflow variants that may need judge-model configuration.
- Files without a hash suffix usually point to a latest/default prompt variant for that method.
- Hash suffixes identify prompt/config versions; do not remove them when reproducing a specific benchmark.

Model config files are grouped by backend/model family and usually export `models`.

## List Built-In Configs

Use the bundled script to discover installed configs without relying on the original repository `tools/` directory:

```bash
python scripts/list_opencompass_configs.py mmlu --kind datasets
python scripts/list_opencompass_configs.py internlm --kind models
python scripts/list_opencompass_configs.py mmlu gsm8k --kind all --format table
```

The script attempts to use `opencompass.utils.match_files` when available. If that import is unavailable, it falls back to package-file discovery via `importlib`.

Useful options:

```bash
python scripts/list_opencompass_configs.py --help
python scripts/list_opencompass_configs.py '*judge*' --kind datasets --format json
python scripts/list_opencompass_configs.py gsm8k --exact --kind datasets
```

## Import Built-In Configs

After selecting configs, import them inside `read_base`:

```python
from mmengine.config import read_base

with read_base():
    from opencompass.configs.datasets.mmlu.mmlu_gen import mmlu_datasets
    from opencompass.configs.datasets.gsm8k.gsm8k_gen import gsm8k_datasets
    from opencompass.configs.models.hf_internlm.hf_internlm2_chat_7b import models as model_cfgs

datasets = [*mmlu_datasets, *gsm8k_datasets]
models = [*model_cfgs]
```

If a dataset module does not export the variable name you expected, inspect the module or use static comparison on candidate files. Dataset variables are usually named `<dataset>_datasets`, but there are exceptions such as modules that export `datasets` directly or aliases for subsets.

## Compare Two Configs Before Running

Use `compare_config_keys.py` when evaluating a config edit, prompt-version swap, or generated config:

```bash
python scripts/compare_config_keys.py baseline.py candidate.py
python scripts/compare_config_keys.py baseline.py candidate.py --show datasets,models
python scripts/compare_config_keys.py baseline.py candidate.py --json
```

The script statically parses Python AST and reports:

- top-level assigned names added/removed in each file;
- imported modules and imported names added/removed;
- dataset summaries from literal dicts assigned to `datasets` or `<name>_datasets`;
- model summaries from literal dicts assigned to `models` or `<name>_models`;
- reader/evaluator key differences when visible as literals.

This does not execute config imports, so it is safer than importing a config that may require optional model backends. Static parsing cannot fully resolve dynamic list construction or imported variables; treat unresolved summaries as a cue to run `opencompass --dry-run` in a proper environment.

## Detect Changed Dataset Abbreviations

Dataset abbreviations drive result keys. Before reusing outputs or comparing result tables, check for changed `abbr` values:

```bash
python scripts/compare_config_keys.py old_eval.py new_eval.py --show datasets
```

Example output to watch for:

```text
Dataset abbrs only in old_eval.py: ['mmlu']
Dataset abbrs only in new_eval.py: ['mmlu-pro']
```

If a dataset entry omits `abbr`, OpenCompass may derive an abbreviation from the dataset config. Prefer explicit `abbr` in custom local configs to make comparisons stable.

## Safe Catalog Workflow

1. Search for candidate dataset configs by dataset family and method.
2. Prefer non-hash default files for latest behavior unless reproducing a paper/config version.
3. Inspect whether the candidate uses `GenInferencer`, `PPLInferencer`, or an LLM judge evaluator.
4. Import selected configs under `read_base` and alias conflicting `models`/`datasets` variable names.
5. Run static comparison against a baseline if editing an existing config.
6. Run `opencompass config.py --dry-run --debug` in an OpenCompass environment before real inference.

## When Discovery Fails

- If `opencompass` imports but no configs are found, the installed wheel may omit package data; use a source checkout or install that includes `opencompass/configs`.
- If `opencompass.utils.match_files` fails because optional dependencies are missing, use `scripts/list_opencompass_configs.py`, which has a package-file fallback.
- If a fuzzy query returns too many files, add method tokens such as `gen`, `ppl`, `llmjudge`, or exact dataset family names.
