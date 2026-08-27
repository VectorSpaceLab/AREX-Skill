# Troubleshooting and safety

Use this reference before retrying a failed operation. Prefer read-only
inspection or a disposable fixture; do not “fix” a collision by deleting a
user-owned directory.

## Installer failures

### “Refusing to overwrite existing Codex skill … marker file not found”

This is the intended ownership refusal. Stop. Do not add the marker by hand,
rename the foreign directory, or delete it. Ask the owner whether to preserve
it, choose a different source/destination arrangement outside this workflow, or
perform a separately approved migration. The preflight runs before Claude
writes, so a clean refusal should not leave a new Claude command behind.

### A marked Codex skill is unexpectedly replaced

A marked destination is considered installer-owned. Rerunning install removes
that directory and copies the current source directory. Preserve any local
edits first, then reinstall only with user approval. The marker is not a
content-level backup and does not prove every file was originally created by
this version.

### Claude command changed or uninstall removed a custom file

Claude destinations have no ownership marker. Install always copies over an
existing same-named command; uninstall unlinks it if present. Treat Claude
files as replaceable only after the user reviews them. Do not infer that a
Claude file is safe to remove because the Codex counterpart is marked.

### Installation stopped after some files were written

The installer preflights Codex conflicts but does not provide rollback after
that point. It writes Claude commands before Codex skills and writes runtime
bundles after both. Record which destinations exist, resolve the underlying
error, and rerun only after approval. A temporary fixture is the preferred
place to reproduce copy or frontmatter errors.

### Invalid frontmatter or missing `SKILL.md`

Source discovery skips directories without `SKILL.md`. A discovered skill must
start with a YAML frontmatter block at the beginning of the file and the block
must parse to a mapping. Fix the source content or exclude that directory from
the source root. Do not hand-edit the Codex-rendered copy as a substitute:
reruns regenerate it.

Only the Codex allow-list (`name`, `description`, `license`, `allowed-tools`,
`metadata`) survives transformation. A source-only key disappearing from
Codex is expected; the Claude copy remains verbatim.

### Wrong number of installed skills

Run the read-only checker against the repository or its `skills/` root. It
checks the eight expected immediate source skills. Do not count `skills/disco`
or any child under it as one of the eight. If a nested active root is present,
report it separately and keep it as its own graph.

## Uninstall and ownership cases

### Uninstall leaves a Codex directory

That directory was unmarked, or its marker was removed. This is safe behavior:
uninstall does not remove an unowned destination. Preserve it and escalate to
its owner instead of adding a marker.

### Uninstall removes the runtime bundle unexpectedly

The runtime-bundle directory is removed by label for each agent home when it
exists; it has no marker gate. Review ownership before invoking uninstall. If a
bundle is shared with another project, do not use this uninstall path until the
shared ownership is resolved.

### The old skill is not selected for uninstall

Discovery is based on the current source set. If a skill was removed or
renamed from the current immediate source root, the uninstall loop will not
select its old command or Codex directory. Handle stale entries as a separate,
explicit cleanup decision; never broaden the loop to recursively scan nested
skill graphs.

## Active-root and source-content cases

### Nested `skills/disco` output is being merged

Stop the merge. A directory that contains a root `SKILL.md` and `sub-skills/`
is an active generated root. Use its own root for validation and handoff. The
source installer only discovers immediate children of the top-level source
root, so nested generated sub-skills are not install candidates. Never copy
sibling sub-skills into the eight source skill directories.

### Codex metadata appears in a generated reference

Remove the UI/export file contents from the generated source record. The
operating contract needs the source `SKILL.md` behavior and frontmatter, not
`agents/openai.yaml` display names, prompts, or export fields. It is acceptable
to state that such files are packaging metadata and must stay out of the graph.

## Paper and conference routes

### Network is unavailable or a public endpoint times out

Do not retry indefinitely, download a dataset, or fabricate papers. Report the
route and endpoint as unavailable. The observed arXiv helper times out after
20 seconds; Semantic Scholar search after 15 seconds; paper-detail fetch after
20 seconds. A safe check mocks these requests or exercises empty-input/error
handling only.

### A user asks for an API key for arXiv or Semantic Scholar

The observed public flows send a user-agent and no service API key. Do not
invent a credential requirement. Distinguish public literature access from the
LLM provider: the latter may still need an API key, compatible endpoint, or
logged-in CLI subscription. Never print or persist secrets in a report.

### Conference results do not honor the venue

The high-level route accepts `--venue`, but the inspected low-level paper
search tool exposes query/limit/year and no venue field. Include the venue in
the search query as appropriate and verify returned metadata before labeling a
paper as a venue match. If exact venue filtering is required, hand off to the
core integration/API owner rather than claiming it is enforced.

## Report and Obsidian routes

### “Progress export disabled”

This is the expected result when `obsidian.enabled` is false or missing. Ask
whether to enable it. Do not write local fallback notes while disabled.

### The destination is wrong

Re-read the intended project config and confirm `vault_path`,
`project_subdir`, and the local workspace. A non-empty vault path selects
`Dashboard.md` plus Markdown daily notes in the vault; an empty one selects
`Dashboard.txt` plus `.txt` daily notes under project-local progress tracking.
Do not silently switch routes because a vault is unavailable.

### Dashboard was replaced or daily note duplicated

Dashboard refresh is overwrite-style. Daily entries append, and a full manual
refresh appends a manual daily entry. Use `--dashboard-only` when no daily
append is wanted, and preserve/inspect the destination before rerunning.

## Explicit boundary

Nothing in this troubleshooting guide authorizes import into live managed
skills. Resolve collisions and route decisions first; installation or import
is a separate, approval-gated action.
