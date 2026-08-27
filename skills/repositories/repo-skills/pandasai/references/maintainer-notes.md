# PandasAI Maintainer Notes

## When to read

Read this only when the task is about modifying or validating a PandasAI checkout
rather than merely using the package. User-facing runtime workflows are routed
through the sub-skills.

## Contributor workflow

- PandasAI documents Poetry as the preferred contributor package manager.
- For code changes, add or update tests that cover the modified behavior.
- The documented formatter/linter is Ruff.
- The repo separates core tests from extension tests; extension packages are
  nested under `extensions/` and have their own package metadata.

## Make targets and what they imply

| Target | Intended use | Notes |
| --- | --- | --- |
| `make test_core` | Run core unit and integration tests | Installs core dependencies with dev tools first. |
| `make test_extensions` | Run tests for extension packages | Iterates over extension package directories and installs each extension's test dependencies. |
| `make test_all` | Full core plus extension test suite | Can be slow and broad because it installs all extension dependencies. |
| `make format_diff` | Check formatting/import ordering | Uses Ruff without modifying files. |
| `make format` | Apply formatting/import ordering | Mutates source files. |
| `make spell_check` / `make spell_fix` | Spell checking | `spell_fix` mutates files. |
| `make docs` | Serve docs | Uses docs tooling and may require packages beyond the core install. |

For repo-skill verification, prefer focused `pytest` cases from the native
candidate map rather than running all extension or all-extras targets. Full
extension tests may need network, credentials, Docker, or enterprise-only
packages.

## Version and compatibility notes

- The package metadata for the skill baseline is PandasAI `3.0.0`.
- The documented Python range is `>=3.8,<3.12`.
- v3 configuration is global through `pai.config.set(...)`; legacy per-wrapper
  configuration is only for compatibility wrappers.
- `SmartDataframe` and `SmartDatalake` are deprecated compatibility classes and
  should not be the target for new user-facing examples unless the task is
  migration.

## Safe maintainer test selection

When validating a change, select the smallest test set that covers the edited
surface:

| Edited surface | Focused tests to consider |
| --- | --- |
| CLI or API-key validation | CLI unit tests |
| DataFrame or chat routing | DataFrame and Agent unit tests |
| Response objects/parser | Response unit tests |
| Semantic schema, loaders, query builders | Data loader, query builder, and focused integration tests |
| Skills registry | Skills unit tests |
| Sandbox contract | Sandbox unit tests and SQL sanitizer tests |

Avoid credential-gated LLM judge tests unless the environment explicitly has the
required provider key and the user wants real network evaluation.
