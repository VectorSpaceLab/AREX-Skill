---
name: import-repo-skills-to-agent
description: "Use this skill when the user asks to export DisCo's managed repository skills and repo-skills-router into another agent tool such as Codex under ~/.agents/skills, Claude Code under ~/.claude/skills, or a project-local agent directory. Handles canonical source and target layout, duplicate-skill overwrite questions, Codex policy, and repo-skills-router merging."
metadata:
  disco-role: meta
---

# Import Repo Skills To Agent

## Purpose

Use this workflow skill to copy DisCo's managed skill library into another
agent tool. The source library is DisCo's managed user directory:
`~/.disco/agent/skills/repositories/repo-skills/` with its sibling
`~/.disco/agent/skills/repositories/repo-skills-router/`, unless
`DISCO_CODING_AGENT_DIR` points to a different DisCo agent directory.

This skill is explicit cross-agent export/import behavior. DisCo already uses
the managed repo skills in `~/.disco/agent/skills/repositories/repo-skills/` at runtime through
`repo-skills-router` and explicit `/skill:<name>` invocation. Do not export to
another agent unless the user asks for that target.

## Inputs

The user may name an agent without a path, or provide a tool root such as:

- `Codex`
- `~/.agents`
- `~/.claude`
- `/path/to/project/.agents`

Resolve the target skills root as follows:

1. If the user says only `Codex`, default to the current standard user-level
   target `~/.agents/skills/`.
2. Expand `~` and environment variables in an explicit path.
3. If the path basename is `skills`, treat it as the exact target skills root.
4. If the path basename is `.agents` or `.claude`, use `<tool-root>/skills`.
5. Treat an explicitly requested `.codex` root as a legacy Codex target and use
   `<tool-root>/skills`; do not choose `~/.codex/skills` by default.
6. Create the target skills root only after confirming the source library is
   readable.

Treat the target as Codex when the user names `codex`, identifies an explicit
`.agents` path as a Codex target, names `$CODEX_HOME`, or explicitly requests a
legacy `.codex` path. If an `.agents` path is given without an agent type and
whether to write Codex policy affects the result, ask which target agent owns
that path before copying. For Codex targets,
non-router repo skills need an additional target-side `agents/openai.yaml`
policy file so Codex keeps their `description` out of the initial model-visible
skills list while leaving `repo-skills-router` visible.

## Source Selection

The user may import the whole managed repo-skill library or a selected subset.
Selection terms may be directory ids, `name` frontmatter values, package/repo
names mentioned in `references/repo-provenance.md`, or a comma/space-separated
list with shell-style `*` wildcards. Resolve selection against the inventory
before copying and show the matched skill ids in the import plan.

If the user names specific packages or skills, import only those matched
non-router skills plus `repo-skills-router` when at least one repo skill is
included. If the user does not provide a package/skill filter, import every
valid skill directory under the DisCo managed `repositories/repo-skills/` collection that
has a direct `SKILL.md`, plus the sibling `repo-skills-router` when present.

Do not import review/test artifact directories, envs, prompts, extensions,
themes, sessions, or workflow run state. The source is only:

```text
<disco-agent-dir>/skills/repositories/repo-skills/<skill-id>/SKILL.md
<disco-agent-dir>/skills/repositories/repo-skills/<skill-id>/**/*
<disco-agent-dir>/skills/repositories/repo-skills-router/**/*
```

If the sibling `repo-skills-router` is missing from the DisCo managed library root but
the bundled template is available, copy the bundled template into the import set
only when there are repo skills to route. Do not create an empty router as the
only imported skill unless the user explicitly asks for it.

## Pre-Import Validation

Before asking overwrite questions or copying files, refresh the DisCo managed
source library once by running
`verify-repo-skill/scripts/update_repo_skills_router.mjs --library-root
<disco-agent-dir>/skills/repositories`. This is source-library validation and a
deterministic router rebuild, not a target import side effect. Every managed
repo skill must already contain a valid v2
`references/repo-routing-metadata.json` produced and accepted by the
create/verify workflow. The updater and exporter must not synthesize or
backfill missing metadata. If a fragment is missing or invalid, stop and report
the skill id, source path, and exact validation reason instead of silently
skipping the skill or inferring assignments.

