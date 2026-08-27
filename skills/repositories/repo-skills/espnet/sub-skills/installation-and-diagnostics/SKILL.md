---
name: installation-and-diagnostics
description: "Install, verify, and troubleshoot ESPnet environments, optional
  extras, host tools, and CPU/CUDA backend readiness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Installation And Diagnostics

Use this sub-skill when the user needs to install ESPnet, choose extras, verify imports, diagnose optional modules or host tools, or separate CPU readiness from CUDA/distributed readiness.

## Quick use

- Read [install-matrix.md](references/install-matrix.md) and [troubleshooting.md](references/troubleshooting.md); run `scripts/check_espnet_environment.py` for safe diagnostics.

## Boundaries

Route data layouts to `../recipes-and-data/SKILL.md`, training config to `../espnet2-training/SKILL.md`, inference to `../inference-and-model-zoo/SKILL.md`, and maintainer tests to `../development-and-testing/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
