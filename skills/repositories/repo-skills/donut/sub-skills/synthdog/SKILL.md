---
name: synthdog
description: "Generate synthetic OCR-free document datasets with SynthDoG,
  render language-specific configs, and adapt the template for custom corpora."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SynthDoG

Use this sub-skill when a user wants to generate synthetic document samples, make OCR-free document data, swap between the English/Japanese/Korean/Chinese template configs, or adapt SynthDoG to a new corpus.

## Route first

- Read [`references/workflows.md`](references/workflows.md) for the render-then-run flow, tiny-fixture smoke, split layout, and metadata layout.
- Read [`references/configuration.md`](references/configuration.md) for the config knobs, language bundle mapping, and custom-corpus adaptation.
- Read [`references/resource-layout.md`](references/resource-layout.md) for the background/paper/corpus/font directory contract and the asset bundling decision.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when `synthtiger`, `pytweening`, NumPy, OpenCV, fonts, corpora, or output paths fail.
- Use [`scripts/render_config.py`](scripts/render_config.py) when you need to turn the bundled placeholder configs into a runnable config that points at external resource directories.
- For shared install/import issues with the broader Donut stack, check the parent-tree troubleshooting file at [`../../references/troubleshooting.md`](../../references/troubleshooting.md) once it exists.
- If the user is actually trying to fine-tune on generated data, hand off to [`../training/SKILL.md`](../training/SKILL.md).

## Boundaries

- Include: template behavior, background/document/content/layout helper modules, language configs, resource requirements, CLI invocation through `synthtiger`, output directory and metadata layout, tiny-fixture generation.
- Exclude: Donut training, inference, and evaluation metrics.

## Quick checks

- `python scripts/render_config.py --help`
- `synthtiger --help` if SynthDoG is installed in the active environment
- `python -m py_compile scripts/render_config.py scripts/template.py scripts/elements/*.py scripts/layouts/*.py`

## What to do

1. Choose the language bundle and resource root.
2. Render a config with `scripts/render_config.py`.
3. Run `synthtiger` from this sub-skill root with `scripts/template.py`, the `SynthDoG` template class name, and the rendered config.
4. Inspect the split directories and `metadata.jsonl` files that `template.py` writes.
5. If the user later wants model training on the generated data, route the dataset to the training sub-skill.
