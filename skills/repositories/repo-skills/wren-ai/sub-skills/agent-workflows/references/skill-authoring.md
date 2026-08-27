# Authoring a Wren CLI-Served Guide

## When to read

Read this while maintaining WrenAI itself and adding or changing a guide
returned by `wren skills get`.

## Placement rule

A CLI-served guide is package data under the `wren` package's skill-content
area. A repository-root discovery-stub directory is not the place for new
workflow content; it only teaches compatible clients to find the CLI.

A guide has this logical shape:

```text
<guide-name>/
  SKILL.md
  references/     # optional detail delivered by --full
  scripts/        # optional helpers delivered by --script
```

The guide directory and `name` frontmatter use lowercase hyphenated names.
Keep the primary guide procedural and move long tables/references into bundled
files.

## Delivery contract

- `wren skills list` enumerates available guide directories.
- `wren skills get <name>` returns the guide body.
- `wren skills get <name> --full` appends bundled markdown references.
- `wren skills get <name> --script <stem>` prints a bundled helper script.

Add or update a focused skills CLI test when changing delivery behavior. Test
names, references, and script stems through the CLI rather than assuming a file
will be packaged.

## Content rules

- Include explicit trigger language and safe workflow ordering.
- Do not make the guide depend on an original checkout being available after
  package installation.
- Keep credentials out of examples and direct users to environment-backed
  configuration.
- When a workflow can make destructive or public changes, require a confirmation
  step near the actual operation.
