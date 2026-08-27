---
name: setup-memory-core
description: "Bootstrap PyRIT setup, memory, registries, core models, and output
  helpers safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyRIT setup, memory, registry, and output core

Use this sub-skill when a task needs to start a PyRIT process, choose a memory backend, load configuration safely, inspect or register framework components, retrieve stored conversations/results, or render PyRIT objects. It is for PyRIT `1.1.0.dev0` and assumes normal Python imports from the installed `pyrit` package.

## Route here for

- Choosing between direct `initialize_pyrit_async(...)` and file-driven `initialize_from_config_async(...)`.
- Creating no-secret quick sessions with `InMemory` or temporary/local `SQLite` memory.
- Understanding `~/.pyrit/.pyrit_conf`, `.env`, `.env.local`, custom `env_files`, and Azure Key Vault references without committing secrets.
- Using `CentralMemory` after initialization and querying memory labels, conversations, scores, attack results, and scenario results.
- Inspecting PyRIT registries such as `ConverterRegistry`, `TargetRegistry`, `ScorerRegistry`, `InitializerRegistry`, and instance registries.
- Creating or checking core model objects (`MessagePiece`, `Message`, `Score`, `AttackResult`, identifiers, filters) needed by setup and memory workflows.
- Rendering attack results, conversations, scores, scorers, and scenario results with `pyrit.output` helpers and safe sinks.

## Route elsewhere

- Prompt target credentials, target-specific constructor parameters, scorer selection, rate limits, and live service verification: [targets-scorers](../targets-scorers/SKILL.md).
- Converter classes, converter stacks, seed datasets, dataset YAML/data schemas, and modality conversion: [converters-datasets](../converters-datasets/SKILL.md).
- Running attacks, scenarios, executors, techniques, concurrency, retry policies, and interpreting attack outcomes: [attacks-scenarios](../attacks-scenarios/SKILL.md).
- `pyrit_scan`, `pyrit_shell`, `pyrit_backend`, backend REST server configuration, and scanner command flags: [cli-backend-scanner](../cli-backend-scanner/SKILL.md).

## Start sequence

1. Decide the initialization path and memory backend using [references/setup-memory-registry.md](references/setup-memory-registry.md).
2. Check exact signatures and model fields in [references/api-reference.md](references/api-reference.md) before writing code.
3. If setup, registry, memory, or output fails, use [references/troubleshooting.md](references/troubleshooting.md) before changing credentials, database files, or registry names.
4. For a no-secret local import/API smoke check, run [scripts/setup_memory_smoke.py](scripts/setup_memory_smoke.py). The helper inspects installed APIs and can optionally construct lightweight in-memory/temporary objects; it never contacts external services.

## Safety defaults

- Prefer `InMemory` for examples, tests, and one-off agent work where persistence is not needed.
- Prefer a caller-owned SQLite path under a temporary or project-approved directory when persistence is needed. Do not silently reuse an old database when labels/results look stale.
- Treat Azure SQL memory as optional and credentialed; use only when the task explicitly requires shared database state and the caller has supplied the required environment.
- Do not print, log, commit, or copy real `.env` values. Use `.env.local` for personal overrides and placeholders in examples.
- Avoid loading default `~/.pyrit` files during no-secret checks; import and introspection are usually enough to validate package availability.
