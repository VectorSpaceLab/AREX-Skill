---
name: extension-development
description: "Guides agents extending RLinf algorithms, models, environments,
  rewards, workers, runners, configuration validation, tests, documentation,
  Docker, and CI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RLinf extension development

Use this sub-skill when the task is to add or modify RLinf extension points: algorithms, advantage functions, policy losses, rule-based rewards, reward models or reward parsers, embodied models, environments, workers, runners, task types, config validation, install support, Docker images, CI jobs, documentation, or e2e coverage.

Do **not** use this sub-skill for simply running an existing embodied/reasoning recipe, operating a Ray cluster, or triaging logs/checkpoints from an existing run. Route those tasks to the appropriate runtime, setup/cluster, or operations/debugging guidance.

## Start here

1. Identify the extension kind and whether it is a core RLinf contribution or an external package that depends on RLinf.
2. Generate the safe checklist for the kind with [scripts/scaffold_extension_checklist.py](scripts/scaffold_extension_checklist.py). It only prints guidance and never edits files.
3. Follow the relevant bundled references:
   - [references/extension-recipes.md](references/extension-recipes.md) for end-to-end recipes by extension kind.
   - [references/api-registration-reference.md](references/api-registration-reference.md) for registries, config keys, validation gates, worker hooks, and external registration limits.
   - [references/install-docker-ci-docs.md](references/install-docker-ci-docs.md) for install script, Docker, CI, docs, and e2e coverage.
   - [references/contributor-guidance.md](references/contributor-guidance.md) for style, tests, YAML, logging, commits, and PR rules.
   - [references/troubleshooting.md](references/troubleshooting.md) for common registration, distributed worker, config, action conversion, FSDP, install, and CI failures.

## Routing map

- **Algorithms, advantages, losses, rule-based rewards, tool parsers:** use the registry contracts in [API registration reference](references/api-registration-reference.md) and the algorithm recipe in [extension recipes](references/extension-recipes.md).
- **Embodied models:** decide first between external `register_model(...)` plus `RLINF_EXT_MODULE` and a core built-in model edit; then cover BasePolicy, FSDP/Megatron, action format, config, tests, and docs.
- **Environments:** usually require core source edits because `SupportedEnvType` is an enum; cover lazy import, action preparation, wrappers/offload, config presets, validation, install, and e2e.
- **Workers/runners/task types:** extend `Worker`/`WorkerGroup` and runner ownership deliberately; add task validation, entrypoint wiring, placement, channels, metrics, checkpoint/eval behavior, and tests.
- **New model/env capabilities:** include install, Docker, CI, docs, and e2e changes unless the task explicitly limits scope to an internal prototype.

## Non-negotiables

- Treat Ray workers as separate Python processes. Any external model/algorithm/reward/parser registration that workers need must be importable through `RLINF_EXT_MODULE` or must be wired into core source imports.
- Do not instantiate `Worker` subclasses directly in the driver; launch them with `create_group(...).launch(...)` and let placement assign ranks and devices.
- Keep user-facing config YAML static. Put derived defaults and validation in Python validation code, not in YAML arithmetic.
- Use worker logging helpers inside workers and standard RLinf logging outside workers. Do not add new `print`-based diagnostics to production paths.
- Every user-facing extension needs tests and documentation. If an e2e requires special hardware or datasets, document the requirement and add the narrowest feasible CI/skip coverage.
