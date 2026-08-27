# Troubleshooting Repository Changes

Use this reference when a TRL repository edit fails review, tests, linting, or policy checks.

## Duplicated Trainer Blocks Drifted

Symptoms:

- A reviewer says GRPO, RLOO, or an experimental trainer changed differently.
- Similar methods have different variable names, branch order, or comments after the edit.
- Metrics or callback state names diverge without a trainer-specific reason.

Fix:

1. Search for the edited method name, distinctive comments, and state variables across `trl/trainer/` and `trl/experimental/`.
2. Align identical logic word-for-word where semantics match.
3. Keep only meaningful trainer-specific differences, such as whether log probabilities are returned or discarded.
4. Add or update targeted tests for every trainer family whose copied block changed.

Do not introduce a shared helper merely to enforce consistency; TRL intentionally keeps trainers self-contained.

## Missing Paper Index Update

Symptoms:

- A new algorithm, loss, trainer, or paper recipe is implemented but docs review flags missing paper coverage.
- The docs mention a paper but `docs/source/paper_index.md` does not.
- A paper link uses an arXiv URL instead of a Hugging Face paper URL.

Fix:

1. Add a subsection under the relevant method heading, or create a clear new heading if no section fits.
2. Use `https://huggingface.co/papers/<id>` for the paper link.
3. Summarize what the paper contributes and how TRL exposes it.
4. Include a minimal configuration snippet only for supported settings.
5. Explicitly note unsupported paper components rather than implying full reproduction.

## Wrong Docstring Style

Symptoms:

- Docstrings use Google-style `param (type):`, NumPy sections, or untyped prose.
- Optional parameters are not marked `*optional*`.
- Defaults are written inconsistently.
- Class references use raw names instead of Hugging Face autodoc links.

Fix:

- Use `param (`type`, *optional*, defaults to `value`):` formatting.
- Use `or` for unions.
- Prefer `(`str`, *optional*)` for a `None` default when the default is obvious from the signature.
- Use links like ``[`~transformers.PreTrainedModel`]`` for external classes.
- Keep examples short and fenced as Python.

Do not reformat unrelated docstrings while fixing one local issue.

## Main vs Experimental Boundary Problems

Symptoms:

- A broad refactor lands in `trl/experimental/` without need.
- Experimental code is promoted or exposed publicly without docs and tests.
- Main trainer behavior changes with only experimental tests.

Fix:

- For main code, add stable docs and focused tests before broadening exposure.
- For experimental code, keep changes local and consistent with nearby patterns.
- If moving functionality between namespaces, update imports, documentation, dataset-format tables, tests, and migration notes as needed.
- Avoid changing public defaults unless the task explicitly calls for migration work.

## Tests Are Too Broad Or Too Narrow

Symptoms:

- Validation starts with a full suite and failures are hard to triage.
- Only the edited file's tests ran even though copied logic changed elsewhere.
- Invariant tests fail after a trainer-loop change.

Fix:

1. Start with the closest test file for the changed module.
2. Add sibling trainer tests when duplicated logic changed.
3. Add CLI tests when command arguments or packaged skills changed.
4. Add distributed/vLLM tests only when those paths are touched.
5. Treat invariant failures as potential trajectory regressions; update snapshots only with explicit justification.

## Packaged Skill Changes Fail Discovery

Symptoms:

- `list_skills` does not show the skill.
- `install_skill` cannot copy the skill.
- CLI skill tests fail after a directory or frontmatter change.

Fix:

- Ensure each skill is a directory with a `SKILL.md` file.
- Keep frontmatter valid YAML with a clear `name` and quoted `description`.
- Do not add generated artifacts, local paths, or environment-specific instructions to runtime skill files.
- Update skill tests if install/list behavior or skill names intentionally changed.

## Over-Abstracted Or Defensive Code

Symptoms:

- Review asks why a registry, factory, fallback branch, `hasattr`, or `getattr` was added.
- A change handles hypothetical versions or unsupported inputs not present in TRL.
- A helper hides trainer flow that was previously readable top-to-bottom.

Fix:

- Inline the common path unless an existing abstraction already owns the behavior.
- Remove speculative fallbacks.
- Use explicit version comparisons only when the repository has an actual version boundary to support.
- Keep trainer files readable in isolation, even if that means duplicated code.
