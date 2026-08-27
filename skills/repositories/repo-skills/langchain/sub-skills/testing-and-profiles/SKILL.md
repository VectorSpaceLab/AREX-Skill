---
name: testing-and-profiles
description: "Select safe LangChain package verification commands, standard
  tests, pytest markers, import/version checks, integration-test skip rules, and
  model-profile refresh workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangChain Testing and Profiles

Use this sub-skill when a task asks how to validate LangChain changes, add or run standard tests, choose safe native verification commands, inspect package-local pytest/ruff/mypy checks, handle snapshots or strict pytest markers, or refresh model profile data.

## Start Here

1. Identify the owning package and run commands from that package directory, not from the repository root.
2. Prefer deterministic unit tests and static checks before integration tests. Use [native-verification.md](references/native-verification.md) and [select_safe_langchain_checks.py](scripts/select_safe_langchain_checks.py) to choose a minimal no-network check set.
3. For integration conformance tests, use [standard-tests.md](references/standard-tests.md) to distinguish `langchain_tests.unit_tests` from `langchain_tests.integration_tests`.
4. For profile data changes, use [model-profile-cli.md](references/model-profile-cli.md); do not manually edit generated `_profiles.py` unless the maintainer explicitly requests it.
5. If pytest, snapshots, credentials, markers, `uv`, or profile refresh commands fail, use [troubleshooting.md](references/troubleshooting.md).

## Routing Rules

- Standard interface tests, pytest markers, cassettes, snapshots, `pytest-socket`, `ruff`, `mypy`, package-local import checks, version checks, and model profile refreshes belong here.
- Provider package implementation details, API-client behavior, credentials, model defaults, and provider-specific feature semantics should route to `../integrations/SKILL.md` when that sibling exists.
- Core primitives, public API contracts, serialization, messages, runnables, callbacks, and tools should route to `../core-primitives/SKILL.md`.
- Agents, middleware, response formats, and LangGraph-backed behavior should route to `../agents-and-middleware/SKILL.md`.
- Classic chains and legacy `langchain-classic` behavior should route to `../classic-chains/SKILL.md`.
- Monorepo package ownership, dependency groups, public API guardrails, and contribution conventions should route to `../monorepo-development/SKILL.md`.

## Safe Validation Defaults

Run only commands that match the changed package and task risk:

```bash
cd libs/<package>
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
uv run --group lint ruff check .
uv run --group typing mypy .
```

When available in the package Makefile, prefer package-local targets such as `make test`, `make lint`, `make format`, `make type`, `make check_imports`, or `make check_version` because they encode package conventions. If `uv` is unavailable, do not claim validation ran; report that checks are blocked by missing `uv` and list the commands to run in a prepared environment.

## Skip Conditions

Skip or ask before running checks that require any of the following:

- Network access, provider API credentials, real cloud services, Docker services, local model servers, or browser/system services.
- Integration test directories that are not explicitly requested or that rely on cassettes, `pytest-recording`, VCR, scheduled markers, or external services.
- GPU-heavy, model-download-heavy, tokenizer/model corpus downloads, or optional dependency groups that are unrelated to the changed files.
- Snapshot updates such as `--snapshot-update` unless the user confirms that changed serialized output is intentional.

## References

- [Standard tests](references/standard-tests.md)
- [Native verification](references/native-verification.md)
- [Model profile CLI](references/model-profile-cli.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe check selector](scripts/select_safe_langchain_checks.py)
