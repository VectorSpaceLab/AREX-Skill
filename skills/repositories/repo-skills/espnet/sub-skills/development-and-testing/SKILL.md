---
name: development-and-testing
description: "Maintain, test, review, and contribute to ESPnet source code,
  recipes, CI checks, style, and focused verification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Development And Testing

Use this sub-skill when the user is editing an ESPnet checkout, adding modules or recipes, selecting tests, debugging CI, or following contribution policy.

## Quick use

- Read [testing-and-contributing.md](references/testing-and-contributing.md) and [ci-command-map.md](references/ci-command-map.md); use the test selector before running broad CI.

## Boundaries

Route user-facing recipe use to `../recipes-and-data/SKILL.md`, training usage to `../espnet2-training/SKILL.md`, install failures to `../installation-and-diagnostics/SKILL.md`, and inference usage to `../inference-and-model-zoo/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
