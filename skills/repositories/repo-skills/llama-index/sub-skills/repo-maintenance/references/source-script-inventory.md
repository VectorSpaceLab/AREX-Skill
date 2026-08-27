# Source Script Inventory

This inventory classifies repository scripts for future agents. Runtime guidance should adapt only safe read-only concepts unless the user explicitly asks for task-specific automation.

## Adapted Concept

- `scripts/integration_health_check.py`: useful conceptually for checking integration health from package metadata, tests, and activity signals. Do not copy its network-backed PyPI statistics or git-history scoring into routine maintenance. Prefer local, read-only metadata checks like the bundled `scripts/list_llama_packages.py`.

## Reference-Only

- `llama-dev/`: official CLI source. Use as evidence for command behavior and safe package/test workflows. Do not copy the CLI; tell agents to use it only when installed in their development environment.
- `scripts/convert-examples.py`: converts notebooks to Markdown and can write to documentation destinations. Treat as docs automation only when the user specifically requests example conversion or docs publishing preparation.
- `docs/scripts/prepare_for_build.py`: generates API reference pages and updates docs build configuration. Use only for docs maintenance tasks with explicit scope.

## Excluded from Runnable Guidance

- `scripts/bulk-version-bump.py`: bulk version mutation belongs to release preparation and is unsafe for routine maintenance.
- `scripts/publish_packages.sh`: package publishing can upload artifacts and requires release credentials; never run without explicit release authorization.
- `scripts/sync-docs-to-developer-hub.sh`: external docs synchronization may require credentials and mutate another documentation target; never run as default maintenance.
- Broad docs build scripts: they can generate or rewrite documentation trees and may require extra dependencies. Run only when docs maintenance is the task.

## Decision Rules

- Read-only inventory, metadata checks, and package-path discovery are safe.
- Package-local `uv run -- pytest` is safe when dependency installation is acceptable for the task.
- Commands that edit versions, publish packages, sync external docs, or depend on secrets require explicit human approval.
- Prefer writing small, local helper scripts inside this skill over pointing runtime users at source repo scripts as dependencies.
