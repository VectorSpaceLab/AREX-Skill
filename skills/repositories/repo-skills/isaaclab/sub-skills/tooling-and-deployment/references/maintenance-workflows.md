# Maintenance Workflows

## Installation and inspection

The root skill handles the main install helper and import smoke checks. Use the maintainer workflow when you need to reason about package structure, extra groups, or repo-level setup commands.

## Documentation

- Build the docs with the repository's docs wrapper.
- Use docs builds after public API or workflow changes.
- Keep generated public API docs synchronized with any new public symbols that are intended to be part of the user-facing package.

## Tests and formatting

- Run formatting/lint hooks before merging maintained changes.
- Run the targeted test file that covers the behavior you changed instead of the entire suite when possible.
- Prefer focused maintainer checks over repo-wide heavy runs unless the task explicitly requires them.

## Scaffolding

- Use the repo wrapper for task or project scaffolding when creating new examples or templates.
- Keep scaffolded output isolated from the skill tree.

## Release-adjacent maintenance

- Add changelog fragments rather than editing compiled changelog files directly.
- Use the package metadata and documented extras when deciding whether a change affects runtime or only maintenance behavior.
- Treat deployment helpers as maintainership tools when they do not represent a safe end-user runtime workflow.
