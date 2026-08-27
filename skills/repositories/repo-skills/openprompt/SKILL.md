---
name: openprompt
description: "Route OpenPrompt prompt-learning, dataset/config,
  template/verbalizer, and training/generation workflows from a single repo
  skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenPrompt

Use this skill when the user asks about OpenPrompt as a package or repository: installing or importing it, loading PLMs, building prompt-learning pipelines, designing templates/verbalizers, validating YAML configs or dataset processors, or inspecting runner and generation behavior.

## Start here

- `references/package-overview.md` for the verified public surface, dependency expectations, and sub-skill map.
- `references/troubleshooting.md` for cross-cutting install/import, dependency, config-path, and backend issues.
- `references/repo-provenance.md` when checking whether this skill matches the current checkout or before refreshing it.
- `scripts/check_openprompt_install.py` for the canonical no-download import/API smoke.

## Quick install guidance

OpenPrompt 1.0.1 is a Python package built around PyTorch and Hugging Face Transformers. For a source checkout, install the runtime stack first, then install the package itself without pulling in extra build behavior:

```bash
python -m pip install torch==1.13.1+cpu transformers==4.19.0 sentencepiece==0.1.96 datasets==2.14.7 scikit-learn==1.3.2 scipy rouge==1.0.0 tensorboardX yacs dill pyyaml
python -m pip install -e . --no-deps
```

If you only need the published package, `pip install openprompt` is the simplest entry point. Use the bundled install smoke before deeper debugging.

## Route map

### `sub-skills/pipeline-basics/`
Use for the minimal pipeline surface: `InputExample`, `InputFeatures`, `PromptDataLoader`, `PromptForClassification`, `PromptForGeneration`, `PromptModel`, `load_plm`, and the top-level package exports. This is the first stop for install/import checks and no-download smoke tests.

### `sub-skills/template-verbalizer-design/`
Use for template grammar, manual/mixed/soft/prefix/P-tuning/PTR templates, verbalizers, calibration, LM-BFF prompt generation, and bundled prompt assets. Route prompt-asset validation and label-word/tokenization issues here.

### `sub-skills/data-and-config-workflows/`
Use for `DataProcessor` families, `load_dataset`, `FewShotSampler`, OpenPrompt YAMLs, `get_user_config`, `experiments/cli.py` config inspection, and dataset-layout validation. Route path and selector problems here before training.

### `sub-skills/training-and-generation/`
Use for `ClassificationRunner`, `GenerationRunner`, `LMBFFClassificationRunner`, `ProtoVerbClassificationRunner`, device placement, checkpointing, generation settings, few-shot/zero-shot behavior, and dry-run training config inspection.

## Operating notes

1. Keep this root skill short and router-like. Use the sub-skills for the concrete API details and runnable helpers.
2. Do not run heavy training, dataset downloads, or model downloads from the root skill unless the user explicitly asks for them and the relevant sub-skill says they are expected.
3. If a user request mixes prompt construction, config loading, and training behavior, start with `pipeline-basics`, then branch to `template-verbalizer-design`, `data-and-config-workflows`, or `training-and-generation` as needed.
4. Optional GPU, UltraChat/accelerate, and PaddlePaddle workflows are documented but not part of the minimum verified path for this skill.
5. When the current checkout changes, compare it with `references/repo-provenance.md` before assuming the skill is still current.

## Canonical smoke

Run the bundled smoke from the root skill directory:

```bash
python scripts/check_openprompt_install.py
```

It proves the package import path, key signatures, and a tiny fake-wrapper `PromptDataLoader` path without needing datasets or model downloads.
