# Contributor Guidance

This reference is for agents modifying the TRL repository. It distills contribution policy, repository style, and maintainer expectations into practical editing rules.

## Repository Areas

- **Main package code** lives under `trl/` and should remain stable, simple, and well-tested.
- **Experimental code** lives under `trl/experimental/`; APIs may be less stable, but avoid broad refactors and prefer small consistency improvements.
- **Documentation** lives under `docs/source/`; public trainer docs usually pair narrative examples with autodoc sections.
- **Tests** live under `tests/`; main trainers have top-level tests, experimental trainers have `tests/experimental/`, distributed behavior has `tests/distributed/`, and trajectory checks have `tests/invariant/`.
- **Packaged skills** live under `trl/skills/`; skill install/list/uninstall behavior is tested by the skill test modules.

## Trainer Consistency Policy

TRL trainers are intentionally self-contained. Shared-looking blocks are duplicated so each trainer can be read and modified in isolation. Do not extract common helpers or base-class behavior merely to remove duplication.

When changing a repeated trainer pattern:

1. Identify all copies of the block before editing. Search by method names, variable names, comments, and branch labels.
2. Keep matching copies structurally aligned: same variable names, same branch order, same comments, and same metric-key style.
3. Preserve semantic differences explicitly. For example, one trainer may collect vLLM log probabilities while another intentionally discards them.
4. If one copy appears wrong, do not silently fix only that copy. Either make the same policy-level fix everywhere or report the cross-trainer issue.
5. Review generated metrics and callback state names after the edit; names such as `self._last_loaded_step` and `self._metrics[mode]` should remain consistent across trainers.

### vLLM Generation Changes

For generation or weight-sync changes, inspect all trainers with online generation paths before finalizing:

- Main online trainers such as GRPO and RLOO.
- Experimental online trainers that reuse similar vLLM/server/colocate patterns.
- Client/server utilities under TRL generation modules when the change affects shared transport behavior.
- Documentation that describes vLLM defaults, server mode, colocate mode, or version bounds.

A safe vLLM edit usually includes targeted trainer tests and, when user-facing options change, docs updates. Keep branch order and comments aligned across duplicated trainer methods.

## Paper Method Additions

If a change implements a method, algorithm, training approach, loss variant, or trainer from a research paper, update `docs/source/paper_index.md`. Use `https://huggingface.co/papers/<id>` links rather than arXiv URLs.

A paper-backed trainer change normally needs:

- Trainer and config implementation in the appropriate main or experimental namespace.
- Public imports only when the feature is intended to be public from that namespace.
- Documentation page or section with a minimal usage snippet.
- A `paper_index.md` subsection summarizing the paper and mapping paper settings to TRL arguments.
- Focused tests for config validation, data handling, loss/reward behavior, and any CLI or import surface.

Do not overstate unsupported paper features. If TRL implements only part of a paper recipe, document unsupported components clearly.

## Documentation Style

Docstrings must follow TRL's repository format:

- Use backticked types in parentheses, such as `(`str`)` or `(`int`, *optional*, defaults to `1`)`.
- Mark optional parameters with `*optional*`.
- For defaults, write `defaults to <value>`.
- For `None` defaults, prefer `(`str`, *optional*)` rather than a verbose `or None` default phrase.
- Use `or` for unions, not slash notation.
- Link classes using formats like ``[`~transformers.PreTrainedModel`]``.
- Keep examples in fenced Python blocks and small enough to understand quickly.

Do not convert existing docstrings to Google, NumPy, or another style as part of a local edit.

## Simplicity Expectations

TRL favors straightforward contributor-readable code:

- Prefer inline logic over registries, factories, plugin systems, or new base-class layers.
- Avoid defensive branches for situations that do not exist in the repository today.
- Avoid `hasattr` and `getattr` as version-probing or overly defensive compatibility workarounds; use explicit version comparisons when truly needed.
- Keep new helpers narrow and local. If a trainer is designed to be self-contained, repeated code is often the correct shape.

## Main vs Experimental Boundaries

Use the target namespace to decide how much stabilization is required:

- **Main code**: require stable docs, strong tests, consistent trainer patterns, and careful backward-compatibility review.
- **Experimental code**: APIs can move faster, but changes should still be readable, tested where practical, and consistent with nearby main patterns.
- **Promotion from experimental to main**: verify imports, docs navigation, dataset-format docs, tests, and migration notes if users must change code.

## Packaged Skills

When editing packaged TRL skills:

- Keep each skill as a directory containing `SKILL.md`.
- Preserve valid YAML frontmatter and a concise description.
- Update skill discovery or installation tests when changing names, install behavior, or directory layout.
- Do not put local machine paths, temporary environment details, or long-running maintainer scripts into skill runtime instructions.

## Review Before Handoff

Before declaring a repository-development change done, check:

- Duplicated trainer logic has been propagated or intentionally documented as divergent.
- Paper-backed changes update `docs/source/paper_index.md`.
- Docstrings use TRL style.
- Tests are selected narrowly and broadened only as needed.
- Experimental edits are not broad refactors.
- New files follow package style, import order, and line-length conventions from `pyproject.toml`.
