---
name: wren-ai
description: "Use WrenAI and Wren Engine for governed semantic SQL, MDL
  projects, data-context memory, agent workflow guides, GenBI dashboards, MCP
  tools, browser WASM queries, framework SDKs, and repository development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# WrenAI

Use this skill for WrenAI, the `wrenai` Python distribution, the `wren` CLI,
`wren_core`, `wren-langchain`, `wren-pydantic`, or `@wrenai/wren-core-wasm`.
It covers the semantic layer that turns SQL written against modeled objects into
target-database SQL, plus the project context and agent-facing workflows around
it.

## Start Here

1. Install only the components required by the requested workflow:
   ```bash
   pip install wrenai
   # Add one datasource extra only when needed, for example:
   pip install "wrenai[postgres]"
   ```
2. Verify the public CLI before relying on a project:
   ```bash
   wren --version
   wren --help
   ```
3. If a task needs a Wren project, verify that `wren_project.yml` and
   `target/mdl.json` exist. Build the target after changing source YAML:
   ```bash
   wren context validate
   wren context build
   ```
4. Route to the owning sub-skill before giving detailed commands. Wren workflows
   are order-sensitive: profile/project setup precedes query execution, and
   model/knowledge changes precede re-indexing or deployment.

## Route by Task

- **Projects, profiles, MDL, connections, dbt/OSI import, or type mapping**:
  read `sub-skills/cli-projects/SKILL.md`.
- **SQL queries, dry plans, dry runs, cubes, connectors, policies, or the
  Python `WrenEngine`**: read `sub-skills/query-engine/SKILL.md`.
- **Business rules, `knowledge/`, query memory, semantic retrieval, recall,
  stored NL→SQL pairs, or context enrichment**: read
  `sub-skills/memory-knowledge/SKILL.md`.
- **`wren skills`, agent onboarding/generation guides, `wren ask`, dlt/SaaS
  ingestion, or authoring a CLI-served Wren guide**: read
  `sub-skills/agent-workflows/SKILL.md`.
- **GenBI apps, Vercel/Cloudflare deployment, `wren serve mcp`, MCP tools, or
  browser-side WebAssembly**: read `sub-skills/genbi-mcp-wasm/SKILL.md`.
- **LangChain, LangGraph, Pydantic AI, `WrenToolkit`, or agent-tool contracts**:
  read `sub-skills/sdk-integrations/SKILL.md`.
- **`wren_core`, Rust/PyO3/WASM maintenance, local engine builds, tests, or
  contributor policy**: read `sub-skills/engine-development/SKILL.md`.

## Core Operating Rules

- Treat the Wren project as portable business context: MDL source, `knowledge/`,
  and the compiled `target/mdl.json` serve different roles. Do not confuse the
  project-level `catalog`/`schema` namespace with a model's physical database
  `table_reference`.
- Profiles hold connection values and should use `${ENV_VAR}` placeholders; do
  not put credentials in project YAML, shell-history flags, agent prompts, or
  static GenBI files.
- Write SQL against Wren models and views. For complex or costly work, run
  `wren dry-plan` first; use `wren dry-run` only when a live database validation
  is intended.
- Prefer `wren cube query` for covered aggregation questions. It constrains
  measure, dimension, time-grain, and filter choices instead of requiring an
  agent to invent `GROUP BY` and date logic.
- Treat `knowledge/sql/` as the source of truth for accepted NL→SQL pairs.
  A LanceDB index is derived state and may be rebuilt; do not delete source
  knowledge just to repair the index.
- Keep GenBI deployment credentials server-side or in environment files. A
  static app is public to its viewers, so a successful deploy is not proof that
  it is safe or publicly reachable.
- Optional datasource, memory, MCP, UI, Rust, Node, and browser features must
  be named explicitly before use. Do not assume `wrenai[all]` or a database
  service is installed.

## Shared References and Helper

- Read `references/overview.md` for the architecture and package map before
  crossing CLI, SDK, MCP, and WASM boundaries.
- Read `references/install-and-extras.md` when choosing a public install command
  or diagnosing optional dependencies.
- Read `references/troubleshooting.md` for cross-cutting installation, profile,
  project-discovery, dependency, and credential issues.
- Read `references/repo-provenance.md` before relying on this skill for a new
  checkout or deciding whether to refresh it.
- Run `scripts/check_wren_environment.py` for a safe public import/CLI check;
  it does not connect to a database or write a project.

## Avoid

- Do not run `wren query` against an unreviewed production profile merely to
  discover schema. Start with project inspection, `wren context show`, memory
  context, or a dry plan.
- Do not pass secrets through `--connection-info`, GenBI deploy arguments, or
  static app files when an environment-backed profile is available.
- Do not treat an optional service connector, semantic-memory stack, MCP server,
  or WebAssembly build as verified merely because the base package imports.
- Do not use repository maintainer build commands for ordinary package-user
  workflows; route those tasks to `engine-development`.
