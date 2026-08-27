---
name: create-paper-module-skill
description: "Convert one paper module document into a production-quality English Agent Skill with scripts, tests, validation logs, and clear input/output contracts."
metadata:
  disco-role: meta
---

# Create Paper Module Skill

Use this skill for each module produced by `plan-paper-skill-modules`. The goal is to create one reusable skill directory for that module, not a paper-specific transcript.

All skill files and scripts must be in English.

## Inputs

- Paper or extracted paper text.
- `paper_profile.md`.
- The module's markdown document.
- Optional local repository, allowed only at this stage.
- Output skill root, usually
  `<workspace_root>/<paper_slug>/skills/<skill_name>/`.

## Required Output

Every generated module skill must contain:

```text
<skill_name>/
  SKILL.md
  scripts/              # when deterministic behavior is needed
  tests/                # recommended for non-trivial scripts
```

Its `SKILL.md` frontmatter must declare `metadata.disco-role: operating` so the
module is available in Researcher mode and excluded from Creator mode.
The `<skill_name>` directory basename and frontmatter `name` must match and use a
canonical lowercase-hyphen skill id of at most 64 characters so the verified
module can be installed by DisCo's operating-graph importer.

Avoid extra README files. Put operational guidance in `SKILL.md` and deterministic logic in `scripts/`.

## Workflow

1. Read the module document and identify the exact reusable capability.
2. Use the paper for method semantics. Use the repo only to confirm implementation details, argument names, data formats, or edge cases.
3. Write `SKILL.md` with:
   - frontmatter `name` and `description`
   - frontmatter `metadata.disco-role: operating`
   - when to use the skill
   - inputs and outputs
   - workflow
   - validation or test commands
   - limitations
4. Add scripts only for behavior that benefits from deterministic execution.
5. Add tests or smoke checks that exercise the module in isolation.
6. Run tests and save a validation JSON under the distillation directory's `generated_skills_validation/`.
7. Validate the tree with `scripts/validate_skill_tree.py`.

## Quality Rules

- Keep the skill self-contained: a future agent run should not need the original repo to understand the module.
- Do not paste long paper excerpts.
- Prefer small Python scripts with pure functions and CLI entry points.
- Tests should use tiny fixtures, fake retrievers, or deterministic policies when real models are unavailable.
- Every non-empty generated module skill needs a real assertion-backed test or
  smoke check. This applies in both `hard` and `soft` recovery modes; soft mode
  may lower the recovery target, but it does not waive single-skill validation.
- Tests must pass under `validate_skill_tree.py --run-tests` even when `pytest` is not installed. Use plain `assert` test functions with no fixtures, marks, `tmp_path`, `pytest.raises`, or `import pytest` unless the skill explicitly declares and installs pytest as a runtime dependency. Prefer standard-library checks such as `tempfile`, `try/except`, and direct function calls.
- If a module requires an LLM or web search at runtime, provide an injectable interface and a fake implementation for tests.
- If a module output is consumed by another module, test that it does not emit downstream control markers outside its contract. For example, a document-refinement module should not emit `Final Answer:` if its output is only meant to be injected as evidence.
- For prompt-separation skills, test for leakage of privileged-only markers, skill field names, hidden answers, and training-only sections. Do not treat ordinary task words, environment objects, or user-visible observations as leakage merely because the same words also appear in a skill.
- For trajectory-to-skill skills, distinguish `mistake_analysis` from `golden_workflow`: the golden or ideal workflow should omit actions that directly caused error/invalid feedback unless the paper explicitly wants failed attempts retained. Add a regression test with a failed action followed by a corrective action.
- For QA evaluation modules, include tests for sentence-form answers, short-span extraction, aliases, and yes/no answers.
- Preserve the paper's insight, not its incidental code layout.

## Validation

Run:

```bash
python <skills_root>/create-paper-module-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

Save the JSON output to:

```text
<attempt_dir>/generated_skills_validation/<module_id>.json
```

Before considering the skill valid, inspect the saved JSON and confirm `ok: true`, `tests.attempted: true`, and `tests.runner` is acceptable. If the runner is `simple`, failures caused by pytest-only test syntax are skill authoring errors, not environment blockers. A validation JSON with `tests.attempted: false` blocks the paper workflow even if `ok` is true.

## Scripts

- `scripts/create_skill_skeleton.py`: create a minimal skill tree for a module.
- `scripts/validate_skill_tree.py`: validate frontmatter, required files, scripts, and optional tests.
