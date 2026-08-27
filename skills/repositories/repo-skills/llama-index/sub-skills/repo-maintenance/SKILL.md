---
name: repo-maintenance
description: "Maintain the LlamaIndex monorepo safely: inspect package layout
  and pyproject metadata, use llama-dev package/test commands, run targeted
  package tests, and triage docs/examples automation without performing release,
  publish, or credentialed sync actions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LlamaIndex Repo Maintenance

Use this sub-skill when an agent is working inside the LlamaIndex monorepo and needs to reason about package boundaries, test one package or a small changed set, inspect package metadata, or decide which maintenance scripts are safe to adapt.

## Safe Maintenance Defaults

- Treat the monorepo as many package projects, not one install target; package-local commands usually run from the package directory.
- Prefer read-only inspection before mutation: list packages, read `pyproject.toml`, inspect tests, then choose the narrowest command.
- Use `uv` package-local workflows for ordinary development and tests; avoid installing every integration unless the task explicitly requires broad validation.
- Keep release, publish, version bump, and credentialed docs sync commands out of normal runnable guidance unless a human explicitly asks for those workflows and confirms credentials/scope.
- When using `llama-dev`, run it from the repo root or pass `--repo-root`; package arguments are repository-relative package paths such as `llama-index-core` or `llama-index-integrations/llms/llama-index-llms-openai`.

## Start Here

1. Identify the package path and distribution name with the bundled read-only helper:

   ```bash
   python skills/llama-index/sub-skills/repo-maintenance/scripts/list_llama_packages.py --repo-root . --filter openai
   ```

2. Inspect the relevant package metadata:

   ```bash
   python skills/llama-index/sub-skills/repo-maintenance/scripts/list_llama_packages.py --repo-root . --package-path llama-index-core
   ```

3. Run package-local tests from the package directory when you only touched one package:

   ```bash
   cd llama-index-integrations/llms/llama-index-llms-openai
   uv run -- pytest
   ```

4. Use `llama-dev test` when you need changed-package/dependant selection or a consistent package test harness:

   ```bash
   llama-dev test llama-index-integrations/llms/llama-index-llms-openai --workers 1
   ```

5. If a command would bump versions, publish packages, sync external docs, or require secrets, stop and ask for explicit human approval.

## Common Workflows

### Run Tests for One Integration

- Locate the integration under `llama-index-integrations/<category>/<distribution-name>/`.
- Read its `pyproject.toml` and confirm its own dependency group instead of syncing unrelated integrations.
- From that package directory, run `uv run -- pytest`; this lets `uv` create/use the package-local environment.
- If local changes affect another package dependency, either install that changed package into the package environment deliberately or use `llama-dev test <package-path>` so the CLI can install local changed packages for test execution.

### Add or Update a Package

- Ensure the directory name, `project.name`, import namespace, and optional `tool.llamahub.import_path` all point to the intended integration.
- Confirm `requires-python`, runtime dependencies, and test/dev dependencies match package needs without inheriting unrelated integrations.
- Use the helper script to compare neighboring packages in the same integration category.
- Add or update package-local tests and run only the changed package first; broaden to dependant packages only after the narrow run passes.

### Use llama-dev Safely

- Safe inspection: `llama-dev pkg info <package-path>`, `llama-dev pkg info --all`, and JSON output when machine parsing helps.
- Safe targeted execution: `llama-dev pkg exec --cmd "uv sync" <package-path>` only when dependency installation is expected.
- Safe tests: `llama-dev test <package-path> --workers 1` or `llama-dev test --base-ref main --workers <n>` for changed-package selection.
- Reference-only: `llama-dev pkg bump` mutates package versions; `llama-dev release ...` supports release automation. Do not run these as routine maintenance.

## References

- [Monorepo layout](references/monorepo-layout.md)
- [llama-dev CLI](references/llama-dev-cli.md)
- [Source script inventory](references/source-script-inventory.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled Script

- `scripts/list_llama_packages.py` scans a supplied repository root for `pyproject.toml` files with `project.name`, prints paths and package metadata, and can emit JSON. It is read-only and safe to run with `--help`.