Then inspect every selected repo skill directory and the sibling router:

1. Read `<skill-id>/SKILL.md` and parse its frontmatter.
2. Require frontmatter `name` to be present, lowercase-hyphen, no longer than
   64 characters, and equal to the directory basename.
3. Require a non-empty `description` line wrapped in double quotes.
4. Require `metadata.disco-role: operating` in every selected root and
   descendant `SKILL.md`, including `repo-skills-router`. Do not synthesize a
   missing role while exporting; repair the DisCo-managed source first.
5. For every non-router repo skill, require
   `disable-model-invocation: true` in the root `SKILL.md` and in every
   `sub-skills/<id>/SKILL.md`. If the source omits it, normalize the copied
   target only when the user explicitly authorizes normalization; otherwise
   skip that skill and report the validation failure.
6. For `repo-skills-router`, require that `disable-model-invocation: true` is
   absent so the router remains model-visible in the target agent.
7. For every selected non-router repo skill, require the v2
   `references/repo-routing-metadata.json`. Validate its canonical
   `owner/repository` identity, taxonomy hash, exact area/family assignments,
   and `classified`/`unclassified` status. The full evidence handoff remains
   outside the runtime skill.

Do not require source repo skills to contain `agents/openai.yaml`. The source
library stays agent-neutral except for the existing Claude/DisCo
`disable-model-invocation` frontmatter. Add Codex-specific `agents/openai.yaml`
only to the copied target skill directories when the target is Codex.

Do not silently import invalid skills. Report validation failures by skill id,
source path, and exact reason. If the user selected a subset, a validation
failure in one selected skill should not block unrelated valid selections unless
the failed skill is required for the requested import.

## Duplicate Handling

Before copying, inspect `<target-skills-root>/repositories/repo-skills/` for
existing repo skill directories and
`<target-skills-root>/repositories/repo-skills-router/` for the router.
Compare by directory basename and by the `name` frontmatter field in
`SKILL.md`.

For each non-router source skill that conflicts with
`<target-skills-root>/repositories/repo-skills/<skill-id>/`:

1. Summarize the conflict using source path, target path, source frontmatter
   name, target frontmatter name, and a short evidence note if the contents look
   different.
2. Ask the user whether to overwrite the target copy. Use `ask_user_question`
   when available; otherwise ask in the conversation and wait.
3. If the user approves overwrite, replace only that target skill directory.
4. If the user declines overwrite, skip that skill and report it.

Never silently overwrite a non-router skill.

## Router Merge

Handle `repo-skills-router` as a generated area/family index, not as a free-form
Markdown document. The source router used for target import must be filtered
to the selected skills for a subset export, so an unselected source skill never
becomes visible in the target.

If the target already has `repo-skills-router`, merge the filtered source view
with the target router while preserving unrelated target skills and their exact
assignments. For a subset export, the source must be a filtered router for the selected import set; never merge the full DisCo router into a subset import.

For a subset import, build a temporary source-router view before touching the
target router:

```bash
node <disco-verify-skill>/scripts/update_repo_skills_router.mjs \
  --library-root <disco-agent-dir>/skills/repositories \
  --include-skill <selected-skill-id> \
  --output-router-dir <temp-dir>/repo-skills-router
```

 Repeat `--include-skill` or pass comma-separated ids for every non-router repo
 skill that will actually be copied or overwritten. Use this temporary router
 as the source for the target router. Do not copy the full
 `<disco-agent-dir>/skills/repositories/repo-skills-router/` directly for a subset import.

The generated router contains a root area map, area pages, family comparison
pages, and `references/index/{taxonomy,repositories,assignments,build-metadata}`.
For a full import, copy the complete generated tree. For a subset import,
replace or merge only the area/family/index view for the selected skills while
preserving unrelated target skills and their exact assignments. Do not merge
old scenario registries or scenario pages.

After merging, validate that every router repository link resolves to a copied
target skill, every assignment uses an exact taxonomy path, and no unselected
source skill appears in the target index.

