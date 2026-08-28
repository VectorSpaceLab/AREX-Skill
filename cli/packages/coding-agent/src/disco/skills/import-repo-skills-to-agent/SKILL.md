---
name: import-repo-skills-to-agent
description: "Export all or selected DisCo-managed repository skills, their regenerated repository-index.jsonl, and a scoped area/family repo-skills-router into Codex, Claude Code, or another agent skills directory. Use when the user asks to copy, install, synchronize, or merge repository skills into another agent or project. Resolve exact skill IDs, obtain explicit approval for replacements, then use the bundled transactional helper for validation, Codex policy injection, deterministic router merging, rollback, and resume."
metadata:
  disco-role: meta
---

# Import Repo Skills To Agent

Export DisCo's managed repository-skill collection to another agent only when
the user explicitly requests a cross-agent export. DisCo already uses its live
collection through `repo-skills-router` and explicit `/skill:<name>`
invocation; it does not need this workflow for its own runtime.

Use the bundled helper for every filesystem mutation:

```text
scripts/export_repo_skills_to_agent.mjs
```

Do not manually copy skills, concatenate indexes, or merge generated router
Markdown.

## Collection layout

Treat the source collection root as the directory containing these siblings:

```text
<disco-agent-root>/skills/repositories/
├── repo-skills/
│   ├── <skill-id>/
│   └── repository-index.jsonl
└── repo-skills-router/
```

The default source agent root is `$DISCO_CODING_AGENT_DIR` when set, otherwise
`~/.disco/agent`. The target uses the same collection shape below its skills
root:

```text
<target-skills-root>/repositories/
├── repo-skills/
│   ├── <skill-id>/
│   └── repository-index.jsonl
└── repo-skills-router/
```

Keep unrelated target skills outside `repositories/` unchanged.

## Resolve the target

Prefer an unambiguous target argument:

- Use `--target-skills-root <dir>` when the path is already a skills root,
  such as `~/.agents/skills` or `~/.claude/skills`.
- Use `--target-agent-dir <dir>` when the path is an agent root; the helper
  appends `skills/repositories`.
- Use `--target <dir> --target-kind skills-root|agent-root` for a generic path.
- Allow `--target` with automatic inference only when the basename or existing
  layout makes the meaning unambiguous.

For Codex, default an agent-only request to the current user-level agent root
`~/.agents`, not the legacy `~/.codex`. Pass `--target-agent codex`. For Claude
Code or a generic target, pass `--target-agent agent-neutral` unless that
target explicitly requires Codex policy metadata.

## Resolve the selection

The helper accepts exact repository skill IDs. Before invoking it:

1. Read the source `repo-skills/repository-index.jsonl` and direct
   `repo-skills/<skill-id>/SKILL.md` files.
2. Resolve user terms, repository names, aliases, or wildcards to exact
   `skill_id` values.
3. Show the matched IDs when the request is ambiguous or a wildcard expands to
   more than the user likely expects.
4. Omit `--include-skill` for a full export. Repeat it, or pass comma-separated
   IDs, for a subset.

Do not select review artifacts, test outputs, environments, sessions, prompts,
or directories outside the managed `repo-skills/` collection.

## Resolve conflicts before mutation

Inspect the target collection before starting the helper. For every selected
skill ID already present under target `repositories/repo-skills/`:

1. Summarize the source and target paths and the relevant identity difference.
2. Ask whether to replace that exact target skill.
3. Pass `--overwrite-skill <skill-id>` only for approved replacements.
4. Exclude a declined skill from the selected export and report it as skipped.

Never silently overwrite a repository skill. The helper independently rejects
an unapproved conflict and refuses repository-identity collisions.

## Run the transaction

For a selected Codex export:

```bash
node <this-skill>/scripts/export_repo_skills_to_agent.mjs \
  --source-agent-dir <disco-agent-root> \
  --target-agent-dir ~/.agents \
  --target-agent codex \
  --include-skill <skill-id> \
  --overwrite-skill <approved-skill-id>
```

For a full agent-neutral export to an exact skills root:

