---
name: espnet3-workflows
description: "Use ESPnet3 System and Hydra stage workflows, config requirements,
  dry-run inspection, demo/publication boundaries, and stage troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Espnet3 Workflows

Use this sub-skill for ESPnet3 stage runners, Hydra config roles, System-based ASR workflows, `--stages`, dry-run planning, and demo/publication boundaries.

## Quick use

- Read [stage-runner.md](references/stage-runner.md) and [configuration.md](references/configuration.md); use the stage inspector before launching ESPnet3 stages.

## Boundaries

Route ESPnet2 shell recipes to `../recipes-and-data/SKILL.md`, ESPnet2 train CLIs to `../espnet2-training/SKILL.md`, install/import issues to `../installation-and-diagnostics/SKILL.md`, and CI/demo tests to `../development-and-testing/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
