---
name: data-and-config-workflows
description: "Operate OpenPrompt data processors, dataset layouts, few-shot
  sampling, and YAML config validation without starting training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPrompt Data And Config Workflows

Use this sub-skill when the task involves OpenPrompt dataset processors, `InputExample` payloads, `FewShotSampler`, experiment YAMLs, `get_user_config`, or safe inspection of `experiments/cli.py` configuration behavior.

## Load First

- `references/api-reference.md` for the supported `PROCESSORS` map, config APIs, and sampler contracts.
- `references/data-formats.md` before preparing or validating local dataset directories.
- `references/workflows.md` for safe config-inspection and example YAML patterns.
- `references/troubleshooting.md` when config loading, dataset names, asset paths, or split files fail.

## Operating Boundaries

This sub-skill owns:

- Selecting an OpenPrompt `DataProcessor` by `config.dataset.name` and explaining the expected dataset layout.
- Reading, merging, and validating YAML config intent at the same level of safety as `openprompt.config.get_user_config` without starting model loading, training, testing, or dataset downloads.
- Explaining `parent_config` selector patterns for `task`, `template`, `verbalizer`, `learning_setting`, and few-shot sampling branches.
- Diagnosing local paths for dataset directories and prompt assets referenced by config keys such as `dataset.path`, `manual_template.file_path`, and `manual_verbalizer.file_path`.

This sub-skill does **not** own:

- PLM loading, tokenizer wrapper smoke tests, or top-level pipeline construction; route those to `../pipeline-basics/`.
- Template/verbalizer grammar and prompt asset authoring; route those to `../template-verbalizer-design/`.
- Runner selection, checkpoint behavior, GPU execution, or actual training/generation; route those to `../training-and-generation/`.
- Running `datasets/download_*.sh` or any network download without explicit user approval.

## Safe Config Inspection

Prefer the bundled script whenever a task asks whether an OpenPrompt YAML is structurally valid or whether referenced local files are present:

```bash
python scripts/inspect_openprompt_config.py \
  --config /path/to/config.yaml \
  --base-dir /path/used-for-relative-assets \
  --check-paths
```

The script is self-contained: it embeds the OpenPrompt processor catalog and config selectors, does not import `openprompt`, does not call `experiments/cli.py`, and does not start training or download datasets.

## Default Procedure

1. Identify the config file, intended base directory for relative paths, and whether paths should be checked or only summarized.
2. Summarize `dataset.name`, `dataset.path`, `task`, `learning_setting`, `template`, `verbalizer`, PLM fields, batch sizes, and selected branches.
3. Check that `dataset.name.lower()` is in the known processor names and that known local layouts match the expected family in `references/data-formats.md`.
4. Validate selector branches: if a YAML selects `template: manual_template`, a corresponding branch should either come from OpenPrompt defaults or be supplied in the YAML; user-added prompt components should declare an appropriate `parent_config`.
5. Validate prompt asset and dataset paths only as filesystem references. Never open a model, instantiate a runner, or call `load_dataset` for a benchmark directory unless the user explicitly asks and supplies data.
6. Report any paths that appear copied from OpenPrompt examples and need replacement with project-local dataset or asset locations.
