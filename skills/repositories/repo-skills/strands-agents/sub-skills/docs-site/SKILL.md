---
name: docs-site
description: "Guide Astro/Starlight docs-site authoring, review, navigation,
  sourceLinks, snippets, and generated API docs work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Docs site

Use this sub-skill for work on the Strands Agents Astro/Starlight documentation
site, including page authoring, docs review, navigation, snippets, source links,
and generated API reference workflows.

## Start here

1. Read [overview.md](references/overview.md) to map site concerns, content sources, and routing boundaries.
2. Read [authoring.md](references/authoring.md) before changing page content, snippets, tabs, frontmatter, or terminology.
3. Read [workflows.md](references/workflows.md) for review, build, API regeneration, route, and migration flows.
4. Read [troubleshooting.md](references/troubleshooting.md) when validation or review fails.
5. Use [docs-site-check.sh](scripts/docs-site-check.sh) for focused site checks and [generate-api-docs.sh](scripts/generate-api-docs.sh) for generated API reference refreshes.

## Use this sub-skill for

- MDX frontmatter, page structure, content collections, Starlight components, and navigation.
- Language tabs, `<Syntax>`, snippet includes, TypeScript snippet scoping, relative links, and `@api` shorthand.
- `sourceLinks` maintenance when SDK files move or docs pages are backed by implementation files.
- Generated Python and TypeScript API docs regeneration; never hand-edit generated API output.
- Docs review, docs audit, docs planning, voice, terminology, and code-example verification.
- Site tests, snippet typechecks, route middleware, sidebar behavior, and build checks.

## Route elsewhere

- Python SDK implementation details, Python API signatures, or Python tests: use [python-sdk](../python-sdk/SKILL.md).
- TypeScript SDK implementation details, package exports, or Node/browser tests: use [typescript-sdk](../typescript-sdk/SKILL.md).
- Docs-search MCP server runtime, `search_docs`, or `fetch_doc`: use [mcp-server](../mcp-server/SKILL.md).

## Guardrails

- Do not hand-edit generated API docs; regenerate and review the resulting diff.
- Keep `sourceLinks` current in the same change when source files move or rename.
- Use the canonical term for each SDK concept; do not vary wording for style.
- Verify code examples against current SDK source before handoff, and omit unverifiable code rather than guessing.
- Use `<Syntax>` for one inline language-specific identifier and `<Tabs>` for multi-line or structurally different examples.
- Keep MDX pages readable from search: clear page goal, coherent content type, and no unexplained internal process artifacts.

## Fast path

1. Classify the task as authoring, review/audit, API regeneration, navigation/route maintenance, sourceLink repair, or troubleshooting.
2. Read the matching reference and choose the smallest check script mode that proves the affected surface.
3. If source files moved, update docs `sourceLinks` and verify API/source links before running broad site checks.
4. If snippets changed, run snippet typechecks and inspect rendered include boundaries.
5. Record skipped site build, API generation, or live-doc checks explicitly when dependencies or network access are unavailable.
