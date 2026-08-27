# Repository Provenance

schema: `disco.repo-provenance.v1`

- source repository: public DB-GPT repository (`https://github.com/eosphoros-ai/DB-GPT`)
- source commit: `c5fd007399691cc936e6d6a4bf4dee829db92135`
- source branch: `main`
- exact tag: none observed at the source commit
- package baseline: `dbgpt-mono` 0.8.1; workspace distributions `dbgpt`, `dbgpt-app`, `dbgpt-client`, `dbgpt-ext`, `dbgpt-serve`, `dbgpt-sandbox`, and `dbgpt-acc-auto` report 0.8.1
- source snapshot state: clean before generated runtime and review artifacts were created; generated files are untracked construction output and are not source evidence
- construction scope: public Python package and user-facing operating workflows; web frontend, generated/build output, benchmarks, broad maintainer automation, external services, credentials, and optional GPU/local-model stacks were not treated as required baseline behavior

## Evidence paths

- package metadata: `pyproject.toml`, `packages/*/pyproject.toml`, `uv.lock`
- core APIs and CLI: `packages/dbgpt-core/src/dbgpt/`
- application and OpenAPI: `packages/dbgpt-app/src/dbgpt_app/`
- Python client: `packages/dbgpt-client/src/dbgpt_client/`
- extensions/connectors/RAG: `packages/dbgpt-ext/src/dbgpt_ext/`
- service APIs: `packages/dbgpt-serve/src/dbgpt_serve/`
- sandbox runtime: `packages/dbgpt-sandbox/src/dbgpt_sandbox/`
- accelerator metadata: `packages/dbgpt-accelerator/dbgpt-acc-auto/`
- public product/install/config docs: `README.md`, `docs/docs/getting-started/`, `docs/docs/installation/`, `docs/docs/application/`, `docs/docs/agents/`, `docs/docs/awel/`, `docs/docs/modules/`, `docs/docs/config-reference/`, `docs/docs/sandbox/`
- representative workflows: `examples/agents/`, `examples/awel/`, `examples/client/`, `examples/rag/`, `examples/sdk/`, `examples/excel/`
- behavioral evidence: package-local `tests/`, `tests/unit_tests/`, selected `tests/intetration_tests/`
- installer/profile evidence: `scripts/install/`, `scripts/examples/`

## Refresh trigger

Refresh this repo skill when DB-GPT changes its public package version, CLI
command tree, provider/model configuration schema, API version/prefixes,
agent/AWEL interfaces, RAG/storage contracts, or sandbox runtime policy. A
source checkout is not required for runtime use, but it is required as the
fresh evidence anchor for a refresh.
