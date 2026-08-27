# Repo Provenance

- schema: disco.repo-provenance.v1
- Source project: LlamaIndex
- Source repository identity: `run-llama/llama_index` from package metadata
- Source commit: `9f66e8a649856524ef0ff081a23d58cd071b6ae4`
- Source branch: `main`
- Exact tag: none detected
- Remote URL: https://github.com/run-llama/llama_index
- Working tree at extraction start: clean; generated `skills/` artifacts were added afterward
- Root package version from `pyproject.toml`: `llama-index==0.14.22`
- Live inspected package: `llama-index-core==0.14.22`
- Python support from metadata: `>=3.10,<4.0`

## Evidence Paths

- `README.md`
- `pyproject.toml`
- `llama-index-core/pyproject.toml`
- `llama-index-core/llama_index/core/`
- `llama-index-core/tests/`
- `llama-index-integrations/`
- `llama-index-utils/`
- `llama-index-instrumentation/`
- `llama-dev/`
- `docs/src/content/docs/framework/`
- `docs/examples/`
- `scripts/`
- `docs/scripts/`

## Refresh Triggers

Refresh this skill if the LlamaIndex core minor version changes, public imports move away from `llama_index.core`, the agent/workflow APIs change, `Settings` migration guidance changes, package naming conventions change, or monorepo tooling such as `llama-dev` changes substantially.
