---
name: recipes-and-data
description: "Create, adapt, validate, and troubleshoot ESPnet2 recipes,
  Kaldi-style data directories, stage commands, and utility CLIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Recipes And Data

Use this sub-skill for ESPnet2 recipe setup, Kaldi-style data layouts, `run.sh` stage planning, tokenization, audio formatting, and safe structural validation.

## Quick use

- Read [kaldi-data-formats.md](references/kaldi-data-formats.md), [espnet2-recipes.md](references/espnet2-recipes.md), and [utility-cli-reference.md](references/utility-cli-reference.md); run the validator scripts for structural checks.

## Boundaries

Route installation failures to `../installation-and-diagnostics/SKILL.md`, model components to `../espnet2-training/SKILL.md`, pretrained inference to `../inference-and-model-zoo/SKILL.md`, and contribution policy to `../development-and-testing/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
