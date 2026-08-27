---
name: data-and-configs
description: "Author and statically validate pytorch-semseg YAML configs, choose
  dataset loaders, and troubleshoot dataset layouts and split/path errors before
  training or validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-and-configs

Use this sub-skill when a task is about preparing a pytorch-semseg YAML config, selecting a dataset loader, checking dataset paths/splits, or diagnosing config/data errors before training or validation.

Do not run training, validation, or single-image inference from this sub-skill.

## Quick workflow

1. Identify the target dataset key and split names from [references/configuration.md](references/configuration.md).
2. Check that the dataset directory layout matches [references/data-formats.md](references/data-formats.md).
3. Draft or update the YAML config with `model`, `data`, and `training` sections.
4. Run the bundled static checker before handing the config to a training or validation workflow:

   ```bash
   python scripts/validate_config.py --config CONFIG.yml --print-summary
   python scripts/validate_config.py --config CONFIG.yml --strict-paths --print-summary
   ```

   The checker uses `yaml.safe_load`, does not import pytorch-semseg, does not instantiate loaders, and does not read image or mask data.

## Scope and routing

- Config schema, dataset registry keys, split names, data layouts, `img_rows`/`img_cols`, augmentations, loss/optimizer/scheduler key checks, and legacy key drift: stay here.
- Model constructor internals, architecture-specific parameters, registry smoke tests, or pretrained-weight side effects: route to `model-zoo-and-apis`.
- Building or running `train.py`/`validate.py` commands, checkpoint resume behavior during execution, and metric interpretation: route to `training-and-evaluation`.
- `test.py` single-image command construction, image checkpoint naming, output mask writing, and DenseCRF: route to `single-image-inference`.

## Runtime files

- [references/configuration.md](references/configuration.md): config schema, registry tables, safe YAML snippets, and legacy drift warnings.
- [references/data-formats.md](references/data-formats.md): expected dataset root layouts and split conventions by loader.
- [references/troubleshooting.md](references/troubleshooting.md): common symptoms, causes, and fixes for config/data failures.
- [scripts/validate_config.py](scripts/validate_config.py): static YAML validator with optional path-layout checks.

## Safety notes

- Treat source example configs as evidence, not as drop-in templates: replace machine-specific paths, set `resume: null` when starting fresh, and validate registry keys.
- Keep `img_rows` and `img_cols` numeric unless the selected loader explicitly supports the string pair `same`.
- Prefer `yaml.safe_load` in any adapted script; the original entry points used legacy `yaml.load(fp)` style that fails on modern PyYAML unless a loader is supplied.
