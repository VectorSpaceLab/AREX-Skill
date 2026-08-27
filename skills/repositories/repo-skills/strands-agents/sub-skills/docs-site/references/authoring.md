# Authoring rules

Use these rules when changing documentation content, metadata, examples, or
cross-references in the site.

## Frontmatter

Every docs page needs:

```yaml
---
title: "Page title"
description: "One sentence that explains what the page helps the reader do."
---
```

Allowed optional fields include `languages`, `community`, `experimental`,
`category`, `integrationType`, `redirectFrom`, `tags`, and `sourceLinks`.
Do not invent fields. Unknown frontmatter is not a reliable storage place and
can disappear during schema processing.

Rules that catch common failures:

- Omit `languages` when a feature is available in both supported SDKs.
- Use `languages: python` or `languages: typescript` only for a one-language
  page or feature. Do not list both supported languages.
- Use `community: true` for community-contributed pages and `experimental: true`
  for experimental features. The site renders those banners automatically.
- Use `sourceLinks` for implementation pointers that should appear on headless
  surfaces. Keep them repo-relative and update them in the same change as a
  source move or rename.
- Use `redirectFrom` when a page moved and the old slug should redirect.

## Tabs, Tab, and Syntax

`Tabs`, `Tab`, and `Syntax` are auto-imported in docs pages.

- Use `<Tabs>` with `<Tab label="...">` for multi-line examples or language-
  specific blocks.
- Do not use `TabItem` in docs pages. It is the Starlight component name, not
  the site authoring convention.
- Keep shared prose between tabs language-neutral.
- Use `<Syntax py="..." ts="..." />` for a single language-specific identifier
  in shared prose.
- Keep headings conceptual. Do not put parameter names or language names in
  headings just because one tab differs.
- Do not start tab content with a blank line.

Example shape:

````mdx
Use <Syntax py="retry_strategy" ts="retryStrategy" /> to configure retries.

<Tabs>
  <Tab label="Python">
    ```python
    from strands import Agent

    agent = Agent()
    ```
  </Tab>
  <Tab label="TypeScript">
    ```typescript
    --8<-- "path/to/example_imports.ts:agent_imports"

    --8<-- "path/to/example.ts:agent_body"
    ```
  </Tab>
</Tabs>
````

## Snippet includes

TypeScript examples live in runnable snippet files and are included into MDX
with MkDocs-style snippet markers.

- Put imports in a sibling `*_imports.ts` file unless the snippet has no
  external imports.
- Put the body in a sibling `.ts` file. Wrap bodies in functions when repeated
  identifiers would collide under `isolatedModules`.
- Put the imports include and body include inside one code fence so the rendered
  block is copy-pasteable.
- Use `snake_case` snippet names. Use `_imports` for import-only regions.
- Put `// --8<-- [start:name]` and `// --8<-- [end:name]` on their own lines.
- Paths in snippet directives resolve relative to the docs content root.
- The plugin dedents extracted sections. A missing file or section renders a
  diagnostic line in the generated code block and should be fixed before handoff.

Python snippets may be inlined when that keeps the example clearer. They still
need imports, setup, and realistic values.

## Links and API shorthand

- Use relative file links for docs-to-docs references. The site resolves file
  paths to slugs at render time.
- Use `@api/python/...` and `@api/typescript/...` for generated API reference
  pages. This is more stable than relative paths into API folders.
- Preserve anchors when converting API links.
- Avoid hard-coded absolute site paths unless the link is intentionally outside
  the docs collection.
- If a page moves, update neighboring relative links and any `redirectFrom`
  entries or known routes needed for old URLs.

## Generated API docs

Generated API docs are build artifacts exposed through `_generated` symlinks.
Do not edit those files directly.

- Python API docs are generated from Python SDK source into the Python API build
  output.
- TypeScript API docs are generated with TypeDoc, post-processed into MDX, and
  grouped by frontmatter category.
- Permanent API index pages import the API list components; the per-symbol or
  per-module pages are generated.
- If the generated output is wrong, fix the source or generator and regenerate.

## Code verification

Code examples must be accurate before review.

- Verify imports, constructor parameters, method names, return shapes, and
  language-specific spelling against the current SDK source.
- Verify Python and TypeScript independently. Do not translate names by guess.
- TypeScript snippet typecheck catches syntax and export mistakes, but it does
  not prove that surrounding prose claims are true.
- If no source, package, or test evidence is available, omit the example or
  surface the verification gap. Do not ship plausible code.

## Voice and terminology

- Use one canonical term for each concept. Do not vary wording for style.
- Lead with the developer's goal in tutorials, how-to guides, explanations, and
  troubleshooting sections.
- Avoid hype, filler, em dashes, and emoji.
- Use callouts only when the information needs to break the reader's flow.
- Keep files under the docs content tree to a 90-character line length, including
  template literal contents in snippet files. Prettier does not enforce this
  fully.
