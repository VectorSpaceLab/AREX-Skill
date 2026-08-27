# Editing and Versioning

## Purpose

Read this while editing the existing skill. Keep the update narrow, self-contained, and compatible with the current skill structure.

## Preserve Stable Identity

Keep existing root and sub-skill directory names and frontmatter `name` values unless the user explicitly requested a rename or the current values violate the skill-id rules.

Every `SKILL.md` frontmatter block must remain valid:

```markdown
---
name: skill-id
description: "Triggering description broad enough for natural user requests."
disable-model-invocation: true
metadata:
  disco-role: operating
---
```

Preserve or add `disable-model-invocation: true` on repo root and sub-skill
frontmatter so imported repo skills stay behind `repo-skills-router` in
compatible agents. Do not add it to `repo-skills-router` itself; Codex target
visibility is handled during `import-repo-skills-to-agent`.
Preserve or add `metadata.disco-role: operating` on the same files so they are
available in Researcher mode and excluded from Creator mode.

## Edit The Working Runtime Tree

Edit in place only when the resolved tree is a source directory outside the live
DisCo skills root. If the starting point was
`<agent-dir>/skills/repositories/repo-skills/<skill-id>/`, edit its external working copy and
leave the live tree unchanged until the dedicated importer replaces it under the
global lock.

Prefer these edit actions, in order:

1. Add a route or decision point to the nearest existing `SKILL.md`.
2. Extend the nearest existing reference file when it already owns the topic.
3. Add a new focused reference when the topic is substantial enough to need its own file.
4. Add a safe reusable script when the workflow benefits from deterministic checks, inspection, conversion, validation, or smoke testing.
5. Add a new sub-skill only when the requested capability has distinct triggers, workflows, references, or scripts that would overload existing sub-skills.

Avoid broad rewrites, unrelated style churn, and moving content only for aesthetics.

## Maintain Self-Containment

Any instruction that would make a future agent open the original repo should be replaced with bundled content:

- Distill docs into `references/*.md`.
- Adapt safe examples into `scripts/`.
- Copy small schemas or config templates only when they are needed and public.
- Summarize large notebooks or training scripts into reproducible recipes.

When a source repo script is unsafe, too large, or environment-specific, extract the reusable logic into a smaller skill script or describe the necessary steps in a reference.

For every source repo script, example, notebook, tool, or config that the
extended skill tells future agents to run, read, or adapt, add or update one
skill-owned replacement and link that replacement from the nearest `SKILL.md`.
Do not use Markdown links that point outside the runtime skill directory, such
as `../scripts/foo.py`, `../../examples/bar.py`, or an absolute checkout path.

## Update Usability Tests

For each meaningful extension:

- Add at least one new case that targets the new capability.
- Add or update at least one regression-sensitive case for an existing capability that could be affected by the edit.
- Keep `user_request.txt` directly copyable with no labels, headings, or test metadata.
- Update `index.md` so the case set reflects the new coverage.

If the skill has no existing test-case directory, create one under the
review/test artifact directory using the same shape required by
`create-repo-skill`.

## Version Notes

When useful, add a short extension note outside runtime skill docs, such as in
the final handoff or the review package under the review/test artifact
directory:

- Changed files.
- Added capabilities.
- Removed stale guidance, if any.
- New or updated usability cases.
- Verification status.

Do not put development history inside `SKILL.md` unless it directly helps future agents choose correct behavior.
