# Repository overview

Strands Agents is a monorepo for building, testing, documenting, and operating model-driven AI agent SDKs and adjacent tooling. The repo has separate Python, TypeScript, docs-site, and MCP-server surfaces that share concepts and cross-SDK conventions.

## Main packages and routes

| Area | Package / role | Use this skill route |
| --- | --- | --- |
| Python SDK | `strands-agents`, import root `strands`, Python 3.10+ | `sub-skills/python-sdk/` |
| TypeScript SDK | `@strands-agents/sdk`, Node.js 20+ | `sub-skills/typescript-sdk/` |
| Docs site | Astro/Starlight site for user guide, API docs, examples, integrations | `sub-skills/docs-site/` |
| MCP server | `strands-agents-mcp-server`, docs search/fetch MCP tools | `sub-skills/mcp-server/` |
| Workspace CLI | `strandly`, local developer wrapper around root/npm workspace flows | TypeScript route plus root scripts |
| Team process | tenets, decisions, feature lifecycle, API bar, PR guidance | root cross-SDK reference |

## Directory model

| Directory | Runtime meaning |
| --- | --- |
| `strands-py/` | Python SDK source, tests, integration tests, package metadata, and Python developer docs. |
| `strands-ts/` | TypeScript SDK source, co-located tests, integration tests, examples, package metadata, and TypeScript developer docs. |
| `site/` | Documentation site source, MDX content, snippets, navigation, tests, and API-generation machinery. |
| `strands-mcp/` | MCP server that indexes Strands documentation and exposes `search_docs` / `fetch_doc`. |
| `strandly/` | TypeScript CLI package for workspace setup/build/test/check/format/example flows. |
| `team/` | Architecture, tenets, API bar, feature lifecycle, and PR process documents. |
| `.agents/` | Repo-local contributor skills and docs references used as source evidence; do not treat them as runtime dependencies of this generated skill. |
| `test-infra/` | AWS CDK stack for a small subset of integration tests. It is opt-in and excluded by default. |

## Included scope

This skill covers high-frequency package and maintainer workflows:

- implementing, debugging, and testing Python SDK features;
- implementing, debugging, packaging, and testing TypeScript SDK features;
- updating docs pages, snippets, source links, navigation, and generated API docs;
- maintaining the Strands docs-search MCP server;
- preserving cross-SDK parity, public/internal API boundaries, structured logging, comment style, and PR readiness.

## Excluded by default

Do not broaden into these areas unless the user's task explicitly selects them:

- live model-provider integrations that require credentials or external accounts;
- browser examples/tests that require Playwright, Chromium, or browser runtime setup;
- live documentation fetch tests that need network access;
- Docker/telemetry examples that need local services;
- AWS `test-infra/` provisioning, SSM-backed integration tests, or account-specific resources;
- GitHub release automation, metrics upload, or broad CI workflow edits;
- generated API output, build output, caches, vendored dependencies, and skill verification artifacts.

## Package identity and install quick facts

| Package | Public install/use clue | Local development clue |
| --- | --- | --- |
| Python SDK | `pip install strands-agents strands-agents-tools` for public use | Use the package-specific Python route for editable install and `hatch`/pytest guidance. |
| TypeScript SDK | `npm install @strands-agents/sdk` for public use | Use npm workspace commands from the repo root; Node 20+ is required. |
| Docs site | Public site at `strandsagents.com` | Use site npm scripts and do not edit generated API docs directly. |
| MCP server | `uvx strands-agents-mcp-server` for public use | Use offline pytest checks first; live docs tests are networked. |

## Native verification posture

The default selected verification scope is CPU/offline:

- Python and MCP server import/signature checks and selected offline unit tests are the strongest default native candidates.
- TypeScript and docs-site native checks require npm dependencies; run them when full Node/docs verification is selected.
- Provider, browser, network, Docker, and AWS-infra cases are optional or excluded until explicitly chosen.

## Staleness and refresh

Read `references/repo-provenance.md` before relying on this skill for a newer checkout. Refresh the skill when package exports, source layout, docs authoring rules, test commands, package versions, or cross-SDK conventions materially change.
