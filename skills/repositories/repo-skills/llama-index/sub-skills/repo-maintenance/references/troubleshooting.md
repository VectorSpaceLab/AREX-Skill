# Troubleshooting

## Package Name vs Path Confusion

Symptoms:

- `llama-dev` says a name is not a path to a LlamaIndex package.
- Imports use underscores but package distributions use hyphens.

Fix:

- Use repository-relative package paths with `llama-dev`, for example `llama-index-integrations/llms/llama-index-llms-openai`.
- Use distribution names from `project.name` for package-manager operations.
- Use import paths from package source or `[tool.llamahub].import_path` for Python imports.

## Editable Install from the Wrong Subpackage

Symptoms:

- Changes are not reflected during tests.
- The active import comes from another installed distribution.
- An integration test cannot find local core changes.

Fix:

- Run tests from the package root with `uv run -- pytest`.
- Check `[tool.uv.sources]` for local path overrides.
- If testing a dependant package after changing another local package, use `llama-dev test <package-path>` or explicitly install the changed local package into the target environment.

## Targeted Pytest Paths

Symptoms:

- A broad test command is slow or pulls unrelated integration dependencies.
- Test logs are hard to read under parallel execution.

Fix:

- Start inside the package directory: `uv run -- pytest tests/<specific_test>.py -q`.
- Use `llama-dev test <package-path> --workers 1` for package-scoped monorepo behavior.
- Avoid `llama-dev pkg exec --all` and repository-wide pytest unless broad validation is requested.

## Missing Development Dependencies

Symptoms:

- `pytest`, optional integration SDKs, or test plugins are missing.
- `uv run -- pytest` fails before collecting tests.

Fix:

- Confirm the package has `[dependency-groups].dev` entries for test dependencies.
- Run `uv sync` in the package root when dependency installation is expected.
- For integrations that rely on external services, mock remote calls and avoid requiring live credentials in tests.

## llama-dev Usage Errors

Symptoms:

- `Either pass '--base-ref' or provide at least one package name.`
- `You have to pass --cov in order to use --cov-fail-under`.
- `Option '--base-ref' cannot be empty.`

Fix:

- Provide explicit package paths for targeted tests.
- Use `--cov-fail-under` only with `--cov`.
- Use a real branch/ref for `--base-ref`, commonly `main`.
- Add `--debug` if truncated output hides the useful failure details.

## Unsafe Release or Publish Scripts

Symptoms:

- A requested command mentions version bumping, release preparation, publishing, package upload, or external docs sync.
- A script requires credentials or writes outside the checked-out repo.

Fix:

- Stop and ask for explicit approval before running the command.
- Prefer dry-run or read-only inspection if available.
- Record the intended packages, external targets, credentials needed, and rollback plan before any release or sync operation.
