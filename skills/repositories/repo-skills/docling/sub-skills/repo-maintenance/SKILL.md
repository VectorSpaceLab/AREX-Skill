---
name: repo-maintenance
description: "Guide safe Docling repository edits across package layout, extras,
  CLI docs, examples, validation, tests, and maintenance scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Maintenance

Use this sub-skill when modifying the Docling repository itself: package metadata, extras, CLI entry points, generated docs/examples, tests, CI-aligned checks, AGENTS guidance, Makefile commands, Tach boundaries, or maintenance scripts.

Do not use this sub-skill for ordinary document conversion, output export, pipeline tuning, remote service usage, extraction, chunking, ASR, VLM, or end-user CLI recipes. Route those requests to the user-facing Docling sub-skills instead.

## Fast Routing

- Start from `AGENTS.md` guidance: keep edits scoped, public APIs typed for Python `>=3.10,<4`, prefer `Path`, avoid broad attribute probing, and add focused tests only for meaningful behavior changes.
- Treat `docling-slim` as the source package that ships the `docling/` module plus `docling` and `docling-tools` CLI entry points; treat `docling` as the full dependency meta-package that re-declares the same scripts for tool installation.
- Use `make check` for read-only local checks and `make validate` before completion; rerun `make validate` if hooks mutate files.
- Run `make docs-render` after CLI or example notebook changes, and `make docs-build` when docs site integration matters.
- Use targeted `uv run pytest ...` first, then broader checks as confidence increases; regenerate reference data only when output changes are intentional.

## References

- `references/package-layout.md`: package split, extras mapping, CLI entry point ownership, dependency drift checks, and collision hazards.
- `references/maintainer-workflows.md`: contributor workflows for CLI flag changes, backend edits, docs/examples generation, tests, validation, CI, and source-script inventory.
- `references/troubleshooting.md`: common repository maintenance failures and focused recovery steps.
- `scripts/check_max_lines.py`: bundled safe equivalent of the repository line-limit guard; run from a checkout root with `python scripts/check_max_lines.py` or pass explicit files.

## Contributor Safety

- Keep runtime skill content self-contained; do not require future agents to open local source paths.
- Do not add new optional dependencies without updating the relevant slim extras, full-package re-export extras when applicable, tests, and docs/CLI guidance.
- Avoid growing accepted long-file debt; split new code or update ignore patterns only with a deliberate reason.
- When changing conversion behavior, prefer focused tests such as backend-specific tests, CLI tests, service client tests, or API smoke tests rather than broad snapshot churn.
