# Development and Testing Notes

## Purpose

Read this only when the user is already working in a Giskard OSS source checkout
and asks for maintainer-style validation or code changes. For ordinary package
usage, start with `package-overview.md` and the workflow sub-skills.

## Repository shape to expect in a checkout

Giskard OSS is a `uv` workspace of pure Python libraries:

- `giskard-core`
- `giskard-llm`
- `giskard-agents`
- `giskard-checks`
- `giskard-scan`

The import namespace remains `giskard.<sublib>`. Package-specific source and
unit tests live under each workspace library. There is no server, daemon, or CLI
that must be started for the base package workflows; validation is done through
Python imports and tests.

## Maintainer validation commands

When validating changes in a checkout that has the repository's own Makefile,
prefer the documented Makefile targets from the checkout root:

```bash
make install
make install-tools
make format
make check
make test-unit PACKAGE=giskard-checks
```

Replace `giskard-checks` with the affected package (`giskard-core`,
`giskard-llm`, `giskard-agents`, or `giskard-scan`) when the change is scoped.
Use all-package `make test-unit` only when cross-library behavior changed.

Do not run broad functional/provider tests by default. Functional tests require
live provider credentials such as OpenAI, Google/Gemini, Anthropic, or Azure
keys and may make network calls. Third-party scanner tests may require optional
scanner packages, remote access, or private dependencies.

## Package-specific edit routing

| Change request | Useful sub-skill | Native verification candidate |
| --- | --- | --- |
| New deterministic check, LLM judge, JSONPath behavior, Scenario/Suite result | `checks-evals` | Focused `giskard-checks` unit tests, especially builtin/core/generator tests. |
| Provider routing, message translation, error mapping, SDK availability | `llm-providers` | `giskard-llm` smoke/routing/provider translator tests; live functional tests only with keys. |
| Generator, ChatWorkflow, tools, templates, structured output | `agents-workflows` | `giskard-agents` smoke/tools/workflow/generator tests. |
| Vulnerability/quality scan, KnowledgeBase, generators, scanner bridges | `scan-redteam` | `giskard-scan` public API/quality/vulnerability/knowledge-base tests; optional scanner suites only when selected. |
| Telemetry, rate limiter, discriminated unions, version helpers | `runtime-setup` | `giskard-core` telemetry/rate-limiter/discriminated/error tests. |

## VM and environment caveats

- Prefer `make install` plus `make install-tools` over a full setup flow when
  pre-commit hook installation is blocked by a global hooks path.
- `make check` includes security and license gates that can reach PyPI or
  license metadata; offline failures in those steps are not the same as package
  import failures.
- Unit tests exclude `functional` markers. Provider and third-party integration
  coverage belongs to targeted functional/integration runs after credentials and
  network are explicitly available.
- If a user only needs installed-package behavior, use the bundled smoke scripts
  instead of source-checkout tests.

## Evidence preservation

When you fix or refresh this skill after repository changes, compare the current
checkout against `repo-provenance.md`. If commit, dirty state, package versions,
or public API signatures changed, run the repo-skill refresh workflow rather
than patching only one reference file.
