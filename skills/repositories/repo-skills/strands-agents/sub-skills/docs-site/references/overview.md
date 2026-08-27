# Docs-site overview

Use this reference to decide where a docs change belongs, which rules apply, and
when to route work out of the docs-site sub-skill.

## What this skill covers

- MDX page authoring for the Astro/Starlight documentation site
- frontmatter, language tabs, `<Syntax>`, snippet includes, and relative links
- `sourceLinks` metadata and generated API reference pages
- navigation, route coverage, and targeted docs maintenance scripts
- docs-writing, review, audit, and planning flows
- build, test, snippet, format, and API-generation checks

## Concern map

| Concern | Runtime reference | What it controls |
| --- | --- | --- |
| Page schema and metadata | `references/authoring.md` | required frontmatter, optional fields, and source pointers |
| MDX patterns | `references/authoring.md` | tabs, syntax switching, snippets, links, callouts, and line length |
| Navigation and routes | `references/workflows.md` | sidebar groups, header sections, and known-route maintenance |
| Generated API docs | `references/workflows.md` and `scripts/generate-api-docs.sh` | regeneration flow and direct-edit guardrails |
| Site checks | `scripts/docs-site-check.sh` | test, typecheck, snippet typecheck, build, and format check |
| Failures and drift | `references/troubleshooting.md` | common build, rendering, link, sourceLink, and voice issues |

## Evidence base distilled into this skill

This sub-skill distills the docs-site evidence, not the live source files as
runtime dependencies:

- Site agent guide: directory layout, check commands, docs-specific cautions,
  and authoring responsibilities.
- Site architecture notes: Starlight customizations, sidebar middleware,
  snippet inclusion, link resolution, generated API docs, and LLM-friendly
  outputs.
- Site package manifest: authoritative npm script names for build, tests,
  typechecks, snippets, formatting, and SDK API generation.
- Content schema: validated frontmatter fields, language restrictions,
  catalog fields, redirects, tags, and `sourceLinks` behavior.
- Navigation config: navbar, sidebar, GitHub dropdown, group collapse, and badge
  conventions.
- Snippet plugin: MkDocs-style `--8<--` syntax, marker matching, section
  extraction, dedent behavior, and graceful missing-file or missing-section
  output.
- Link utilities: relative link normalization, `@api` shorthand, slug matching,
  base-path handling, and raw-markdown URL conversion.
- Site tests and snippet tests: expected behavior for links, source links,
  snippets, sidebar, route middleware, generated API docs, schemas, redirects,
  and route coverage.
- Docs authoring references: MDX authoring, terminology, code verification,
  and voice constraints.
- Existing docs workflows: write or rewrite pages, review drafts, audit
  published pages for source accuracy, and plan larger docs backlogs.

## Routing boundaries

Stay in docs-site when the work is about the site, docs content, page metadata,
navigation, generated docs, or docs review. Route out when the user is asking to
change runtime behavior rather than documentation:

- SDK implementation or API behavior belongs to python-sdk or typescript-sdk.
- Docs-search MCP server runtime belongs to mcp-server.
- Repository-wide contribution process can use the repo root guidance, then
  return here for docs-site-specific checks.

## Default outcome for a docs change

A finished docs-site change should have:

1. Valid frontmatter and page structure.
2. Correct MDX components, snippets, links, and source metadata.
3. Code examples verified against the SDK source, not guessed.
4. Generated API docs regenerated instead of hand-edited when API output changes.
5. Site checks run or an explicit explanation of the unrun checks.
