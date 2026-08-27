# Galaxy Development and Testing

## Purpose

Read this when selecting safe, focused Galaxy validation commands for a repo change or when deciding whether a native test/example is safe to run.

## Test Suite Decision Tree

| Task shape | Native suite | Typical command shape | Safety notes |
| --- | --- | --- | --- |
| Pure Python helper, parser, schema, datatype, utility, or package code | Unit tests | `./run_tests.sh -unit` or targeted `pytest` | Usually safest when dependencies are installed; prefer one file/test first. |
| Galaxy API behavior requiring a running test server | API tests | `./run_tests.sh -api` | Starts/uses Galaxy test harness; service-backed. |
| Tool wrapper behavior only | Framework tool tests | `./run_tests.sh -framework` | Service-backed but often narrower than full integration. |
| Workflow Format2/framework behavior | Workflow framework tests | `./run_tests.sh -framework-workflows` | Service-backed workflow test harness. |
| Custom Galaxy config or backend service behavior | Integration tests | `./run_tests.sh -integration` or targeted `pytest test/integration/...` | Can start services and mutate temp DB/storage; inspect config first. |
| Browser UI behavior | Selenium/Playwright | `./run_tests.sh -selenium` or `./run_tests.sh -playwright` | Requires browser drivers and running Galaxy; skip unless explicitly needed. |
| Vue/TypeScript unit behavior | Client Vitest | `make client-test` or `pnpm test` from `client/` | Requires Node/pnpm deps; see web-client sub-skill. |
| Split package-only change | Package test | `make test` from the package directory or package-specific pytest | Use package README/Makefile conventions. |

## Safe Validation Order

1. Run the generated skill helper relevant to the task, such as a config, API dry-run, tool-util, datatype, Tool Shed planner, or client command planner.
2. Run parser/help/import checks before service-backed tests.
3. Run one targeted native unit test file before broad suites.
4. Escalate to API/integration/framework/Selenium/client build only when the changed behavior requires it.
5. Record skip reasons for network, credentials, cloud backends, destructive cleanup, long-running tests, unavailable browser/Node dependencies, or missing service state.

## Native Candidate Classification

Use these labels in verification notes:

- `safe-runnable`: short, deterministic, no service/network/credentials/destructive writes.
- `help-only`: safe only for `--help`, parser construction, version, or dry-run output.
- `tiny-fixture-runnable`: safe with a temporary fixture created for the test.
- `skip-service`: requires a running Galaxy/Tool Shed/test harness.
- `skip-network`: downloads, remote APIs, container registries, or external package indexes.
- `skip-credentials`: cloud storage, OAuth, private data, or API keys.
- `skip-expensive`: browser, large integration, benchmark, long workflow, or broad client build.
- `skip-unsafe`: purge, delete, migration, production index rebuild, database/storage mutation.

## Useful Test Ownership

- Config changes usually belong to [Configuration and Admin](../sub-skills/configuration-and-admin/SKILL.md) and candidate tests under config unit/integration suites.
- API route behavior belongs to [API Automation](../sub-skills/api-automation/SKILL.md) and API test helpers/populators.
- Tool XML/workflow behavior belongs to [Workflows and Tools](../sub-skills/workflows-and-tools/SKILL.md) and framework tool/workflow tests.
- Datatypes, file sources, and object stores belong to [Data and Storage](../sub-skills/data-and-storage/SKILL.md) and data/objectstore/files tests.
- Tool Shed repository behavior belongs to [Tool Shed Operations](../sub-skills/tool-shed-operations/SKILL.md) and Tool Shed unit/integration tests.
- Vue/TypeScript behavior belongs to [Web Client Development](../sub-skills/web-client-development/SKILL.md) and client Vitest/package commands.

## Common Pitfalls

- Do not treat a skipped credentialed/cloud test as a pass; pair it with a synthetic or local-unit assertion case when possible.
- Do not run destructive cleanup or migration scripts against non-disposable data.
- Do not use broad `./run_tests.sh` invocations before a targeted test has established confidence.
- Do not install full client or server dependency stacks just to inspect a small parser/config change.
