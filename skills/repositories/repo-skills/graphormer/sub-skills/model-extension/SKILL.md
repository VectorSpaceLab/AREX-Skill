---
name: model-extension
description: "Inspect and extend Graphormer fairseq models, tasks, criterions,
  and architectures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graphormer model-extension

Use this sub-skill when a future agent must inspect, register, or extend Graphormer fairseq user-dir components: models, model architectures, tasks, criterions, Graphormer encoder internals, Graphormer3D interfaces, or GraphMLP-style custom models.

## Route elsewhere

- Training command schedules, dataset-specific `fairseq-train` recipes, and GPU/runtime choices belong to the `fairseq-training` sub-skill.
- Dataset sources, split contracts, custom dataset modules, and collation/preprocessing details belong to the `datasets-and-customization` sub-skill.
- Pretrained checkpoint selection, fine-tuning output-layer choices, and evaluation loops belong to the `pretrained-and-evaluation` sub-skill.
- Distributional Graphormer (DiG) diffusion internals belong to the `distributional-graphormer` sub-skill.

## Runtime resources

1. Read [references/model-api-reference.md](references/model-api-reference.md) for verified registry names, API signatures, architecture defaults, import behavior, model outputs, and criterion/task compatibility notes.
2. Read [references/extension-recipes.md](references/extension-recipes.md) for self-contained recipes to add a model, architecture, task, or criterion in a Graphormer fairseq user-dir.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when registries are missing, imports fail, shapes do not match criterions, or Graphormer3D tensors are rejected.
4. Run [scripts/summarize_graphormer_registries.py](scripts/summarize_graphormer_registries.py) to safely import a user-dir and summarize fairseq registry entries without training, downloading data, or loading checkpoints.

## Safe registry check

```bash
python scripts/summarize_graphormer_registries.py --user-dir <graphormer-package-dir> --format text
python scripts/summarize_graphormer_registries.py --user-dir <graphormer-package-dir> --format json --require-complete
```

`<graphormer-package-dir>` is the directory that contains Graphormer's `models/`, `tasks/`, and `criterions/` packages. The script only imports Python modules and reads fairseq registries.