```bash
node <this-skill>/scripts/export_repo_skills_to_agent.mjs \
  --source-agent-dir <disco-agent-root> \
  --target-skills-root <target-skills-root> \
  --target-agent agent-neutral
```

The helper performs one deterministic workflow:

1. Validate source and existing target paths, symlink safety, skill identity,
   v2 `references/repo-routing-metadata.json`, exact taxonomy assignments, and
   source/target non-overlap.
2. Generate a filtered source router for the selected skills without modifying
   the source collection.
3. Merge selected source records with unrelated target records by canonical
   `skill_id` and `owner/repository` identity.
4. Stage the final `repo-skills/` tree.
5. For a Codex target, add or update `agents/openai.yaml` beside every root and
   descendant `SKILL.md` in the staged non-router repository skills, setting
   `policy.allow_implicit_invocation: false` while preserving unrelated OpenAI
   metadata. Never add this policy to `repo-skills-router`.
6. Regenerate `repo-skills/repository-index.jsonl` and the sibling router from
   the final merged records. Do not copy a stale source root index or combine
   Markdown pages.
7. Revalidate taxonomy paths, links, repository and assignment
   indexes, router visibility, selected/unselected boundaries, and Codex
   policy before touching the live target.
8. Replace only target `repositories/repo-skills/` and
   `repositories/repo-skills-router/` through the persisted transaction.
9. Validate the installed target and commit, or restore the exact previous
   target if a post-mutation step fails.

The final root `repository-index.jsonl` must be byte-for-byte consistent with
`repo-skills-router/references/index/repositories.jsonl`. A subset export must
not leak unselected source skills into either index or any generated area or
family page. Existing unrelated target repository skills and assignments must
remain present.

## Index and visibility contract

The long-lived repository indexes intentionally do not store a per-repository
skill `content_sha256`. They preserve repository identity, provenance, routing
assignments, and descriptions; their complete-file integrity is protected by
the router's `build-metadata.json` index digests. The import handoff may still
contain a one-time `skill_content_sha256`, which is checked while importing the
verified runtime tree and is not copied into either long-lived repository index.

Target-specific `agents/openai.yaml` files are still excluded from the
handoff's portable-tree digest. Do not ignore arbitrary extra files, symlinks,
or non-regular entries.

Keep `repo-skills-router` model-visible for a fresh target. Preserve an
existing target router's visibility by default; use
`--router-visibility enabled|disabled` only when the user explicitly asks to
change it. Repository skills remain hidden from implicit selection through
their portable frontmatter and, for Codex targets, the target-only OpenAI
policy.

## Recover an interrupted export

The helper prints the persisted transaction directory on failure. Its
manifest stores both the selected index fingerprint and a transaction-only
snapshot of the selected source skill trees. This keeps interrupted exports
safe without reintroducing a per-repository digest into the long-lived
indexes. Resume or retry exactly that transaction with:

```bash
node <this-skill>/scripts/export_repo_skills_to_agent.mjs \
  --resume <transaction-directory>
```

Do not manually repair a partial target. The helper restores any mutation
phase to the recorded target snapshot, then reuses the persisted source,
selection, overwrite approvals, target policy, and router visibility. For a
validated pre-mutation transaction, it revalidates the source fingerprint,
target snapshot, and staging before committing it.
Arguments do not need to be repeated; any explicitly repeated argument must
match the manifest or resume stops before mutation.

If rollback cannot restore the exact recorded target snapshot, preserve the
reported staging and backup paths and stop for manual inspection.

## Safety and handoff

- Keep the source collection read-only.
- Reject source/target overlap and paths that traverse symlinks.
- Do not import a structurally invalid selected skill or infer missing routing
  metadata.
- Do not delete unrelated target skills or assignments.
- Do not add Codex policy to the router.
- Do not report success until live target validation and transaction commit
  both complete.

Report the resolved source and target, exact selected IDs, copied and approved
replacement counts, final repository and assignment counts, router action,
Codex policy mode, and any skipped conflicts. If the target agent caches skill
discovery, tell the user to restart or reload it.
