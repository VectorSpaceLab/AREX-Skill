# Repository provenance

Schema: `disco.repo-provenance.v1`

This file records the source baseline used to generate this self-contained repo skill. It intentionally omits local checkout paths and private environment paths.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | `strands-agents/harness-sdk` |
| Remote URL | `https://github.com/strands-agents/harness-sdk.git` |
| Commit | `11ad6366a1578d432ea4cd2c3ed41b610953d297` |
| Branch | `main` |
| Exact tag at HEAD | `mcp/v0.2.9` |
| Working tree state at generation | Dirty: untracked `skills/` directory contains generated runtime and verification artifacts. |

## Package facts

| Package / area | Version evidence |
| --- | --- |
| Python SDK distribution `strands-agents` | Installed inspection version `0.1.dev1+g11ad6366a`; source metadata uses dynamic VCS version from `python/v*` tags. |
| MCP server distribution `strands-agents-mcp-server` | Installed inspection version `0.2.9`; source metadata uses dynamic VCS version from `mcp/v*` tags. |
| TypeScript SDK package `@strands-agents/sdk` | `0.0.1-development` in package metadata. |
| Docs site package | `docs` version `1.0.0`. |
| Workspace CLI package `@strands-agents/strandly` | `0.0.1`. |

## Evidence paths distilled

The generated skill distilled these relative source paths:

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`
- `team/` process and design documents
- `strands-py/AGENTS.md`, `strands-py/README.md`, `strands-py/pyproject.toml`, `strands-py/docs/`, `strands-py/src/strands/`, `strands-py/tests/`, selected `strands-py/tests_integ/` metadata
- `strands-ts/AGENTS.md`, `strands-ts/README.md`, `strands-ts/package.json`, `strands-ts/docs/`, `strands-ts/src/`, `strands-ts/examples/`, selected `strands-ts/test/` metadata
- `site/AGENTS.md`, `site/SITE-ARCHITECTURE.md`, `site/package.json`, `site/src/`, `site/test/`, `site/test-snippets/`, selected `site/scripts/` metadata
- `.agents/skills/` and `.agents/references/` as contributor-workflow and docs-authoring evidence
- `strands-mcp/README.md`, `strands-mcp/pyproject.toml`, `strands-mcp/src/strands_mcp_server/`, `strands-mcp/tests/`, selected `strands-mcp/tests_integ/` metadata
- `strandly/src/cli.ts`, root `package.json`, and root `package-lock.json`
- `test-infra/AGENTS.md` as exclusion and safety evidence

## Excluded evidence

Generated output, caches, virtual environments, `node_modules`, build artifacts, generated API docs, review artifacts, release automation, and AWS test infrastructure were excluded from runtime skill content unless explicitly recorded as safety or scope boundaries.

## Refresh triggers

Refresh this skill when any of the following change materially:

- public package exports, package entry points, optional extras, or versions;
- cross-SDK naming, hook event, logging, public/internal API, or comment rules;
- Python or TypeScript source layout, test layout, package scripts, or runtime floors;
- docs frontmatter schema, snippet syntax, generated API docs, `sourceLinks`, navigation, or site test commands;
- MCP server `search_docs` / `fetch_doc` return shapes, URL restrictions, cache/indexing behavior, or environment variables;
- `test-infra/` policy or the default safe/native verification scope.