## Copy Procedure

1. Resolve source and target paths.
2. Inventory source and target `repositories/repo-skills/` collections and
   sibling routers.
3. Apply any user-provided package/skill filters and validate the selected
   source skills before planning destructive operations.
4. Plan actions:
   - `copy`: target skill missing.
   - `overwrite`: target skill conflicts and user approved.
   - `skip`: user declined overwrite or source is invalid.
   - `merge-router`: both source and target have `repo-skills-router`.
5. Ask all required overwrite/merge conflict questions before making
   destructive changes.
6. Copy approved skills into `<target-skills-root>/repositories/repo-skills/<skill-id>/`.
   Prefer directory-level replacement for approved overwrites, preserving
   permissions when possible. Never flatten them into the target skills root.
7. If the target is Codex, run
   `scripts/apply_codex_openai_policy.py <target-skill-dir>...` for every
   copied or overwritten non-router repo skill directory. This writes
   `agents/openai.yaml` beside the root `SKILL.md` and every descendant
   `SKILL.md` under that skill directory with:

   ```yaml
   policy:
     allow_implicit_invocation: false
   ```

   If an `agents/openai.yaml` file already exists, preserve unrelated
   `interface`, `dependencies`, and other metadata while setting only
   `policy.allow_implicit_invocation` to `false`. Never run this on
   `repo-skills-router`, because it must remain the model-visible routing
   entry point. This is a target normalization step only; do not modify the
   DisCo source skill directory.
8. Build a filtered source `repo-skills-router` for the exact non-router repo
   skills that were approved for copy/overwrite, then merge or copy that
   filtered router to the sibling
   `<target-skills-root>/repositories/repo-skills-router/`.
9. Re-validate the target copy:
   - every copied root and descendant `SKILL.md` preserves
     `metadata.disco-role: operating`;
   - non-router repo skills still contain `disable-model-invocation: true`;
   - for Codex targets, each copied or overwritten non-router root skill and
     descendant skill contains `agents/openai.yaml` with
     `policy.allow_implicit_invocation: false`;
   - for Codex targets, `repo-skills-router` does not contain
     `agents/openai.yaml` with `policy.allow_implicit_invocation: false`;
   - `repo-skills-router` remains model-visible;
   - router links point to existing files;
   - selected skills are present and unselected skills were not modified;
   - the target router does not gain entries for unselected DisCo source
     skills, except for unrelated entries that already existed in the target
     router before this import.
10. Report imported, overwritten, skipped, merged items, and any Codex
    `agents/openai.yaml` files written with exact paths.

## Safety Checks

- Do not delete target skills that are not in the DisCo source library.
- Do not copy private envs, sessions, logs, auth files, package caches, or
  review/test artifacts.
- Do not write absolute local DisCo source paths into imported public skill
  content.
- If the target path is inside the DisCo source library root, stop and tell
  the user that source and target are the same library.
- If a target conflict cannot be understood because `SKILL.md` is unreadable,
  ask before overwriting.
- Do not make all repo skills model-visible in the target agent. The
  `repo-skills-router` skill is the model-visible entry point; imported
  non-router repo skills should be hidden from automatic model invocation and
  read only after router selection or explicit user request.
- For Codex targets, do not rely on `disable-model-invocation: true` alone.
  Codex uses `agents/openai.yaml` with
  `policy.allow_implicit_invocation: false` to keep non-router repo skill
  descriptions out of the initial model-visible skill list.
- Do not let subset import leak all DisCo-managed repo skills through
  `repo-skills-router`. The router content imported from DisCo must be scoped
  to the selected skills that are actually present in the target.

## Handoff

End with a concise import summary:

- source DisCo repo-skills collection and sibling router;
- target skills root;
- package/skill selection filters and matched skill ids;
- skills copied;
- skills overwritten after approval;
- skills skipped and validation or conflict reason;
- router action: copied, merged, unchanged, or unavailable;
- for Codex targets, number of `agents/openai.yaml` policy files written;
- any manual follow-up needed, such as restarting the target agent so it reloads
  skills.
