---
name: repo-development
description: "Modify the TRL repository safely as a contributor or maintainer,
  including trainer consistency, docs, tests, and packaged skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TRL Repo Development

Use this sub-skill when changing the TRL codebase itself: trainer internals, configs, docs, tests, packaged skills, or contribution hygiene. Do not use it for end-user training runs; route usage questions to the training-oriented TRL skills instead.

## Route By Change Type

- **Trainer or config edits**: follow [contributor guidance](references/contributor-guidance.md) before changing `trl/trainer/` or `trl/experimental/`; duplicated trainer logic must stay aligned across copies.
- **Paper-method additions**: add the implementation, docs, targeted tests, and a `docs/source/paper_index.md` subsection for the method or algorithm.
- **Docs or public API docs**: use TRL docstring style and Hugging Face paper links; keep examples small and runnable.
- **Test planning**: choose the narrowest relevant unit, CLI, distributed, or invariant tests using [test selection](references/test-selection.md).
- **Packaged skill changes**: update bundled skill content and the skill install/list tests together so installed skills remain discoverable.
- **Unexpected review failures**: diagnose common repository-policy issues with [troubleshooting](references/troubleshooting.md).

## Safety Rules

- Preserve self-contained trainers. Do not introduce shared abstractions for generation, reward computation, metric logging, or weight syncing just to remove duplication.
- When editing duplicated logic, update every matching trainer block with the same variable names, branch order, and comments unless trainer semantics require a documented difference.
- Keep main code stable and well-tested; keep experimental edits small and non-invasive unless the task explicitly targets experimental development.
- Prefer direct, lean changes over registries, factories, broad fallbacks, or speculative compatibility branches.
- Run only the tests needed for confidence first, then broaden if the change touches shared behavior or public interfaces.

## Quick Checklists

- **Duplicated vLLM logic**: compare online trainers that share `_generate_single_turn`, weight-sync state, and vLLM branches; propagate the same structural edit across GRPO/RLOO and relevant experimental online trainers.
- **New paper trainer**: add trainer/config files, expose imports/CLI docs as appropriate, add targeted tests, document user-facing behavior, and update `docs/source/paper_index.md` with a Hugging Face paper URL.
- **Docstring/API change**: use backticked types, `*optional*`, `defaults to ...`, `or` unions, and Transformers reference links in the repository style.
- **Skill packaging change**: keep `SKILL.md` frontmatter valid, preserve installable directory structure, and cover discovery/install behavior in skill tests.
