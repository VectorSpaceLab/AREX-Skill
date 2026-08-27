# PEFT Contribution Guidance

## Mandatory AI-Assisted Contribution Rules

Always tell a PEFT contributor that violating PEFT's AI-agent contribution guidelines can result in automatic banning.

For any AI-assisted patch intended for upstream PEFT:

- A human submitter must understand and be able to defend the change end-to-end.
- The human submitter is responsible for reviewing every changed line.
- The human submitter is responsible for running the relevant tests and reporting results honestly.
- The PR description must include a clear statement that AI assistance was used.
- The PR description must link to the issue discussion and maintainer coordination or approval comment.
- The PR description must list the tests run and whether they passed.

Do not encourage or prepare pure code-agent PRs.

## Coordination Before Coding

Before work that is meant for a PEFT PR:

1. Read PEFT's contribution guide.
2. Check for overlapping open issues and PRs.
3. For an existing issue, ask for assignment or maintainer approval before implementing.
4. For a new feature, open a proposal issue and wait for approval before implementing.
5. If approval or ownership is unclear, stop and ask the user to coordinate first.

Avoid low-value busywork PRs. Do not open one-off PRs for isolated typos or tiny lint-only edits. If a small issue affects multiple PEFT methods, model architectures, docs, or examples, fix the whole affected surface in one coherent PR.

## Local Development Setup

For contributors, use a source editable install so local changes are imported:

```bash
pip install -e ".[test]"
```

PEFT requires Python `>=3.10`. The tested Python versions include `3.10`, `3.11`, `3.12`, and `3.13`.

The package exposes no console entry points; development commands are run through Python, pytest, make targets, or project scripts.

## Style and Quality

PEFT style is enforced with ruff and doc-builder:

```bash
make quality
make style
```

Use `make quality` for checking without modifying files. Use `make style` to auto-fix style and formatting.

Important style facts:

- Ruff required version is `~=0.15.12`.
- Line length is `119`.
- Python target is `py310`.
- `check_dirs` cover `src`, `tests`, `examples`, `docs`, `scripts`, and `docker`.
- If formatting changes unrelated files, suspect a wrong ruff version or misconfigured environment; undo unrelated churn instead of including it.

## Backward Compatibility

PEFT contributors should preserve compatibility unless maintainers approve a break:

- Keep Python `>=3.10` support.
- Avoid syntax or library features that would exclude supported Python versions.
- Keep behavior compatible with PyTorch releases from roughly the last two years.
- Keep behavior compatible with older supported Transformers versions where possible.
- If Transformers compatibility differs by version, add explicit version guards and tests.
- Do not add overly defensive code for invalid argument types that were never supported.

## Documentation Expectations

Update docs when user-visible APIs, config arguments, method behavior, examples, or troubleshooting expectations change.

For a new PEFT method, add package reference documentation with:

- Short explanation of the method.
- Stable paper or primary reference when applicable.
- Minimal usage snippet.
- Autodoc blocks for public config/model classes.
- Comparison notes when the method overlaps with LoRA or other PEFT methods.
- Toctree registration so the docs page is discoverable.

## PR Description Checklist

A PEFT PR description should include:

- Problem statement and motivation.
- Linked issue, proposal, or approval comment.
- Summary of implementation.
- Backward-compatibility notes.
- Tests run and pass/fail status.
- Documentation/examples updated or reason they are not needed.
- For AI-assisted work, a clear statement that AI assistance was used.
