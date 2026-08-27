# llama-dev CLI

`llama-dev` is a Click-based development CLI for package inspection, package-scoped command execution, test selection, and release support in the monorepo. Run it from the repository root when possible; otherwise pass `--repo-root <repo>`.

## Safe Inspection Commands

```bash
llama-dev --help
llama-dev pkg info llama-index-core
llama-dev pkg info --all
llama-dev pkg info --all --json
```

Notes:

- Package arguments are paths relative to the repo root, not PyPI names.
- `pkg info --json` is intended for machine parsing, but verify output shape before depending on it in automation.
- If a path is not a package root with `pyproject.toml`, `llama-dev` raises a usage error.

## Safe Test Commands

```bash
llama-dev test llama-index-core --workers 1
llama-dev test llama-index-integrations/llms/llama-index-llms-openai --workers 1
llama-dev test --base-ref main --workers 4
llama-dev test --base-ref main --cov --cov-fail-under 80
```

Behavior to expect:

- The CLI requires either explicit package paths or `--base-ref`.
- For `--base-ref`, it uses `git diff --name-only <base>...HEAD` to find changed packages.
- It includes dependant packages unless coverage mode is enabled.
- It skips packages without tests and packages incompatible with the current Python version.
- It runs package-local `uv sync`, then `uv run --no-sync -- pytest -q --disable-warnings --disable-pytest-warnings`.
- Per-package test execution has a timeout; use package-local pytest directly when you need custom flags or interactive debugging.

## Safe Command Execution

```bash
llama-dev pkg exec --cmd "uv sync" llama-index-core
llama-dev pkg exec --cmd "uv run -- pytest" llama-index-core --fail-fast
```

Cautions:

- `pkg exec` splits the command string on spaces and does not provide full shell quoting semantics.
- Avoid `--all` unless broad package mutation or dependency installation is explicitly intended.
- Do not pass commands that publish, upload, delete, rewrite history, or require credentials.

## Reference-Only Commands

The CLI includes commands that mutate release state:

- `llama-dev pkg bump ...` updates versions in package `pyproject.toml` files. Even with `--dry-run`, treat it as release-prep tooling and ask before using it.
- `llama-dev release ...` contains release process utilities. Do not run release commands during ordinary repo maintenance.

## Error Patterns

- `Either specify a package name or use the --all flag`: provide package paths or use `--all` only for intentional broad operations.
- `<name> is not a path to a LlamaIndex package`: pass a repo-relative package path such as `llama-index-core`, not `llama-index-core` as a distribution name from outside the repo or an import path like `llama_index.core`.
- `Option '--base-ref' cannot be empty`: omit the flag or provide a real branch/ref.
- Install failures are reported separately from test failures; inspect package dependencies and Python compatibility before assuming code regressions.
