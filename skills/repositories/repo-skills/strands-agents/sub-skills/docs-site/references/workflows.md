# Workflows

Use these playbooks after you know the content type and scope of the docs-site
change.

## Write or rewrite a page

Follow the docs-writer pattern: outline, draft, verify, review.

1. Classify the page as tutorial, how-to, reference, explanation, blog, or a
   mixed page that needs restructuring.
2. State the reader goal for the page and for each section before drafting.
3. Add valid frontmatter first. Use optional fields only when the schema supports
   them and the page needs them.
4. Choose the right MDX primitive:
   - `<Tabs>` for multi-line or multi-language content.
   - `<Syntax>` for one inline identifier that differs by SDK language.
   - Snippet includes for runnable TypeScript examples.
5. Keep shared prose language-neutral. Put language-specific syntax inside tabs
   or `<Syntax>`.
6. Use relative links for docs pages and `@api` shorthand for generated API
   reference links.
7. Verify code examples against SDK source, not by translation or memory.
8. Run `scripts/docs-site-check.sh`, or record which checks could not run and
   why.
9. Run the docs-reviewer flow for voice, structure, terminology, and example
   completeness before handoff.

## Review or audit a docs page

Use docs-reviewer for a draft that is trying to ship. Use docs-audit when the
page is published, the question is accuracy, or a rewrite needs a baseline.

1. Read the page as a standalone entry point from search or an AI assistant.
2. Check content type alignment. Mixed tutorial/reference/how-to structure is a
   finding, not a style choice.
3. Check section purpose. Each section should answer one reader question.
4. Check terminology and voice constraints.
5. Check code examples for imports, setup, realistic values, non-deterministic
   output labeling, and claim parity.
6. For API claims, verify against the SDK source. For two-language pages, verify
   Python and TypeScript separately.
7. Check `sourceLinks` if source files moved or the page claims implementation
   backing.
8. Check that generated API docs were regenerated, not hand-edited.
9. Produce a clear verdict: ship, tighten, or rethink. If the issue is a broader
   content gap, use the docs-planner flow before expanding scope.

## Regenerate API docs

Use this workflow when SDK source changed, a generated API page drifted, or an
API link points at a missing generated slug.

1. Run `scripts/generate-api-docs.sh` for both SDKs, or pass a language-specific
   option if only one SDK changed.
2. Review the diff under the generated API output. Do not edit generated files
   directly.
3. If anchors, module names, classes, or categories changed, update docs links to
   use the correct `@api` shorthand.
4. If a source file moved, update `sourceLinks` in affected page frontmatter in
   the same change.
5. Run `scripts/docs-site-check.sh` after regeneration.

## Navigation and route maintenance

Use this workflow when pages move, sidebar order changes, or route coverage
changes.

1. Update the navigation configuration for sidebar hierarchy, labels, collapse
   behavior, and badges. Page badges usually belong in page frontmatter; group
   badges may belong in navigation config.
2. Update header navigation only when top-level header tabs or GitHub dropdown
   sections change.
3. Keep route redirects explicit. Use page-level redirects for one-off page
   moves and structural route rules only for broad patterns.
4. Refresh known-route data when route coverage changes.
5. Run the full site check so unit tests, route middleware, sidebar behavior,
   build, and formatting all agree.

## Maintenance script map

These source scripts are part of the docs-site operating model. Prefer the npm
script when the package manifest exposes one.

| Workflow helper | Use when | Runtime-safe action |
| --- | --- | --- |
| API generation wrapper | Python API docs need regeneration | Run `scripts/generate-api-docs.sh --python` from this sub-skill or the documented site npm API-generation script if the checkout exposes one. |
| API generation wrapper | TypeScript API docs need regeneration | Run `scripts/generate-api-docs.sh --typescript` from this sub-skill or the documented site npm API-generation script if the checkout exposes one. |
| Known-route refresh | Known route coverage needs fresh sitemap data | Prefer a site package script that owns route refresh; if the checkout lacks one, inspect the current checkout before constructing a one-off command. |
| Language-index migration | Targeted language-index card migration is explicitly requested | Do not run a source migration helper from this skill by default; inspect the current checkout and create a task-specific command only after confirming the migration still applies. |
| Quickstart migration | Targeted quickstart overview card migration is explicitly requested | Do not run a source migration helper from this skill by default; inspect the current checkout and create a task-specific command only after confirming the migration still applies. |

Do not run migration helpers casually. They target specific historical markup
patterns and should produce a small, expected diff. If a helper is not bundled
here, treat it as source evidence, not as a default runtime dependency.

## When to route elsewhere

- SDK implementation details, new API behavior, or provider internals: route to
  python-sdk or typescript-sdk.
- docs-search MCP server runtime: route to mcp-server.
- A docs request that is really a backlog or strategy question: use docs-planner
  before writing pages.
