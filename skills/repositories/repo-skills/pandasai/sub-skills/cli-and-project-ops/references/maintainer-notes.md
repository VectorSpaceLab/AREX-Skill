# CLI and Repo Maintainer Notes

## Purpose

Use this when the task is about a PandasAI checkout rather than a library-only
application.

## Dependency management

Contributor docs prefer Poetry for repository development:

```bash
poetry install --all-extras --with dev
```

For repo-skill usage or focused diagnostics, do not install all extras unless
the user explicitly needs extension development. A minimal library environment is
enough for core API and CLI inspection, with `click` required for CLI import.

## Useful focused commands

| Need | Command pattern |
| --- | --- |
| Run core tests | `pytest tests/unit_tests tests/integration_tests` or a focused subset |
| CLI behavior | `pytest tests/unit_tests/test_cli.py -q` |
| Semantic layer/loaders | `pytest tests/unit_tests/data_loader tests/unit_tests/query_builders -q` plus focused integration tests |
| Chat/Agent behavior | `pytest tests/unit_tests/agent tests/unit_tests/dataframe -q` |
| Custom skills registry | `pytest tests/unit_tests/skills -q` |
| Sandbox contract | `pytest tests/unit_tests/sandbox/test_sandbox.py -q` |
| Formatting | `make format_diff` to check, `make format` to mutate |
| Spell checking | `make spell_check` to check, `make spell_fix` to mutate |

Avoid credential-gated LLM judge tests unless a provider key is explicitly
available and the user wants network evaluation.

## Extension packages

Extension packages are separate nested packages for LLMs, SQL connectors, and
sandboxing. Their full test/install targets can pull many dependencies. For a
single user-facing task, install only the exact extension needed.
